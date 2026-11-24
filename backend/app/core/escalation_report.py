"""
Escalation Report Service for Aura AI.
Deterministic issue tracking, report generation, and confirmation emails without extra LLM calls.
"""
import asyncio
import logging
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from sqlalchemy import select
from app.core.config import settings
from app.core.integrations import send_smtp_email
from app.db.database import AsyncSessionLocal
from app.db.models import Call, Message, Customer, BusinessProfile, Escalation, gen_id

logger = logging.getLogger(__name__)

# In-memory tracking of issues during a call: {call_id: [{time, type, detail}]}
_call_issues: Dict[str, List[Dict[str, Any]]] = {}
_created_escalations: Dict[str, str] = {}  # (call_id, reason) -> escalation_id for deduplication


def record_issue(call_id: str, issue_type: str, detail: str = ""):
    """Record an operational issue that occurred during a call."""
    if not call_id:
        return
    now_str = datetime.now(timezone.utc).isoformat()
    _call_issues.setdefault(call_id, []).append({
        "time": now_str,
        "type": issue_type,
        "detail": detail,
    })


def get_call_issues(call_id: str) -> List[Dict[str, Any]]:
    return _call_issues.get(call_id, [])


async def create_escalation(
    call_id: str,
    reason: str = "general",
    priority: str = "medium",
    requested_action: str = "email",
    caller_email: Optional[str] = None,
) -> Optional[Escalation]:
    """Create and persist an escalation report, then queue emails."""
    dedupe_key = f"{call_id}:{reason}"
    if dedupe_key in _created_escalations:
        existing_id = _created_escalations[dedupe_key]
        async with AsyncSessionLocal() as db:
            return await db.get(Escalation, existing_id)

    async with AsyncSessionLocal() as db:
        call = await db.get(Call, call_id) if call_id else None
        biz_id = call.business_profile_id if call else None
        cust_id = call.customer_id if call else None

        biz = await db.get(BusinessProfile, biz_id) if biz_id else None
        if not biz:
            res = await db.execute(select(BusinessProfile).limit(1))
            biz = res.scalars().first()

        cust = await db.get(Customer, cust_id) if cust_id else None

        # Fetch last 8 messages
        msg_q = select(Message).where(Message.call_id == call_id).order_by(Message.timestamp.desc()).limit(8)
        msgs = list(reversed((await db.execute(msg_q)).scalars().all()))

        # Determine caller intent (last user message with >= 3 words)
        caller_intent = "General inquiry"
        for m in reversed(msgs):
            if m.speaker == "user" and len(m.text.strip().split()) >= 3:
                caller_intent = m.text.strip()
                break

        # Transcript snippet
        transcript_snippet = [
            {
                "speaker": m.speaker,
                "text": m.text,
                "time": m.timestamp.isoformat() if m.timestamp else "",
            }
            for m in msgs
        ]

        # Gather issues & tools used
        issues = list(_call_issues.get(call_id, []))
        tools_used = []
        agent_attempts_parts = []
        for iss in issues:
            itype = iss.get("type")
            idetail = iss.get("detail", "")
            if itype == "inaudible_speech":
                agent_attempts_parts.append("Asked caller to repeat due to inaudible speech")
            elif itype == "low_confidence":
                agent_attempts_parts.append(f"Low speech recognition confidence: {idetail}")
            elif itype == "tool_failure":
                agent_attempts_parts.append(f"Tool failure encountered: {idetail}")
            elif itype == "llm_error":
                agent_attempts_parts.append(f"AI response issue: {idetail}")
            elif itype == "anger":
                agent_attempts_parts.append(f"Caller expressed frustration: {idetail}")
            elif itype == "human_requested":
                agent_attempts_parts.append("Caller requested human representative")

        agent_attempts = "; ".join(agent_attempts_parts) if agent_attempts_parts else "Attempted automated conversation resolution"

        # Summary
        summary = (
            f"Caller contacted regarding '{caller_intent}'. "
            f"The interaction required escalation due to {reason.replace('_', ' ')}. "
            f"Current status: escalation logged for team follow-up."
        )

        final_caller_email = (caller_email or (cust.email if cust else "") or "").strip()
        caller_name = (cust.name if cust else None) or (call.caller_id if call else "Unknown caller")
        caller_phone = (cust.phone if cust else None) or (call.caller_id if call else "")
        token = secrets.token_urlsafe(16)

        esc = Escalation(
            id=gen_id("esc"),
            call_id=call_id,
            business_profile_id=biz.id if biz else None,
            caller_name=caller_name,
            caller_phone=caller_phone,
            caller_email=final_caller_email,
            confirm_token=token,
            user_confirmation="pending",
            user_note="",
            email_status="not_sent",
            language=call.current_language if call else "en",
            reason=reason,
            priority=priority,
            caller_intent=caller_intent,
            agent_attempts=agent_attempts,
            summary=summary,
            transcript_snippet=transcript_snippet,
            tools_used=tools_used,
            issues=issues,
            requested_action=requested_action,
            status="new",
        )
        db.add(esc)
        await db.commit()
        await db.refresh(esc)

        _created_escalations[dedupe_key] = esc.id

        # Fire and forget email notifications
        asyncio.create_task(send_escalation_emails(esc.id))
        return esc


async def send_escalation_emails(escalation_id: str):
    """Deliver confirmation email to caller and alert email to business team."""
    async with AsyncSessionLocal() as db:
        esc = await db.get(Escalation, escalation_id)
        if not esc:
            return

        biz = await db.get(BusinessProfile, esc.business_profile_id) if esc.business_profile_id else None
        support_phone = (biz.contact_phone if biz and biz.contact_phone else settings.SUPPORT_PHONE) or "our support line"
        support_hours = settings.SUPPORT_HOURS
        public_url = settings.PUBLIC_API_URL.rstrip("/")

        # 1. Email to caller (if email available)
        email_sent = False
        if esc.caller_email:
            confirm_yes_url = f"{public_url}/api/escalations/{esc.id}/confirm?token={esc.confirm_token}&match=yes"
            confirm_no_url = f"{public_url}/api/escalations/{esc.id}/confirm?token={esc.confirm_token}&match=no"

            issues_html = "".join(f"<li>{iss.get('type', 'issue').replace('_', ' ').capitalize()}: {iss.get('detail', '')}</li>" for iss in esc.issues) if esc.issues else "<li>Automated system was unable to complete the request.</li>"
            issues_text = "\n".join(f"- {iss.get('type', 'issue')}: {iss.get('detail', '')}" for iss in esc.issues) if esc.issues else "- Request could not be completed automatically."

            snippet_lines = esc.transcript_snippet[-6:] if esc.transcript_snippet else []
            snippet_html = "".join(f"<p><strong>{s.get('speaker', '').capitalize()}:</strong> {s.get('text', '')}</p>" for s in snippet_lines)
            snippet_text = "\n".join(f"{s.get('speaker', '').capitalize()}: {s.get('text', '')}" for s in snippet_lines)

            caller_subject = f"Your request {esc.id}: please confirm we captured your issue correctly"
            caller_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
                <h2>Support Request Update</h2>
                <p>Hello {esc.caller_name},</p>
                <p>We are reviewing your recent call regarding <strong>{esc.caller_intent}</strong>.</p>
                <p><strong>Reference ID:</strong> {esc.id}<br>
                <strong>Date & Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
                
                <h3>What We Recorded:</h3>
                <ul>{issues_html}</ul>
                
                <h3>Recent Conversation:</h3>
                <div style="background: #f4f4f4; padding: 10px; border-radius: 4px;">{snippet_html}</div>

                <div style="margin: 25px 0; padding: 15px; border: 1px solid #ddd; border-radius: 6px; text-align: center;">
                    <p style="font-weight: bold; margin-bottom: 12px;">Does this match what you faced?</p>
                    <a href="{confirm_yes_url}" style="background: #10b981; color: white; padding: 10px 18px; text-decoration: none; border-radius: 4px; margin-right: 10px;">Yes, this is my issue</a>
                    <a href="{confirm_no_url}" style="background: #ef4444; color: white; padding: 10px 18px; text-decoration: none; border-radius: 4px;">No, this is different</a>
                </div>

                <p><strong>Need immediate help?</strong> Call us on <strong>{support_phone}</strong> ({support_hours}).</p>
            </div>
            """

            caller_text = f"""Support Request Update (Ref: {esc.id})
Hello {esc.caller_name},
We are reviewing your recent call regarding: {esc.caller_intent}

What We Recorded:
{issues_text}

Recent Conversation:
{snippet_text}

Does this match what you faced?
- Yes: {confirm_yes_url}
- No: {confirm_no_url}

Need immediate help? Call us on {support_phone} ({support_hours}).
"""
            try:
                res = await send_smtp_email(esc.caller_email, caller_subject, caller_html, text_body=caller_text)
                if res.get("status") == "sent":
                    email_sent = True
            except Exception as e:
                logger.warning(f"Failed to send caller escalation email: {e}")

        # 2. Email to business team
        target_email = ""
        if biz:
            routes = (biz.escalation or {}).get("email_routes", {})
            target_email = routes.get(esc.reason, routes.get("default", biz.contact_email or settings.SMTP_FROM))
        if not target_email:
            target_email = settings.SMTP_FROM or "team@aura.ai"

        team_subject = f"[{esc.priority.upper()}] Escalation Report {esc.id}: {esc.caller_name}"
        team_html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h3>Escalation Alert [{esc.priority.upper()}]</h3>
            <p><strong>Ref:</strong> {esc.id} | <strong>Reason:</strong> {esc.reason}</p>
            <p><strong>Caller:</strong> {esc.caller_name} ({esc.caller_phone})</p>
            <p><strong>Intent:</strong> {esc.caller_intent}</p>
            <p><strong>Summary:</strong> {esc.summary}</p>
            <p><strong>Attempts:</strong> {esc.agent_attempts}</p>
        </div>
        """
        try:
            team_res = await send_smtp_email(target_email, team_subject, team_html, text_body=esc.summary)
            if team_res.get("status") == "sent":
                email_sent = True
        except Exception as e:
            logger.warning(f"Failed to send team escalation email: {e}")

        # Update status
        if email_sent:
            esc.email_status = "sent"
        elif not settings.SMTP_HOST:
            esc.email_status = "not_configured"
        else:
            esc.email_status = "failed"
        await db.commit()
