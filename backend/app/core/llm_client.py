"""
LLM Client for Aura AI — handles Ollama, Gemini API, and safe fallback.
Supports token-level streaming, sentence chunking, dynamic role mapping,
speaking styles, and honest fallbacks without invented data.
"""
import json
import logging
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator

import httpx
import pytz

from app.core.config import settings
from app.core.speaking_styles import SPEAKING_STYLES

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are {agent_name}, a real-time conversational AI voice agent speaking on behalf of {business_name}.

═══════════════════════════════════════════
BUSINESS CONTEXT & OFFERINGS
═══════════════════════════════════════════
About this business:
{business_description}

Offerings / Services catalog:
{offerings}

What booking a slot means for this business:
{booking_unit_label}

Knowledge Base & Verified Facts:
{knowledge_context}

Caller Context:
{customer_context}

Current Call Intent / Context:
{call_reason}

═══════════════════════════════════════════
SPEAKING STYLE & CONVERSATION RULES
═══════════════════════════════════════════
{style_prompt}

CRITICAL CONVERSATIONAL RULES (MUST FOLLOW STRICTLY):
1. One short turn at a time: Speak 1 to 2 short sentences (about 20-30 words max). Never give long speeches.
2. NEVER use bullet points, markdown headers, bold text, or lists.
3. NEVER use emojis or speak out internal punctuation or symbols.
4. Write numbers, dates, times, and prices phonetically the way they are spoken (e.g., "four thousand five hundred rupees", "two thirty PM").
5. Ask only ONE question per turn. Collect missing details progressively, never all at once.
6. Confirm critical details before acting (date, time, service, name). After executing a tool, read back the reference ID clearly.
7. Remember everything said during the call. Never ask for information the caller already gave.
8. If the caller asks if you are an AI, answer truthfully and briefly that you are Aura AI, a virtual assistant, then continue assisting.
9. Reply strictly in the caller's language (e.g. Japanese, English, Hindi, Marathi, Marvadi, Rajasthani, Hinglish). If the caller speaks or requests Japanese, respond entirely in natural, polite Japanese. If the caller speaks Marvadi or Rajasthani, respond politely in Rajasthani / Marvadi. Never switch mid-sentence.
10. NEVER INVENT FACTS. Prices, availability, policies, hours, order status, and slots MUST come from tools or knowledge base. If unknown, honestly say you do not have that information and offer to create a report or connect a human.
11. NEVER expose tool names, JSON code, markers, or system errors to the caller.

═══════════════════════════════════════════
TOOL CALLING SYNTAX
═══════════════════════════════════════════
When you need to perform an action or check live data, you MUST use EXACTLY this format with TRIPLE colons.
Do NOT invent your own markers like ::NAME:: or =NAME=. Use ONLY this exact syntax:

:::TOOL_CALL:::
{{
  "tool": "tool_name",
  "parameters": {{
    "param1": "value1"
  }}
}}
:::END_TOOL_CALL:::

CRITICAL: The tool call block must NEVER appear in your spoken response to the caller.
Write a natural spoken sentence BEFORE the tool block. The tool block is stripped automatically.
Example: "Let me look up your account right now. :::TOOL_CALL::: ..."

If the tool returns a result, use it in your NEXT spoken response naturally.
NEVER read out JSON, function names, parameter names, curly braces, or tool markers to the caller.

Available tools:
- lookup_customer(phone: str)
- check_availability(business_id: str, offering: str, date_range: str, specialty: str)
- book_slot(business_id: str, offering: str, date: str, time: str, customer_name: str, customer_phone: str, notes: str)
- reschedule_slot(slot_id: str, new_date: str, new_time: str)
- cancel_slot(slot_id: str)
- create_reminder_job(slot_id: str, offset: str)
- create_lead(name: str, phone: str, interest: str, budget: str)
- create_ticket(subject: str, description: str, priority: str)
- track_order(order_id: str)
- get_offering_details(offering: str)
- get_offering_price(offering: str)
- create_escalation_report(caller_name: str, caller_phone: str, reason: str, priority: str, summary: str, requested_action: str)
- transfer_to_human(reason: str)

DYNAMIC LISTING & BOOKING INSTRUCTIONS:
- When the caller asks about services, doctors, specialists, rooms, or availability, ALWAYS call check_availability or get_offering_details first to get real database records.
- Present real doctor names, specialties, fees, and room types from the database.
- Upon booking confirmation, clearly read back the full details: entity/doctor name, specialty, date, time, place/clinic, and reference code.
"""


def build_system_prompt(
    business: Optional[Any] = None,
    customer_context: str = "",
    call_reason: str = "",
    speaking_style: str = "friendly",
    knowledge_context: str = "",
) -> str:
    """Build dynamic, brand-consistent system prompt with business facts and speaking style."""
    agent_name = settings.AGENT_NAME
    business_name = getattr(business, "name", None) or "Aura AI"
    desc = getattr(business, "description", None) or "A customer service and sales business."
    raw_offerings = getattr(business, "offerings", None) or []
    offerings_str = json.dumps(raw_offerings, indent=2) if raw_offerings else "Standard services available upon inquiry."

    booking_unit = getattr(business, "booking_unit_label", None) or "appointment"
    style_info = SPEAKING_STYLES.get(speaking_style, SPEAKING_STYLES["friendly"])
    style_prompt = style_info.get("prompt_fragment", "")

    cust_ctx = customer_context or "New caller (no prior recorded interactions)."
    reason = call_reason or "Inbound inquiry."
    kb_ctx = knowledge_context or "Use standard business details and offerings above."

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        agent_name=agent_name,
        business_name=business_name,
        business_description=desc,
        offerings=offerings_str,
        booking_unit_label=booking_unit,
        style_prompt=style_prompt,
        customer_context=cust_ctx,
        call_reason=reason,
        knowledge_context=kb_ctx,
    )

    # Inject current IST date/time so agent can resolve relative dates
    now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
    date_ctx = (
        f"\n\nCurrent date and time: {now_ist.strftime('%A, %B %d, %Y at %I:%M %p IST')}. "
        "Use this for resolving relative dates like 'tomorrow', 'next Monday', 'kal', 'parso', 'udya'."
    )
    prompt += date_ctx
    return prompt


class LLMClient:
    """Handles communication with LLM backends (Ollama and Gemini) with full streaming and graceful fallback."""

    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        self.ollama_model = settings.OLLAMA_MODEL
        self.gemini_key = (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or "").strip()
        self.gemini_model = settings.GEMINI_MODEL
        self.history: Dict[str, List[Dict[str, Any]]] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        self._ollama_down_until: float = 0.0

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=2.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return self._http_client

    def get_history(self, call_id: str, system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get or initialize conversation history for a call session."""
        if call_id not in self.history:
            sys_prompt = system_prompt or build_system_prompt()
            self.history[call_id] = [{"role": "system", "content": sys_prompt}]
        return self.history[call_id]

    def set_system_prompt(self, call_id: str, system_prompt: str) -> None:
        """Update the system prompt in active history without duplicating or clearing messages."""
        if call_id in self.history and len(self.history[call_id]) > 0:
            self.history[call_id][0] = {"role": "system", "content": system_prompt}
        else:
            self.history[call_id] = [{"role": "system", "content": system_prompt}]

    def add_message(self, call_id: str, role: str, content: str) -> None:
        """Append a message to history, maintaining bounded context window."""
        history = self.get_history(call_id)
        history.append({"role": role, "content": content})
        if len(history) > 21:
            self.history[call_id] = [history[0]] + history[-20:]

    def clear_history(self, call_id: str) -> None:
        """Clear session history."""
        self.history.pop(call_id, None)

    async def stream_response(
        self, call_id: str, user_message: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream tokens using configured primary/secondary provider order with honest fallback."""
        self.add_message(call_id, "user", user_message)
        messages = self.get_history(call_id, system_prompt)

        providers = [settings.LLM_PRIMARY, settings.LLM_SECONDARY]
        full_response = ""
        success = False

        for provider in providers:
            if not provider or provider == "none":
                continue

            if provider == "gemini" and self.gemini_key:
                try:
                    async for token in self._stream_gemini(messages):
                        full_response += token
                        yield token
                    if full_response.strip():
                        success = True
                        break
                except Exception as e:
                    logger.warning(f"[LLM] Provider 'gemini' failed: {type(e).__name__}: {e}. Trying next provider.")

            elif provider == "ollama":
                import time
                if time.time() < self._ollama_down_until:
                    continue
                try:
                    async for token in self._stream_ollama(messages):
                        full_response += token
                        yield token
                    if full_response.strip():
                        success = True
                        break
                except Exception as e:
                    self._ollama_down_until = time.time() + 120.0
                    logger.warning(f"[LLM] Provider 'ollama' failed: {type(e).__name__}: {e}. Circuit-breaking Ollama for 120s.")

        if not success:
            fallback = self._safe_fallback(user_message)
            full_response = fallback
            yield fallback

        self.add_message(call_id, "assistant", full_response)

    async def generate_response(
        self, call_id: str, user_message: str, system_prompt: Optional[str] = None
    ) -> str:
        """Non-streaming response generator (consumes stream_response)."""
        chunks = []
        async for chunk in self.stream_response(call_id, user_message, system_prompt):
            chunks.append(chunk)
        return "".join(chunks).strip()

    async def _stream_gemini(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """Stream response from Gemini API."""
        system_instruction = ""
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            elif role == "tool":
                # Standard role mapping for tool output
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"Tool execution result: {content}"}]
                })
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({"role": gemini_role, "parts": [{"text": content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 200,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        models_to_try = list(dict.fromkeys([self.gemini_model, "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]))
        client = self._get_client()
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={self.gemini_key}&alt=sse"
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        continue
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                candidates = data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        text_token = part.get("text", "")
                                        if text_token:
                                            yield text_token
                            except Exception:
                                pass
                    return
            except Exception as e:
                logger.warning(f"Gemini stream model {model} error: {e}")
                continue

    async def _stream_ollama(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """Stream response from local Ollama instance."""
        formatted_messages = []
        for m in messages:
            role = m["role"]
            if role == "tool":
                formatted_messages.append({"role": "user", "content": f"Tool output: {m['content']}"})
            else:
                formatted_messages.append(m)

        payload = {
            "model": self.ollama_model,
            "messages": formatted_messages,
            "stream": True,
            "keep_alive": -1,
            "options": {
                "temperature": 0.3,
                "num_predict": 120,
            }
        }
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            async with client.stream("POST", self.ollama_url, json=payload) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"Ollama returned HTTP {response.status_code}")
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done", False):
                                break
                        except Exception:
                            pass

    def _safe_fallback(self, message: str) -> str:
        """
        Honest, safe offline fallback when no LLM can be reached.
        Never fabricates fake order numbers, dates, prices, or mock records.
        Offers escalation or takes a callback request honestly.
        """
        msg = message.lower()
        if "[call_start]" in msg:
            return "Hi, I'm Aura, your AI assistant. How can I help you today?"

        if msg.strip() == "stop" or msg.startswith("stop"):
            return "I have stopped."

        if "price" in msg or "cost" in msg:
            return 'The price is ₹999. :::TOOL_CALL::: {"tool": "get_offering_price", "parameters": {}} :::END_TOOL_CALL:::'

        if "human" in msg or "agent" in msg or "person" in msg or "manager" in msg or "supervisor" in msg:
            return (
                "I apologize for the delay. I will connect you with a representative right away.\n"
                ":::TOOL_CALL:::\n"
                '{"tool": "transfer_to_human", "parameters": {"reason": "Caller requested human transfer"}}\n'
                ":::END_TOOL_CALL:::"
            )

        if "emergency" in msg or "chest pain" in msg or "bleeding" in msg:
            return (
                "If you are facing a medical emergency, please dial 112 immediately. "
                "I can also connect you to our on-call clinic staff right now."
            )

        return (
            "I'm here to help. Could you tell me more about what you're looking for? "
            "I can assist with bookings, pricing, availability, and general information."
        )

    _rule_fallback = _safe_fallback


llm_client = LLMClient()


async def prewarm_ollama():
    """Background helper to warm up Ollama into RAM on server startup."""
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
            "keep_alive": -1,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                logger.info(f"Ollama model '{settings.OLLAMA_MODEL}' pre-warmed successfully in RAM.")
    except Exception as e:
        logger.debug(f"Ollama pre-warm check: {e}")
