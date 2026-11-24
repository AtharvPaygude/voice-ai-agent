"""
Data migration script: SQLite to Supabase PostgreSQL for AURA Voice AI.

Reads existing records from SQLite (backend/aura_voice.db) and safely
migrates them to Supabase PostgreSQL, preserving:
- Business profiles
- Users
- Customers
- Calls
- Messages
- Appointments
- Call jobs
- Leads & Tickets

Handles:
- Foreign key dependency order
- Automatic placeholder creation for orphan test calls so no messages are lost
- JSON string to Python dict/list parsing
- Datetime string to datetime object parsing
- Integer to boolean conversion
- Idempotent insertion (skips existing IDs, preserves data)
- Preserves the original SQLite database file untouched.
"""
import argparse
import asyncio
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, func
from app.db.database import AsyncSessionLocal, engine
from app.db import models


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_dt(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    try:
        dt = datetime.fromisoformat(val)
        return dt.replace(tzinfo=None)
    except Exception:
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
        except Exception:
            try:
                return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None


def parse_json(val, default):
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return default
    return default


def parse_bool(val, default=False):
    if val is None:
        return default
    return bool(val)


async def migrate_data(sqlite_path: Path, dry_run: bool = False):
    if not sqlite_path.exists():
        print(f"Error: SQLite database file not found at {sqlite_path}")
        return

    print(f"Opening SQLite database: {sqlite_path}")
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if engine is None or AsyncSessionLocal is None:
        print("Error: PostgreSQL engine is not initialized. Check backend/.env.")
        return

    async with AsyncSessionLocal() as session:
        # 1. Business Profiles
        cur.execute("SELECT * FROM business_profiles")
        bp_rows = cur.fetchall()
        print(f"\n--- Migrating Business Profiles ({len(bp_rows)} found) ---")
        for r in bp_rows:
            d = dict(r)
            existing = await session.get(models.BusinessProfile, d["id"])
            if not existing:
                bp = models.BusinessProfile(
                    id=d["id"],
                    name=d["name"],
                    industry=d.get("industry", "service_business"),
                    description=d.get("description", ""),
                    offerings=parse_json(d.get("offerings"), []),
                    capabilities=parse_json(d.get("capabilities"), []),
                    knowledge_base=parse_json(d.get("knowledge_base"), []),
                    tools=parse_json(d.get("tools"), []),
                    workflows=parse_json(d.get("workflows"), []),
                    permissions=parse_json(d.get("permissions"), {}),
                    policies=parse_json(d.get("policies"), {}),
                    booking_unit_label=d.get("booking_unit_label", "appointment"),
                    persona=d.get("persona", "professional"),
                    category=d.get("category", "service_business"),
                    address=d.get("address", ""),
                    city=d.get("city", ""),
                    timezone=d.get("timezone", "UTC"),
                    contact_email=d.get("contact_email", ""),
                    contact_phone=d.get("contact_phone", ""),
                    operating_hours=parse_json(d.get("operating_hours"), {}),
                    breaks=parse_json(d.get("breaks"), []),
                    slot_duration_minutes=int(d.get("slot_duration_minutes", 30)),
                    specialties=parse_json(d.get("specialties"), []),
                    practitioners=parse_json(d.get("practitioners"), []),
                    inventory=parse_json(d.get("inventory"), []),
                    holidays=parse_json(d.get("holidays"), []),
                    onboarding_status=d.get("onboarding_status", "completed"),
                    onboarding_step=d.get("onboarding_step", "done"),
                    onboarding_answers=parse_json(d.get("onboarding_answers"), {}),
                    is_published=parse_bool(d.get("is_published"), True),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                )
                session.add(bp)
                print(f"  + Added BusinessProfile: {bp.name} ({bp.id})")
            else:
                print(f"  = Skipping existing BusinessProfile: {existing.name} ({existing.id})")

        await session.flush()

        # 2. Users
        cur.execute("SELECT * FROM users")
        user_rows = cur.fetchall()
        print(f"\n--- Migrating Users ({len(user_rows)} found) ---")
        for r in user_rows:
            d = dict(r)
            existing = await session.get(models.User, d["id"])
            if not existing:
                u = models.User(
                    id=d["id"],
                    email=d["email"],
                    password_hash=d["password_hash"],
                    full_name=d.get("full_name", ""),
                    role=d.get("role", "customer"),
                    business_profile_id=d.get("business_profile_id"),
                    session_token_hash=d.get("session_token_hash"),
                    is_active=parse_bool(d.get("is_active"), True),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                    last_login_at=parse_dt(d.get("last_login_at")),
                )
                session.add(u)
                print(f"  + Added User: {u.email} ({u.id})")
            else:
                print(f"  = Skipping existing User: {existing.email} ({existing.id})")

        await session.flush()

        # 3. Customers
        cur.execute("SELECT * FROM customers")
        cust_rows = cur.fetchall()
        print(f"\n--- Migrating Customers ({len(cust_rows)} found) ---")
        for r in cust_rows:
            d = dict(r)
            existing = await session.get(models.Customer, d["id"])
            if not existing:
                c = models.Customer(
                    id=d["id"],
                    phone=d["phone"],
                    name=d.get("name", "Valued Customer"),
                    business_profile_id=d.get("business_profile_id"),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                )
                session.add(c)
                print(f"  + Added Customer: {c.name} ({c.phone})")
            else:
                print(f"  = Skipping existing Customer: {existing.name} ({existing.id})")

        await session.flush()

        # 4. Calls
        cur.execute("SELECT * FROM calls")
        call_rows = cur.fetchall()
        print(f"\n--- Migrating Calls ({len(call_rows)} found) ---")
        for r in call_rows:
            d = dict(r)
            existing = await session.get(models.Call, d["id"])
            if not existing:
                call = models.Call(
                    id=d["id"],
                    business_profile_id=d.get("business_profile_id"),
                    customer_id=d.get("customer_id"),
                    caller_id=d.get("caller_id", "web-demo"),
                    initial_language=d.get("initial_language", "en"),
                    current_language=d.get("current_language", "en"),
                    languages_used=parse_json(d.get("languages_used"), []),
                    duration=int(d.get("duration", 0)),
                    intent=d.get("intent", "unknown"),
                    sentiment=d.get("sentiment", "neutral"),
                    lead_score=int(d.get("lead_score", 0)),
                    summary=d.get("summary", ""),
                    status=d.get("status", "completed"),
                    started_at=parse_dt(d.get("started_at")) or now_utc(),
                    ended_at=parse_dt(d.get("ended_at")),
                )
                session.add(call)
                print(f"  + Added Call: {call.id}")
            else:
                print(f"  = Skipping existing Call: {existing.id}")

        # Ensure orphan test call IDs referenced by messages exist
        cur.execute("SELECT DISTINCT call_id FROM messages WHERE call_id NOT IN (SELECT id FROM calls)")
        missing_call_ids = [r[0] for r in cur.fetchall()]
        if missing_call_ids:
            print(f"  + Creating {len(missing_call_ids)} placeholder call record(s) for orphan test messages...")
            for missing_id in missing_call_ids:
                existing = await session.get(models.Call, missing_id)
                if not existing:
                    placeholder = models.Call(
                        id=missing_id,
                        caller_id="test-harness",
                        intent="test",
                        sentiment="neutral",
                        summary="Historical test call record",
                        status="completed",
                        started_at=now_utc(),
                    )
                    session.add(placeholder)

        await session.flush()

        # 5. Messages
        cur.execute("SELECT * FROM messages")
        msg_rows = cur.fetchall()
        print(f"\n--- Migrating Messages ({len(msg_rows)} found) ---")
        for r in msg_rows:
            d = dict(r)
            existing = await session.get(models.Message, d["id"])
            if not existing:
                msg = models.Message(
                    id=d["id"],
                    call_id=d["call_id"],
                    speaker=d["speaker"],
                    text=d["text"],
                    detected_language=d.get("detected_language", "en"),
                    confidence=float(d.get("confidence", 1.0)),
                    timestamp=parse_dt(d.get("timestamp")) or now_utc(),
                )
                session.add(msg)
            else:
                pass
        print(f"  + Processed {len(msg_rows)} messages.")

        await session.flush()

        # 6. Appointments
        cur.execute("SELECT * FROM appointments")
        apt_rows = cur.fetchall()
        print(f"\n--- Migrating Appointments ({len(apt_rows)} found) ---")
        for r in apt_rows:
            d = dict(r)
            existing = await session.get(models.Appointment, d["id"])
            if not existing:
                apt = models.Appointment(
                    id=d["id"],
                    business_profile_id=d.get("business_profile_id"),
                    call_id=d.get("call_id"),
                    date=d["date"],
                    time=d["time"],
                    service=d.get("service", "Consultation"),
                    practitioner_name=d.get("practitioner_name"),
                    customer_name=d.get("customer_name"),
                    customer_phone=d.get("customer_phone"),
                    duration_minutes=int(d.get("duration_minutes", 30)),
                    notes=d.get("notes", ""),
                    status=d.get("status", "confirmed"),
                    reminder_enabled=parse_bool(d.get("reminder_enabled"), False),
                    reminder_offset=d.get("reminder_offset", "1_day"),
                    reminder_sent=parse_bool(d.get("reminder_sent"), False),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                )
                session.add(apt)
                print(f"  + Added Appointment: {apt.id} ({apt.service} on {apt.date})")
            else:
                print(f"  = Skipping existing Appointment: {existing.id}")

        await session.flush()

        # 7. Call Jobs
        cur.execute("SELECT * FROM call_jobs")
        job_rows = cur.fetchall()
        print(f"\n--- Migrating Call Jobs ({len(job_rows)} found) ---")
        for r in job_rows:
            d = dict(r)
            existing = await session.get(models.CallJob, d["id"])
            if not existing:
                job = models.CallJob(
                    id=d["id"],
                    customer_id=d.get("customer_id"),
                    business_profile_id=d.get("business_profile_id"),
                    reason=d.get("reason", "reminder"),
                    scheduled_for=parse_dt(d.get("scheduled_for")) or now_utc(),
                    status=d.get("status", "pending"),
                    related_appointment_id=d.get("related_appointment_id"),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                )
                session.add(job)
                print(f"  + Added CallJob: {job.id}")
            else:
                print(f"  = Skipping existing CallJob: {existing.id}")

        await session.flush()

        # 8. Leads
        cur.execute("SELECT * FROM leads")
        lead_rows = cur.fetchall()
        print(f"\n--- Migrating Leads ({len(lead_rows)} found) ---")
        for r in lead_rows:
            d = dict(r)
            existing = await session.get(models.Lead, d["id"])
            if not existing:
                lead = models.Lead(
                    id=d["id"],
                    call_id=d.get("call_id"),
                    name=d["name"],
                    phone=d.get("phone", ""),
                    interest=d.get("interest", ""),
                    score=int(d.get("score", 75)),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                )
                session.add(lead)
                print(f"  + Added Lead: {lead.id}")

        await session.flush()

        # 9. Tickets
        cur.execute("SELECT * FROM tickets")
        ticket_rows = cur.fetchall()
        print(f"\n--- Migrating Tickets ({len(ticket_rows)} found) ---")
        for r in ticket_rows:
            d = dict(r)
            existing = await session.get(models.Ticket, d["id"])
            if not existing:
                ticket = models.Ticket(
                    id=d["id"],
                    call_id=d.get("call_id"),
                    subject=d["subject"],
                    description=d.get("description", ""),
                    priority=d.get("priority", "medium"),
                    status=d.get("status", "open"),
                    created_at=parse_dt(d.get("created_at")) or now_utc(),
                )
                session.add(ticket)
                print(f"  + Added Ticket: {ticket.id}")

        if dry_run:
            print("\n[DRY RUN] Rolling back transaction. No changes committed to PostgreSQL.")
            await session.rollback()
        else:
            await session.commit()
            print("\nSUCCESS: All records successfully committed to Supabase PostgreSQL!")

    conn.close()


async def verify_counts():
    """Verify row counts in PostgreSQL."""
    print("\n--- Verifying PostgreSQL Table Counts ---")
    async with AsyncSessionLocal() as session:
        for model in [
            models.BusinessProfile,
            models.User,
            models.Customer,
            models.Call,
            models.Message,
            models.Appointment,
            models.CallJob,
            models.Lead,
            models.Ticket,
        ]:
            res = await session.execute(select(func.count()).select_from(model))
            count = res.scalar() or 0
            print(f"  {model.__tablename__}: {count} rows")


async def async_main(sqlite_path: Path, dry_run: bool, verify_only: bool):
    try:
        if verify_only:
            await verify_counts()
        else:
            await migrate_data(sqlite_path, dry_run=dry_run)
            await verify_counts()
    finally:
        if engine is not None:
            await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to Supabase PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=BACKEND_DIR / "aura_voice.db",
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without committing changes",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only check and display row counts in PostgreSQL",
    )
    args = parser.parse_args()

    asyncio.run(async_main(args.sqlite_path, dry_run=args.dry_run, verify_only=args.verify_only))


if __name__ == "__main__":
    main()
