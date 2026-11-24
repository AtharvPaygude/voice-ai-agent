"""
Escalation Reports API routes for Aura AI.
Allows viewing, tracking, resolving, and resending escalation reports.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Escalation, BusinessProfile
from app.core.config import settings
from app.core.escalation_report import send_escalation_emails

router = APIRouter()


class EscalationUpdateStatus(BaseModel):
    status: str  # new, sent, acknowledged, resolved, failed, pending


class EscalationResponse(BaseModel):
    id: str
    call_id: Optional[str] = None
    business_profile_id: Optional[str] = None
    caller_name: str
    caller_phone: str
    caller_email: str = ""
    language: str
    reason: str
    priority: str
    caller_intent: str
    agent_attempts: str
    summary: str
    transcript_snippet: List[dict]
    tools_used: List[str]
    issues: List[dict] = []
    user_confirmation: str = "pending"
    user_note: str = ""
    email_status: str = "not_sent"
    requested_action: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[EscalationResponse])
async def list_escalations(
    status: Optional[str] = None,
    business_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all escalation reports, optionally filtered by status or business."""
    stmt = select(Escalation).order_by(Escalation.created_at.desc())
    if status:
        stmt = stmt.where(Escalation.status == status)
    if business_id:
        stmt = stmt.where(Escalation.business_profile_id == business_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{escalation_id}", response_model=EscalationResponse)
async def get_escalation(escalation_id: str, db: AsyncSession = Depends(get_db)):
    """Get single escalation report details."""
    esc = await db.get(Escalation, escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation report not found")
    return esc


@router.patch("/{escalation_id}/status", response_model=EscalationResponse)
async def update_escalation_status(
    escalation_id: str, data: EscalationUpdateStatus, db: AsyncSession = Depends(get_db)
):
    """Update status of an escalation report (e.g. acknowledge, resolve)."""
    esc = await db.get(Escalation, escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation report not found")

    esc.status = data.status
    esc.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(esc)
    return esc


@router.get("/{escalation_id}/confirm", response_class=HTMLResponse)
async def confirm_escalation(
    escalation_id: str,
    token: str,
    match: str,
    note: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for caller to verify or dispute their recorded issue report."""
    esc = await db.get(Escalation, escalation_id)
    if not esc or not esc.confirm_token or esc.confirm_token != token:
        raise HTTPException(status_code=403, detail="Invalid confirmation token")

    is_yes = match.lower() in ("yes", "true", "1")
    esc.user_confirmation = "confirmed" if is_yes else "disputed"
    esc.status = "acknowledged" if is_yes else "pending"
    if note:
        esc.user_note = note
    esc.updated_at = datetime.utcnow()
    await db.commit()

    biz = await db.get(BusinessProfile, esc.business_profile_id) if esc.business_profile_id else None
    support_phone = (biz.contact_phone if biz and biz.contact_phone else settings.SUPPORT_PHONE) or "our support team"

    msg = "Thank you for confirming. Our team is already working on your request." if is_yes else "Thank you for your feedback. We have marked this for immediate review by our team."
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>Request Confirmation</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 20px;">
        <div style="background: #1e293b; padding: 32px; border-radius: 12px; max-width: 480px; width: 100%; text-align: center; border: 1px solid #334155;">
            <h2 style="color: #38bdf8; margin-top: 0;">Feedback Received</h2>
            <p style="font-size: 16px; line-height: 1.5; color: #cbd5e1;">{msg}</p>
            <p style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #334155; color: #94a3b8; font-size: 14px;">
                Reference ID: <strong style="color: #f8fafc;">{esc.id}</strong><br>
                For immediate assistance, call: <strong style="color: #38bdf8;">{support_phone}</strong> ({settings.SUPPORT_HOURS})
            </p>
        </div>
    </body>
    </html>
    """)


@router.get("/{escalation_id}/report")
async def get_escalation_report(escalation_id: str, db: AsyncSession = Depends(get_db)):
    """Full report JSON including issues, transcript, and caller confirmation."""
    esc = await db.get(Escalation, escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation report not found")
    biz = await db.get(BusinessProfile, esc.business_profile_id) if esc.business_profile_id else None
    support_phone = (biz.contact_phone if biz and biz.contact_phone else settings.SUPPORT_PHONE) or ""
    return {
        "id": esc.id,
        "call_id": esc.call_id,
        "caller_name": esc.caller_name,
        "caller_phone": esc.caller_phone,
        "caller_email": esc.caller_email,
        "support_phone": support_phone,
        "reason": esc.reason,
        "priority": esc.priority,
        "status": esc.status,
        "email_status": esc.email_status,
        "user_confirmation": esc.user_confirmation,
        "user_note": esc.user_note,
        "caller_intent": esc.caller_intent,
        "agent_attempts": esc.agent_attempts,
        "summary": esc.summary,
        "issues": esc.issues or [],
        "transcript_snippet": esc.transcript_snippet or [],
        "tools_used": esc.tools_used or [],
        "created_at": esc.created_at,
        "updated_at": esc.updated_at,
    }


@router.post("/{escalation_id}/resend")
async def resend_escalation_email(escalation_id: str, db: AsyncSession = Depends(get_db)):
    """Resend escalation email via SMTP using rich builder."""
    esc = await db.get(Escalation, escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation report not found")

    await send_escalation_emails(esc.id)
    await db.refresh(esc)
    return {"status": "ok", "email_status": esc.email_status}
