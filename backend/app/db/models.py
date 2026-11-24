"""
SQLAlchemy ORM models for Aura AI.
Production-grade persisted entities for calls, messages, business profiles,
appointments, customers, leads, tickets, call jobs, escalations, and knowledge base.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def gen_id(prefix: str) -> str:
    """Generate a short, readable unique id like 'call-8f3a2c91d4'."""
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


class User(Base):
    """Authentication user — either admin (business owner) or customer."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("usr"))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)  # PBKDF2-SHA256
    full_name: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="customer")  # admin | customer
    business_profile_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("business_profiles.id"), nullable=True
    )
    session_token_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BusinessProfile(Base):
    """Business profile representing an organization or tenant."""
    __tablename__ = "business_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("biz"))
    name: Mapped[str] = mapped_column(String)
    industry: Mapped[str] = mapped_column(String, default="service_business")
    description: Mapped[str] = mapped_column(String, default="")
    offerings: Mapped[List[dict]] = mapped_column(JSON, default=list)
    capabilities: Mapped[List[str]] = mapped_column(JSON, default=list)
    knowledge_base: Mapped[List[str]] = mapped_column(JSON, default=list)
    tools: Mapped[List[str]] = mapped_column(JSON, default=list)
    workflows: Mapped[List[str]] = mapped_column(JSON, default=list)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    policies: Mapped[dict] = mapped_column(JSON, default=dict)
    booking_unit_label: Mapped[str] = mapped_column(String, default="appointment")
    persona: Mapped[str] = mapped_column(String, default="professional")
    speaking_style: Mapped[str] = mapped_column(String, default="friendly")  # friendly | professional | empathetic
    
    # Operational & scheduling configuration
    category: Mapped[str] = mapped_column(String, default="service_business")
    address: Mapped[str] = mapped_column(String, default="")
    city: Mapped[str] = mapped_column(String, default="")
    timezone: Mapped[str] = mapped_column(String, default="UTC")
    contact_email: Mapped[str] = mapped_column(String, default="")
    contact_phone: Mapped[str] = mapped_column(String, default="")
    operating_hours: Mapped[dict] = mapped_column(JSON, default=dict)
    breaks: Mapped[List[dict]] = mapped_column(JSON, default=list)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    specialties: Mapped[List[str]] = mapped_column(JSON, default=list)
    practitioners: Mapped[List[dict]] = mapped_column(JSON, default=list)
    inventory: Mapped[List[dict]] = mapped_column(JSON, default=list)
    holidays: Mapped[List[str]] = mapped_column(JSON, default=list)
    faqs: Mapped[List[dict]] = mapped_column(JSON, default=list)
    
    # Escalation settings
    escalation: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Onboarding workflow progress
    onboarding_status: Mapped[str] = mapped_column(String, default="completed")
    onboarding_step: Mapped[str] = mapped_column(String, default="done")
    onboarding_answers: Mapped[dict] = mapped_column(JSON, default=dict)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Customer(Base):
    """Customer profile resolved by phone number."""
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("cust"))
    phone: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="Unknown caller")
    email: Mapped[str] = mapped_column(String, default="")
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    calls: Mapped[List["Call"]] = relationship(back_populates="customer", order_by="Call.started_at.desc()")


class Call(Base):
    """A real-time voice call session."""
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("call"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customers.id"), nullable=True)
    caller_id: Mapped[str] = mapped_column(String, default="unknown")
    initial_language: Mapped[str] = mapped_column(String, default="en")
    current_language: Mapped[str] = mapped_column(String, default="en")
    speaking_style: Mapped[str] = mapped_column(String, default="friendly")
    languages_used: Mapped[List[str]] = mapped_column(JSON, default=list)
    duration: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    intent: Mapped[str] = mapped_column(String, default="unknown")
    sentiment: Mapped[str] = mapped_column(String, default="neutral")
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="active")  # active, completed, transferred
    
    # Latency tracking
    latency_first_token_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_first_audio_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_stt_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_total_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    customer: Mapped[Optional["Customer"]] = relationship(back_populates="calls")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="call", cascade="all, delete-orphan", order_by="Message.timestamp"
    )


class Message(Base):
    """A single utterance in a call."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("msg"))
    call_id: Mapped[str] = mapped_column(String, ForeignKey("calls.id"))
    speaker: Mapped[str] = mapped_column(String)  # user, agent, system
    text: Mapped[str] = mapped_column(String)
    detected_language: Mapped[str] = mapped_column(String, default="en")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    call: Mapped["Call"] = relationship(back_populates="messages")


class Appointment(Base):
    """Scheduled appointment or booking."""
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("APT"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    call_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("calls.id"), nullable=True)
    date: Mapped[str] = mapped_column(String)
    time: Mapped[str] = mapped_column(String)
    service: Mapped[str] = mapped_column(String, default="Consultation")
    practitioner_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    notes: Mapped[Optional[str]] = mapped_column(String, default="", nullable=True)
    status: Mapped[str] = mapped_column(String, default="confirmed")  # confirmed, cancelled
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_offset: Mapped[str] = mapped_column(String, default="1_day")
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_status: Mapped[str] = mapped_column(String, default="pending")  # pending, called, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Lead(Base):
    """Qualified sales lead."""
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("LEAD"))
    call_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("calls.id"), nullable=True)
    name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String, default="")
    interest: Mapped[str] = mapped_column(String, default="")
    score: Mapped[int] = mapped_column(Integer, default=75)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Ticket(Base):
    """Support or in-stay service ticket."""
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("TKT"))
    call_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("calls.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="")
    priority: Mapped[str] = mapped_column(String, default="medium")
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class CallJob(Base):
    """Background scheduled telephony/reminder job."""
    __tablename__ = "call_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("job"))
    customer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customers.id"), nullable=True)
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    reason: Mapped[str] = mapped_column(String, default="reminder")
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, done, failed
    related_appointment_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("appointments.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Escalation(Base):
    """Escalation report generated when the agent cannot assist or emergency occurs."""
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("esc"))
    call_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("calls.id"), nullable=True)
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    caller_name: Mapped[str] = mapped_column(String, default="Unknown caller")
    caller_phone: Mapped[str] = mapped_column(String, default="")
    language: Mapped[str] = mapped_column(String, default="en")
    reason: Mapped[str] = mapped_column(String, default="general")  # medical, billing, complaint, sales, technical, other
    priority: Mapped[str] = mapped_column(String, default="medium")  # low, medium, high, urgent
    caller_intent: Mapped[str] = mapped_column(String, default="")
    agent_attempts: Mapped[str] = mapped_column(String, default="")
    summary: Mapped[str] = mapped_column(String, default="")
    transcript_snippet: Mapped[List[dict]] = mapped_column(JSON, default=list)
    tools_used: Mapped[List[str]] = mapped_column(JSON, default=list)
    issues: Mapped[List[dict]] = mapped_column(JSON, default=list)
    caller_email: Mapped[str] = mapped_column(String, default="")
    confirm_token: Mapped[str] = mapped_column(String, default="")
    user_confirmation: Mapped[str] = mapped_column(String, default="pending")  # pending | confirmed | disputed
    user_note: Mapped[str] = mapped_column(String, default="")
    email_status: Mapped[str] = mapped_column(String, default="not_sent")  # not_sent | sent | failed | not_configured
    requested_action: Mapped[str] = mapped_column(String, default="email")  # email | call
    status: Mapped[str] = mapped_column(String, default="new")  # new, sent, acknowledged, resolved, failed, pending
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class KnowledgeDocument(Base):
    """Knowledge base document for RAG indexing."""
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("doc"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    title: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String, default="txt")  # txt, pdf, docx, csv, md
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="indexed")  # indexed, processing, error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """Embedded chunk of a knowledge document."""
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("chk"))
    document_id: Mapped[str] = mapped_column(String, ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[List[float]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")


def gen_ref(prefix: str) -> str:
    """Generate a human-readable reference code like APT-7K3Q9."""
    import random, string
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=5))
    return f"{prefix}-{suffix}"


class FAQ(Base):
    __tablename__ = "faqs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("faq"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String, default="general")
    language: Mapped[str] = mapped_column(String, default="en")
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Resource(Base):
    """Doctor, consultant or technician."""
    __tablename__ = "resources"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("res"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String, default="doctor")  # doctor | consultant | technician
    name: Mapped[str] = mapped_column(String)
    specialty: Mapped[str] = mapped_column(String, default="")
    fee: Mapped[int] = mapped_column(Integer, default=500)  # in rupees
    languages: Mapped[List[str]] = mapped_column(JSON, default=list)
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class ResourceSchedule(Base):
    __tablename__ = "resource_schedules"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("rsch"))
    resource_id: Mapped[str] = mapped_column(String, ForeignKey("resources.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Monday..5=Saturday
    start_time: Mapped[str] = mapped_column(String, default="09:00")
    end_time: Mapped[str] = mapped_column(String, default="18:00")
    break_start: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    break_end: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class ResourceTimeOff(Base):
    __tablename__ = "resource_time_offs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("rto"))
    resource_id: Mapped[str] = mapped_column(String, ForeignKey("resources.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[str] = mapped_column(String, default="Leave")


class Booking(Base):
    """Booking with conflict-safe reference."""
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("book"))
    reference: Mapped[str] = mapped_column(String, unique=True, default=lambda: gen_ref("APT"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("resources.id"), nullable=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customers.id"), nullable=True)
    call_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("calls.id"), nullable=True)
    service: Mapped[str] = mapped_column(String, default="Consultation")
    reason: Mapped[str] = mapped_column(String, default="")
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="confirmed")  # pending|confirmed|cancelled|completed|no_show
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_offsets: Mapped[List[str]] = mapped_column(JSON, default=list)
    reminder_status: Mapped[str] = mapped_column(String, default="pending")  # pending|called|failed
    notes: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class RoomType(Base):
    __tablename__ = "room_types"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("rtyp"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String)  # Standard, Deluxe, Executive Suite, Family
    description: Mapped[str] = mapped_column(Text, default="")
    base_price: Mapped[int] = mapped_column(Integer, default=3000)  # per night, INR
    max_guests: Mapped[int] = mapped_column(Integer, default=2)
    amenities: Mapped[List[str]] = mapped_column(JSON, default=list)
    inventory_count: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("room"))
    room_type_id: Mapped[str] = mapped_column(String, ForeignKey("room_types.id"), index=True)
    number: Mapped[str] = mapped_column(String)
    floor: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="available")


class Reservation(Base):
    __tablename__ = "reservations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("rsrv"))
    reference: Mapped[str] = mapped_column(String, unique=True, default=lambda: gen_ref("RSV"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customers.id"), nullable=True)
    room_type_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("room_types.id"), nullable=True)
    room_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("rooms.id"), nullable=True)
    call_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("calls.id"), nullable=True)
    check_in: Mapped[str] = mapped_column(String)   # ISO date
    check_out: Mapped[str] = mapped_column(String)  # ISO date
    guests: Mapped[int] = mapped_column(Integer, default=1)
    special_requests: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="confirmed")
    total_price: Mapped[int] = mapped_column(Integer, default=0)
    cancellation_policy: Mapped[str] = mapped_column(String, default="Free cancellation up to 48 hours before check-in")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Facility(Base):
    __tablename__ = "facilities"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("fac"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    opening_time: Mapped[str] = mapped_column(String, default="06:00")
    closing_time: Mapped[str] = mapped_column(String, default="22:00")
    location: Mapped[str] = mapped_column(String, default="")


class Offering(Base):
    __tablename__ = "offerings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("off"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String, default="service")
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String, default="INR")
    billing_period: Mapped[str] = mapped_column(String, default="one-time")
    features: Mapped[List[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("ord"))
    order_number: Mapped[str] = mapped_column(String, unique=True, default=lambda: gen_ref("ORD"))
    business_profile_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("business_profiles.id"), nullable=True, index=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, default="placed")
    total: Mapped[int] = mapped_column(Integer, default=0)
    tracking_id: Mapped[str] = mapped_column(String, default="")
    carrier: Mapped[str] = mapped_column(String, default="")
    eta: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    placed_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class ToolAuditLog(Base):
    __tablename__ = "tool_audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("tal"))
    call_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tool: Mapped[str] = mapped_column(String)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: gen_id("obx"))
    channel: Mapped[str] = mapped_column(String, default="email")
    to_addr: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="pending")
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
