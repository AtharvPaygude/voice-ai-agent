"""
WebSocket endpoint for real-time voice streaming in Aura AI.
Features:
- Instant deterministic agent-first greeting
- Real-time sentence-level streaming for ultra-low latency (<1.5s first audio)
- Concurrent sentence synthesis (TTS pipeline)
- True tool call buffering and loop
- Real barge-in task cancellation
- Multilingual caller language detection (from user speech, not agent output)
- Escalation state machine and healthcare safety triage
"""
import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.llm_client import llm_client, build_system_prompt
from app.core.languages import detect_multilingual_language
from app.core.speaking_styles import get_greeting, get_style_prosody, SPEAKING_STYLES
from app.core.sentence_chunker import chunk_into_sentences, sanitize_spoken_text
from app.core.stt import transcribe_audio_bytes
from app.core.tts import synthesize_speech
from app.api.routes.knowledge import get_relevant_knowledge_context
from app.api.routes.tools import execute_tool, ToolCallRequest
from app.db.database import AsyncSessionLocal
from app.db.models import BusinessProfile, Call, Customer, Message, Escalation, gen_id
from app.core.escalation_report import record_issue, create_escalation

router = APIRouter()
logger = logging.getLogger(__name__)

# Active call tracking
_call_start_times: Dict[str, datetime] = {}
languages_seen: Dict[str, list] = {}
call_business_profiles: Dict[str, str] = {}
call_speaking_styles: Dict[str, str] = {}
call_caller_emails: Dict[str, str] = {}
audio_buffers: Dict[str, bytearray] = {}
active_tasks: Dict[str, asyncio.Task] = {}
call_failure_counts: Dict[str, int] = {}           # voice STT empty / tool failure counts
call_escalation_states: Dict[str, str] = {}        # normal | clarifying | offering_options | awaiting_choice
call_turn_counts: Dict[str, int] = {}              # number of completed turns per call (post-greeting)
call_consecutive_low_conf: Dict[str, int] = {}     # consecutive low-confidence voice turns
call_consecutive_tool_fail: Dict[str, int] = {}    # consecutive tool failure counts
call_anger_counts: Dict[str, int] = {}             # anger / frustration signal counts
debug_traces: Dict[str, List[dict]] = {}           # turn-by-turn per-call debug trace

HEALTHCARE_EMERGENCY_TERMS = [
    "chest pain", "can't breathe", "cannot breathe", "bleeding", "unconscious",
    "stroke", "suicid", "seene mein dard", "chhati dukhne", "saans nahi",
    "heart attack", "raktstrav", "behosh"
]

HEALTHCARE_ADVICE_TERMS = [
    "which tablet", "what medicine", "prescribe", "dosage", "painkiller",
    "treatment for", "dawaii", "kaunsi dawa", "aushadh"
]

# Anger / frustration signal phrases
_ANGER_PHRASES = [
    "this is ridiculous", "you're useless", "you are useless", "i'm frustrated",
    "i am frustrated", "this doesn't work", "this is stupid", "stop it",
    "you don't understand", "you do not understand", "unbelievable", "pathetic",
    "i give up", "worst service", "terrible", "this sucks", "pareshaan", "bakwaas",
]

# Emergency keywords (covered by HEALTHCARE_EMERGENCY_TERMS but adding generic ones)
_EMERGENCY_PHRASES = [
    "emergency", "urgent help", "call police", "call ambulance", "fire",
] + HEALTHCARE_EMERGENCY_TERMS

# Human-request phrases
_HUMAN_REQUEST_PHRASES = [
    "insaan se baat", "manager la bolwa", "speak to a person", "human agent",
    "talk to human", "real person", "connect me to", "transfer me", "manager",
    "operator",
]

VOICE_CONF_THRESHOLD = 0.35       # below this = low confidence for voice
LOW_CONF_ESCALATE_COUNT = 2       # consecutive low-conf turns before escalating
ANGER_ESCALATE_COUNT = 2          # anger signals before escalating
TOOL_FAIL_ESCALATE_COUNT = 2      # consecutive tool failures before escalating
GRACE_TURNS = 2                   # first N turns after greeting: no escalation


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, call_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[call_id] = websocket

    def disconnect(self, call_id: str):
        self.active_connections.pop(call_id, None)

    async def send_json(self, call_id: str, data: dict):
        ws = self.active_connections.get(call_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                pass

    async def send_bytes(self, call_id: str, data: bytes):
        ws = self.active_connections.get(call_id)
        if ws:
            try:
                await ws.send_bytes(data)
            except Exception:
                pass


manager = ConnectionManager()


def _classify_healthcare(text: str) -> Optional[str]:
    lowered = text.lower()
    if any(term in lowered for term in HEALTHCARE_EMERGENCY_TERMS):
        return "emergency"
    if any(term in lowered for term in HEALTHCARE_ADVICE_TERMS):
        return "medical_advice"
    return None


_classify_healthcare_request = _classify_healthcare


def _format_phone_for_speech(phone: str) -> str:
    """Format phone numbers for clear TTS pronunciation."""
    if not phone:
        return ""
    digit_words = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '+': 'plus '
    }
    parts = []
    for char in phone:
        if char in digit_words:
            parts.append(digit_words[char])
        elif char in [' ', '-', '(', ')']:
            parts.append(', ')
    res = " ".join(parts).replace(" , ", ", ")
    return re.sub(r'\s+', ' ', res).strip()


async def _deliver_escalation_turn(
    call_id: str,
    reason: str,
    language: str,
    send_audio: bool,
    prosody: dict,
    priority: str = "high",
) -> None:
    caller_email = call_caller_emails.get(call_id, "")
    esc = await create_escalation(
        call_id=call_id,
        reason=reason,
        priority=priority,
        requested_action="call" if reason in ["human_requested", "medical_emergency"] else "email",
        caller_email=caller_email,
    )
    ref = esc.id if esc else f"ESC-{int(time.time()) % 10000:04d}"
    phone_spoken = _format_phone_for_speech(settings.SUPPORT_PHONE)
    hours = settings.SUPPORT_HOURS

    email_note = f" I've also sent the report to {caller_email} so you can verify what happened." if caller_email else ""
    spoken_text = (
        f"I've logged issue report {ref} for our team. If you'd like to talk to someone right now, "
        f"please call our support team at {phone_spoken}, available {hours}.{email_note} "
        f"Is there anything else I can help you with?"
    )

    await manager.send_json(call_id, {
        "type": "escalation_alert",
        "escalation_id": esc.id if esc else ref,
        "ref": ref,
        "reason": reason,
        "status": "new",
        "support_phone": settings.SUPPORT_PHONE,
    })

    await _deliver_simple_response(call_id, spoken_text, language, send_audio, prosody)


async def get_customer_context(customer_id: Optional[str], db: AsyncSession) -> str:
    if not customer_id:
        return ""
    res = await db.execute(
        select(Call).where(Call.customer_id == customer_id, Call.summary != "")
        .order_by(Call.started_at.desc()).limit(2)
    )
    past = res.scalars().all()
    summaries = [f"- {c.summary.strip()}" for c in past if c.summary and c.summary.strip()]
    if not summaries:
        return ""
    return "Recent past customer interactions:\n" + "\n".join(summaries)


async def _resolve_or_create_customer(phone: str, name: str, business_id: Optional[str], db: AsyncSession, email: str = "") -> Customer:
    cleaned_phone = phone.strip() or f"caller-{int(time.time())}"
    res = await db.execute(select(Customer).where(Customer.phone == cleaned_phone))
    cust = res.scalars().first()
    if not cust:
        cust = Customer(
            id=gen_id("cust"),
            phone=cleaned_phone,
            name=name if name and name != "Unknown caller" else "Unknown caller",
            email=email.strip(),
            business_profile_id=business_id,
        )
        db.add(cust)
        await db.commit()
        await db.refresh(cust)
    else:
        changed = False
        if name and name != "Unknown caller" and cust.name == "Unknown caller":
            cust.name = name
            changed = True
        if email and email.strip() and not cust.email:
            cust.email = email.strip()
            changed = True
        if changed:
            await db.commit()
    return cust


async def _save_call_start(call_id: str, caller_phone: str, customer_id: Optional[str], business_id: Optional[str], style: str) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.get(Call, call_id)
        if existing:
            existing.caller_id = caller_phone
            existing.customer_id = customer_id
            existing.business_profile_id = business_id
            existing.speaking_style = style
            await db.commit()
            return
        db.add(Call(
            id=call_id,
            caller_id=caller_phone,
            customer_id=customer_id,
            business_profile_id=business_id,
            speaking_style=style,
            status="active",
        ))
        await db.commit()


async def _save_message(call_id: str, speaker: str, text: str, language: str, confidence: float) -> None:
    async with AsyncSessionLocal() as db:
        db.add(Message(
            call_id=call_id,
            speaker=speaker,
            text=text,
            detected_language=language,
            confidence=confidence,
        ))
        await db.commit()


async def _save_call_end(
    call_id: str, languages_used: list, intent: str, sentiment: str, lead_score: int, summary: str,
    latency_stats: dict
) -> None:
    async with AsyncSessionLocal() as db:
        call = await db.get(Call, call_id)
        if not call:
            return
        start = _call_start_times.pop(call_id, call.started_at)
        call.duration = max(0, int((datetime.utcnow() - start).total_seconds()))
        call.status = "completed"
        call.ended_at = datetime.utcnow()
        call.languages_used = languages_used
        call.intent = intent
        call.sentiment = sentiment
        call.lead_score = lead_score
        call.summary = summary
        call.latency_first_token_ms = latency_stats.get("first_token")
        call.latency_first_audio_ms = latency_stats.get("first_audio")
        call.latency_stt_ms = latency_stats.get("stt")
        call.latency_total_ms = latency_stats.get("total")
        await db.commit()


async def _process_user_turn(
    call_id: str,
    user_text: str,
    language: str,
    stt_confidence: float,
    send_audio: bool,
    stt_latency_ms: int = 0,
) -> None:
    """Core sentence-streaming conversational turn."""
    turn_start_time = time.time()
    languages_seen.setdefault(call_id, []).append(language)
    style = call_speaking_styles.get(call_id, "friendly")
    prosody = get_style_prosody(style)

    try:
        # 1. Echo user transcript to client
        await manager.send_json(call_id, {
            "type": "transcript",
            "text": user_text,
            "language": language,
            "confidence": stt_confidence,
            "speaker": "user",
        })
        await _save_message(call_id, "user", user_text, language, stt_confidence)

        # 2. Healthcare safety triage
        business_id = call_business_profiles.get(call_id)

        async with AsyncSessionLocal() as db:
            biz = await db.get(BusinessProfile, business_id) if business_id else None
            if biz and biz.policies and biz.policies.get("healthcare_safety"):
                triage = _classify_healthcare(user_text)
                if triage == "emergency":
                    resp = (
                        "This sounds like an emergency. Please call 112 immediately. "
                        "I am also connecting you to our on-call clinic staff right now."
                    )
                    await _deliver_emergency_turn(call_id, resp, language, send_audio, prosody, db, biz)
                    return
                elif triage == "medical_advice":
                    resp = (
                        "I cannot provide medical advice, diagnosis, or prescription dosages. "
                        "I can book an appointment with our doctor or connect you with clinic staff."
                    )
                    await _deliver_simple_response(call_id, resp, language, send_audio, prosody)
                    return

        # 3. Check for caller escalation requests / frustration
        lowered_input = user_text.lower()
        if any(p in lowered_input for p in _ANGER_PHRASES):
            record_issue(call_id, "anger", user_text)
            call_anger_counts[call_id] = call_anger_counts.get(call_id, 0) + 1
            if call_turn_counts.get(call_id, 0) >= GRACE_TURNS and call_anger_counts[call_id] >= ANGER_ESCALATE_COUNT:
                await _deliver_escalation_turn(call_id, "customer_frustration", language, send_audio, prosody, priority="high")
                return

        if any(p in lowered_input for p in _HUMAN_REQUEST_PHRASES):
            record_issue(call_id, "human_requested", user_text)
            await _deliver_escalation_turn(call_id, "human_requested", language, send_audio, prosody, priority="high")
            return

        # 4. State -> thinking
        await manager.send_json(call_id, {"type": "state_change", "state": "thinking"})

        # 5. Retrieve dynamic knowledge context
        kb_context = ""
        async with AsyncSessionLocal() as db:
            kb_context = await get_relevant_knowledge_context(user_text, business_id, db)

        # 6. Stream tokens and chunk into spoken sentences
        token_stream = llm_client.stream_response(call_id, user_text)
        sentence_stream = chunk_into_sentences(token_stream)

        first_token_time: Optional[float] = None
        first_audio_time: Optional[float] = None
        full_agent_reply = ""
        sentence_idx = 0

        await manager.send_json(call_id, {"type": "state_change", "state": "speaking"})

        async for spoken_sentence, tool_json in sentence_stream:
            # Tool call detected
            if tool_json:
                try:
                    tool_data = json.loads(tool_json)
                    tool_name = tool_data.get("tool")
                    tool_params = tool_data.get("parameters", {})
                    if business_id:
                        tool_params.setdefault("business_id", business_id)

                    await manager.send_json(call_id, {"type": "state_change", "state": "tool_action"})
                    tool_resp = await execute_tool(ToolCallRequest(tool=tool_name, parameters=tool_params, call_id=call_id))

                    await manager.send_json(call_id, {
                        "type": "tool_call",
                        "tool": tool_name,
                        "status": tool_resp.status,
                        "result": tool_resp.result,
                        "message": tool_resp.message,
                    })

                    if tool_resp.status == "error":
                        record_issue(call_id, "tool_failure", f"{tool_name}: {tool_resp.message}")
                        call_consecutive_tool_fail[call_id] = call_consecutive_tool_fail.get(call_id, 0) + 1
                        if call_consecutive_tool_fail[call_id] >= TOOL_FAIL_ESCALATE_COUNT:
                            await _deliver_escalation_turn(call_id, "consecutive_tool_failures", language, send_audio, prosody, priority="high")
                            return
                    else:
                        call_consecutive_tool_fail[call_id] = 0
                        if tool_name == "transfer_to_human":
                            await _deliver_escalation_turn(call_id, "transferred_by_agent", language, send_audio, prosody, priority="high")
                            return

                    # If the tool generated spoken message, stream it
                    if tool_resp.message:
                        spoken_sentence = tool_resp.message
                except Exception as e:
                    logger.error(f"Streaming tool execution error: {e}")
                    record_issue(call_id, "tool_failure", str(e))

            if spoken_sentence:
                # Final safety: strip any tool-call syntax that leaked through
                spoken_sentence = sanitize_spoken_text(spoken_sentence)
                if not spoken_sentence or len(spoken_sentence.split()) < 2:
                    continue

                if first_token_time is None:
                    first_token_time = time.time()
                    first_token_ms = int((first_token_time - turn_start_time) * 1000)
                    logger.info(f"[AUDIO PIPELINE] First LLM token in {first_token_ms}ms for call {call_id}")
                    await manager.send_json(call_id, {
                        "type": "latency_metrics",
                        "first_token_ms": first_token_ms,
                        "stt_ms": stt_latency_ms,
                    })

                full_agent_reply += " " + spoken_sentence
                detected_agent_lang = detect_multilingual_language(spoken_sentence, language)

                # Send sentence transcript to client
                await manager.send_json(call_id, {
                    "type": "response_sentence",
                    "index": sentence_idx,
                    "text": spoken_sentence,
                    "language": detected_agent_lang,
                    "has_audio": send_audio,
                })

                # Synthesize sentence audio immediately
                if send_audio:
                    audio_bytes = await synthesize_speech(
                        spoken_sentence,
                        language=detected_agent_lang,
                        rate=prosody.get("rate", "+0%"),
                        pitch=prosody.get("pitch", "+0Hz"),
                        volume=prosody.get("volume", "+0%"),
                    )
                    if audio_bytes:
                        if first_audio_time is None:
                            first_audio_time = time.time()
                            first_audio_ms = int((first_audio_time - turn_start_time) * 1000)
                            logger.info(f"[AUDIO PIPELINE] First TTS audio in {first_audio_ms}ms for call {call_id} ({len(audio_bytes)} bytes)")
                            await manager.send_json(call_id, {
                                "type": "latency_metrics",
                                "first_audio_ms": first_audio_ms,
                            })

                        await manager.send_json(call_id, {
                            "type": "audio_start",
                            "index": sentence_idx,
                            "format": "mp3",
                        })
                        # Send full sentence audio bytes in a single binary frame
                        await manager.send_bytes(call_id, audio_bytes)
                        await manager.send_json(call_id, {"type": "audio_end", "index": sentence_idx})

                sentence_idx += 1

        total_turn_ms = int((time.time() - turn_start_time) * 1000)
        logger.info(f"[AUDIO PIPELINE] Turn complete for call {call_id} in {total_turn_ms}ms")
        await manager.send_json(call_id, {
            "type": "turn_complete",
            "total_turn_ms": total_turn_ms,
        })

        full_text_clean = full_agent_reply.strip()
        if full_text_clean:
            await _save_message(call_id, "agent", full_text_clean, language, 0.98)

        # Reset failure counts and return escalation state to normal on successful turn
        call_failure_counts[call_id] = 0
        call_escalation_states[call_id] = "normal"
        call_turn_counts[call_id] = call_turn_counts.get(call_id, 0) + 1

        # Record debug trace
        debug_traces.setdefault(call_id, []).append({
            "turn": call_turn_counts[call_id],
            "input_source": "voice" if stt_latency_ms > 0 else "text",
            "user_text": user_text,
            "transcript_confidence": stt_confidence,
            "detected_language": language,
            "agent_reply": full_text_clean,
            "total_ms": total_turn_ms,
            "escalation_state": "normal",
        })

        logger.debug(f"[TURN TRACE] call={call_id} turn={call_turn_counts[call_id]} reply='{full_text_clean[:60]}...' ms={total_turn_ms}")

    except asyncio.CancelledError:
        logger.info(f"Turn cancelled by client/barge-in: call_id={call_id}")
        raise
    except Exception as e:
        logger.error(f"Error in _process_user_turn for call {call_id}: {e}", exc_info=True)
        record_issue(call_id, "turn_error", str(e))
        await manager.send_json(call_id, {"type": "turn_error", "message": "An error occurred during turn processing."})
        await _deliver_simple_response(
            call_id,
            "I'm sorry, I encountered a brief technical issue. Could you please repeat that?",
            language,
            send_audio,
            prosody,
        )
        total_turn_ms = int((time.time() - turn_start_time) * 1000)
        await manager.send_json(call_id, {
            "type": "turn_complete",
            "total_turn_ms": total_turn_ms,
        })


async def _deliver_simple_response(call_id: str, text: str, language: str, send_audio: bool, prosody: dict):
    await manager.send_json(call_id, {"type": "state_change", "state": "speaking"})
    await manager.send_json(call_id, {
        "type": "response",
        "text": text,
        "language": language,
        "has_audio": send_audio,
    })
    await _save_message(call_id, "agent", text, language, 0.99)
    if send_audio:
        audio = await synthesize_speech(text, language=language, rate=prosody.get("rate", "+0%"))
        if audio:
            await manager.send_json(call_id, {"type": "audio_start", "format": "mp3"})
            await manager.send_bytes(call_id, audio)
            await manager.send_json(call_id, {"type": "audio_end"})
    await manager.send_json(call_id, {"type": "turn_complete", "total_turn_ms": 0})


async def _deliver_emergency_turn(call_id: str, text: str, language: str, send_audio: bool, prosody: dict, db: AsyncSession, biz: Optional[BusinessProfile]):
    caller_email = call_caller_emails.get(call_id, "")
    esc = await create_escalation(
        call_id=call_id,
        reason="medical_emergency",
        priority="urgent",
        requested_action="call",
        caller_email=caller_email,
    )
    await manager.send_json(call_id, {
        "type": "escalation_alert",
        "reason": "medical_emergency",
        "escalation_id": esc.id if esc else None,
        "ref": esc.id if esc else "EMERGENCY",
        "support_phone": settings.SUPPORT_PHONE,
    })
    await _deliver_simple_response(call_id, text, language, send_audio, prosody)


@router.get("/debug/calls/{call_id}/trace")
async def get_call_trace(call_id: str):
    """Retrieve turn-by-turn debug trace for a call."""
    return debug_traces.get(call_id, [])


@router.websocket("/voice/{call_id}")
async def voice_websocket(websocket: WebSocket, call_id: str):
    """Real-time voice streaming WebSocket endpoint."""
    await manager.connect(call_id, websocket)

    try:
        await manager.send_json(call_id, {
            "type": "state_change",
            "state": "idle",
            "message": "Aura AI Connected",
        })

        while True:
            data = await websocket.receive()

            if "bytes" in data and data["bytes"]:
                # Audio frame buffer for server voice pipeline
                audio_buffers.setdefault(call_id, bytearray()).extend(data["bytes"])

            elif "text" in data and data["text"]:
                try:
                    msg = json.loads(data["text"])
                    msg_type = msg.get("type")

                    # 1. START CALL — Instant Agent-First Greeting
                    if msg_type == "start_call":
                        llm_client.clear_history(call_id)
                        _call_start_times[call_id] = datetime.utcnow()
                        audio_buffers[call_id] = bytearray()
                        call_failure_counts[call_id] = 0

                        caller_phone = str(msg.get("phone") or msg.get("caller_phone") or "Unknown").strip()
                        caller_name = str(msg.get("name") or msg.get("caller_name") or "Unknown caller").strip()
                        caller_email = str(msg.get("email") or msg.get("caller_email") or "").strip()
                        call_caller_emails[call_id] = caller_email
                        business_id = msg.get("business_id") or msg.get("business_profile_id")
                        style = str(msg.get("speaking_style") or settings.DEFAULT_SPEAKING_STYLE).lower()
                        send_audio = bool(msg.get("send_audio", True))
                        initial_lang = str(msg.get("language") or "en")

                        customer = None
                        business = None
                        customer_ctx = ""
                        async with AsyncSessionLocal() as db:
                            customer = await _resolve_or_create_customer(caller_phone, caller_name, business_id, db, email=caller_email)
                            customer_ctx = await get_customer_context(customer.id, db)
                            if business_id:
                                business = await db.get(BusinessProfile, business_id)
                            if not business:
                                res = await db.execute(select(BusinessProfile).limit(1))
                                business = res.scalars().first()

                        biz_id = business.id if business else business_id
                        call_business_profiles[call_id] = biz_id
                        call_speaking_styles[call_id] = style

                        await _save_call_start(call_id, caller_phone, customer.id if customer else None, biz_id, style)

                        # Set system prompt
                        sys_prompt = build_system_prompt(
                            business=business,
                            customer_context=customer_ctx,
                            speaking_style=style,
                        )
                        llm_client.get_history(call_id, system_prompt=sys_prompt)

                        business_name = business.name if business else "Aura AI"
                        agent_name = settings.AGENT_NAME

                        # DETERMINISTIC INSTANT GREETING (Section 2D)
                        greeting_text = get_greeting(
                            style=style,
                            language=initial_lang,
                            business_name=business_name,
                            agent_name=agent_name,
                        )

                        await manager.send_json(call_id, {
                            "type": "call_started",
                            "call_id": call_id,
                            "agent_name": agent_name,
                            "business_name": business_name,
                            "speaking_style": style,
                        })

                        # Stream the greeting instantly
                        prosody = get_style_prosody(style)
                        await _deliver_simple_response(call_id, greeting_text, initial_lang, send_audio, prosody)

                    # 2. SET SPEAKING STYLE (Section 2A)
                    elif msg_type == "set_style":
                        new_style = str(msg.get("style", "friendly")).lower()
                        if new_style in SPEAKING_STYLES:
                            call_speaking_styles[call_id] = new_style
                            async with AsyncSessionLocal() as db:
                                biz_id = call_business_profiles.get(call_id)
                                biz = await db.get(BusinessProfile, biz_id) if biz_id else None
                                updated_prompt = build_system_prompt(business=biz, speaking_style=new_style)
                                llm_client.set_system_prompt(call_id, updated_prompt)
                            await manager.send_json(call_id, {"type": "style_updated", "style": new_style})

                    # 3. TEXT INPUT
                    elif msg_type == "text_input":
                        user_text = str(msg.get("text", "")).strip()
                        if not user_text:
                            continue

                        # Cancel any running in-flight response task on barge-in
                        task = active_tasks.get(call_id)
                        if task and not task.done():
                            task.cancel()

                        lang = msg.get("language") or detect_multilingual_language(user_text, "en")
                        active_tasks[call_id] = asyncio.create_task(
                            _process_user_turn(call_id, user_text, lang, stt_confidence=0.98, send_audio=True)
                        )

                    # 4. VOICE INPUT (Server Voice Pipeline)
                    elif msg_type == "voice_input":
                        hint_lang = msg.get("language")
                        buffered = bytes(audio_buffers.pop(call_id, bytearray()))
                        audio_buffers[call_id] = bytearray()
                        buf_len = len(buffered)

                        logger.info(f"[AUDIO PIPELINE] voice_input received for call {call_id}: {buf_len} bytes, hint='{hint_lang}'")

                        if buf_len < 400:
                            logger.info(f"[AUDIO PIPELINE] Audio buffer ({buf_len} bytes) too small for utterance; resuming listening.")
                            await manager.send_json(call_id, {"type": "turn_complete", "total_turn_ms": 0})
                            continue

                        await manager.send_json(call_id, {"type": "state_change", "state": "thinking"})
                        stt_start = time.time()
                        transcribed_text, detected_lang, confidence = await asyncio.to_thread(
                            transcribe_audio_bytes, buffered, hint_lang
                        )
                        stt_ms = int((time.time() - stt_start) * 1000)
                        logger.info(
                            f"[AUDIO PIPELINE] STT complete for call {call_id} in {stt_ms}ms: "
                            f"text='{transcribed_text}' lang='{detected_lang}' conf={confidence:.2f}"
                        )

                        if not transcribed_text:
                            # Silence or inaudible utterance
                            logger.warning(f"[AUDIO PIPELINE] Inaudible utterance for call {call_id}")
                            record_issue(call_id, "inaudible_speech")
                            call_failure_counts[call_id] = call_failure_counts.get(call_id, 0) + 1
                            fc = call_failure_counts[call_id]
                            style = call_speaking_styles.get(call_id, "friendly")
                            prosody = get_style_prosody(style)

                            if fc == 1:
                                retry_line = "Sorry, I didn't quite catch that. Could you say it once more?"
                                await _deliver_simple_response(call_id, retry_line, hint_lang or "en", True, prosody)
                            elif fc == 2:
                                retry_line = "I may be missing something. Could you tell me in a few words what you need, for example booking or pricing?"
                                await _deliver_simple_response(call_id, retry_line, hint_lang or "en", True, prosody)
                            else:
                                await _deliver_escalation_turn(call_id, "inaudible_speech", hint_lang or "en", True, prosody, priority="medium")
                            continue

                        words = transcribed_text.strip().split()
                        if confidence < VOICE_CONF_THRESHOLD and len(words) < 2:
                            # Low-confidence noise: ignore and do not interrupt
                            logger.info(f"[AUDIO PIPELINE] Low confidence noise ignored: '{transcribed_text}' (conf={confidence:.2f})")
                            await manager.send_json(call_id, {"type": "turn_complete", "total_turn_ms": 0})
                            continue

                        if confidence < VOICE_CONF_THRESHOLD:
                            record_issue(call_id, "low_confidence", f"conf={confidence:.2f}")

                        call_failure_counts[call_id] = 0
                        # Cancel in-flight task on barge-in
                        task = active_tasks.get(call_id)
                        if task and not task.done():
                            task.cancel()

                        active_tasks[call_id] = asyncio.create_task(
                            _process_user_turn(call_id, transcribed_text, detected_lang, confidence, send_audio=True, stt_latency_ms=stt_ms)
                        )

                    # 5. BARGE-IN INTERRUPT
                    elif msg_type == "interrupt":
                        audio_buffers[call_id] = bytearray()
                        task = active_tasks.get(call_id)
                        if task and not task.done():
                            task.cancel()
                        await manager.send_json(call_id, {"type": "audio_interrupted", "call_id": call_id})
                        await manager.send_json(call_id, {"type": "state_change", "state": "listening"})

                    # 6. END CALL
                    elif msg_type == "end_call":
                        task = active_tasks.get(call_id)
                        if task and not task.done():
                            task.cancel()

                        llm_client.clear_history(call_id)
                        languages_used = list(dict.fromkeys(languages_seen.get(call_id, ["en"])))
                        duration = max(0, int((datetime.utcnow() - _call_start_times.get(call_id, datetime.utcnow())).total_seconds()))
                        summary = f"Call completed successfully ({duration}s). Languages: {', '.join(languages_used)}."

                        await _save_call_end(
                            call_id,
                            languages_used=languages_used,
                            intent="general_inquiry",
                            sentiment="neutral",
                            lead_score=75,
                            summary=summary,
                            latency_stats={},
                        )
                        await manager.send_json(call_id, {
                            "type": "call_summary",
                            "call_id": call_id,
                            "summary": summary,
                            "duration": duration,
                            "languages_used": languages_used,
                        })
                        languages_seen.pop(call_id, None)
                        audio_buffers.pop(call_id, None)
                        call_business_profiles.pop(call_id, None)
                        call_speaking_styles.pop(call_id, None)
                        call_caller_emails.pop(call_id, None)
                        break

                except Exception as err:
                    logger.error(f"WebSocket parse error: {err}")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: call_id={call_id}")
    finally:
        manager.disconnect(call_id)
        audio_buffers.pop(call_id, None)
        active_tasks.pop(call_id, None)
        call_caller_emails.pop(call_id, None)
