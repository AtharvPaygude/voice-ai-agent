"""
Call management API routes — now backed by the real database instead of
hardcoded MOCK_CALLS / MOCK_MESSAGES lists.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Call, Message

router = APIRouter()


# ─── Response Models ────────────────────────────────────────────────────────

class CallSummary(BaseModel):
    id: str
    business_profile_id: Optional[str] = None
    caller_id: str
    initial_language: str
    current_language: str
    languages_used: List[str]
    duration: int  # seconds
    intent: str
    sentiment: str
    lead_score: int
    summary: str
    status: str  # active, completed, transferred
    started_at: str
    ended_at: Optional[str] = None

    class Config:
        from_attributes = True


class CallMessage(BaseModel):
    id: str
    call_id: str
    speaker: str  # user, agent
    text: str
    detected_language: str
    confidence: float
    timestamp: str

    class Config:
        from_attributes = True


def _call_to_summary(call: Call) -> CallSummary:
    return CallSummary(
        id=call.id,
        business_profile_id=call.business_profile_id,
        caller_id=call.caller_id,
        initial_language=call.initial_language,
        current_language=call.current_language,
        languages_used=call.languages_used or [],
        duration=call.duration,
        intent=call.intent,
        sentiment=call.sentiment,
        lead_score=call.lead_score,
        summary=call.summary,
        status=call.status,
        started_at=call.started_at.isoformat() + "Z",
        ended_at=(call.ended_at.isoformat() + "Z") if call.ended_at else None,
    )


def _msg_to_model(msg: Message) -> CallMessage:
    return CallMessage(
        id=msg.id,
        call_id=msg.call_id,
        speaker=msg.speaker,
        text=msg.text,
        detected_language=msg.detected_language,
        confidence=msg.confidence,
        timestamp=msg.timestamp.isoformat() + "Z",
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[CallSummary])
async def list_calls(db: AsyncSession = Depends(get_db)):
    """List all calls, most recent first."""
    result = await db.execute(select(Call).order_by(Call.started_at.desc()))
    calls = result.scalars().all()
    return [_call_to_summary(c) for c in calls]


@router.get("/{call_id}", response_model=CallSummary)
async def get_call(call_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific call."""
    call = await db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return _call_to_summary(call)


@router.get("/{call_id}/messages", response_model=List[CallMessage])
async def get_call_messages(call_id: str, db: AsyncSession = Depends(get_db)):
    """Get messages for a specific call, in chronological order."""
    result = await db.execute(
        select(Message).where(Message.call_id == call_id).order_by(Message.timestamp.asc())
    )
    return [_msg_to_model(m) for m in result.scalars().all()]


@router.get("/{call_id}/summary")
async def get_call_summary(call_id: str, db: AsyncSession = Depends(get_db)):
    """Get AI-generated call summary."""
    call = await db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return {
        "call_id": call.id,
        "summary": call.summary,
        "intent": call.intent,
        "sentiment": call.sentiment,
        "lead_score": call.lead_score,
        "languages_used": call.languages_used or [],
        "duration": call.duration,
    }
