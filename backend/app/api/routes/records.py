"""
Records API routes for Aura AI.
Serves real persisted data from bookings, reservations, orders, leads, tickets,
escalations, and outbox with business_profile_id filtering.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import (
    Booking, Reservation, Order, Lead, Ticket, Escalation, Outbox, RoomType, Resource, Customer
)

router = APIRouter()


@router.get("/bookings")
async def get_bookings(
    business_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    q = select(Booking).order_by(Booking.created_at.desc()).limit(limit)
    if business_id:
        q = q.where(Booking.business_profile_id == business_id)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "reference": r.reference,
            "business_id": r.business_profile_id,
            "resource_id": r.resource_id,
            "customer_id": r.customer_id,
            "service": r.service,
            "start_at": r.start_at.isoformat() if r.start_at else None,
            "end_at": r.end_at.isoformat() if r.end_at else None,
            "status": r.status,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/reservations")
async def get_reservations(
    business_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    q = select(Reservation).order_by(Reservation.created_at.desc()).limit(limit)
    if business_id:
        q = q.where(Reservation.business_profile_id == business_id)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "reference": r.reference,
            "business_id": r.business_profile_id,
            "customer_id": r.customer_id,
            "room_type_id": r.room_type_id,
            "check_in": r.check_in,
            "check_out": r.check_out,
            "guests": r.guests,
            "special_requests": r.special_requests,
            "status": r.status,
            "total_price": r.total_price,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/orders")
async def get_orders(
    business_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    q = select(Order).order_by(Order.placed_at.desc()).limit(limit)
    if business_id:
        q = q.where(Order.business_profile_id == business_id)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "order_number": r.order_number,
            "business_id": r.business_profile_id,
            "customer_id": r.customer_id,
            "status": r.status,
            "total": r.total,
            "tracking_id": r.tracking_id,
            "carrier": r.carrier,
            "eta": r.eta,
            "placed_at": r.placed_at.isoformat() if r.placed_at else None,
        }
        for r in rows
    ]


@router.get("/leads")
async def get_leads(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db)):
    q = select(Lead).order_by(Lead.created_at.desc()).limit(limit)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "call_id": r.call_id,
            "name": r.name,
            "phone": r.phone,
            "interest": r.interest,
            "score": r.score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/tickets")
async def get_tickets(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db)):
    q = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "call_id": r.call_id,
            "subject": r.subject,
            "description": r.description,
            "priority": r.priority,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/escalations")
async def get_escalations(
    business_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    q = select(Escalation).order_by(Escalation.created_at.desc()).limit(limit)
    if business_id:
        q = q.where(Escalation.business_profile_id == business_id)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "call_id": r.call_id,
            "business_id": r.business_profile_id,
            "caller_name": r.caller_name,
            "caller_phone": r.caller_phone,
            "reason": r.reason,
            "priority": r.priority,
            "summary": r.summary,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/outbox")
async def get_outbox(limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db)):
    q = select(Outbox).order_by(Outbox.created_at.desc()).limit(limit)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "id": r.id,
            "channel": r.channel,
            "to_addr": r.to_addr,
            "subject": r.subject,
            "body": r.body,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        }
        for r in rows
    ]


@router.get("/overview")
async def get_records_overview(db: AsyncSession = Depends(get_db)):
    """Aggregate counts across all record tables for live dashboard."""
    bookings_cnt = (await db.execute(select(func.count(Booking.id)))).scalar() or 0
    reservations_cnt = (await db.execute(select(func.count(Reservation.id)))).scalar() or 0
    orders_cnt = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    leads_cnt = (await db.execute(select(func.count(Lead.id)))).scalar() or 0
    tickets_cnt = (await db.execute(select(func.count(Ticket.id)))).scalar() or 0
    escalations_cnt = (await db.execute(select(func.count(Escalation.id)))).scalar() or 0
    outbox_cnt = (await db.execute(select(func.count(Outbox.id)))).scalar() or 0

    return {
        "bookings": bookings_cnt,
        "reservations": reservations_cnt,
        "orders": orders_cnt,
        "leads": leads_cnt,
        "tickets": tickets_cnt,
        "escalations": escalations_cnt,
        "outbox": outbox_cnt,
    }
