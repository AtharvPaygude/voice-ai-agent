"""
APScheduler background jobs for Appointment Reminders and Outbound CallJobs.

Runs recurring background ticks:
1. check_upcoming_reminders: Finds confirmed appointments whose reminder offset has arrived,
   creates pending CallJobs, and marks reminder_sent=True.
2. process_pending_call_jobs: Polls pending CallJobs scheduled for <= now and dispatches
   outbound calls via app.core.telephony.
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
except ImportError:
    AsyncIOScheduler = None
    scheduler = None
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import Appointment, Booking, Call, Customer, CallJob, gen_id
from app.core.telephony import place_outbound_call

logger = logging.getLogger(__name__)


def parse_offset(offset_str: str) -> timedelta:
    """Parse strings like '1_day', '2_hours', '1_hour', '30_min', '0_min' into a timedelta."""
    clean = str(offset_str or "1_hour").strip().lower()
    if "day" in clean:
        match = re.search(r'\d+', clean)
        days = int(match.group()) if match else 1
        return timedelta(days=days)
    elif "hour" in clean:
        match = re.search(r'\d+', clean)
        hours = int(match.group()) if match else 1
        return timedelta(hours=hours)
    elif "min" in clean:
        match = re.search(r'\d+', clean)
        minutes = int(match.group()) if match else 30
        return timedelta(minutes=minutes)
    elif clean in ("0", "now", "immediate"):
        return timedelta(0)
    return timedelta(hours=1)


def parse_appointment_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse appointment date and time strings into a datetime object."""
    combined = f"{date_str.strip()} {time_str.strip()}"
    formats = [
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %I:%M%p",
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y %I:%M %p",
        "%d/%m/%Y %I:%M %p",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue
    try:
        # Fallback to date only
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return None


async def check_upcoming_reminders() -> int:
    """
    Find Appointments and Bookings where reminder_enabled=True,
    reminder_status != 'called', and the reminder window has arrived.
    Creates a pending CallJob for each.
    """
    created_count = 0
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        # 1. Check Appointment records
        result = await db.execute(
            select(Appointment).where(
                Appointment.reminder_enabled == True,
                Appointment.reminder_status != "called",
                Appointment.reminder_sent == False,
                Appointment.status == "confirmed",
            )
        )
        appointments = result.scalars().all()

        for apt in appointments:
            apt_dt = parse_appointment_datetime(apt.date, apt.time)
            offset = parse_offset(apt.reminder_offset)

            # Check if reminder time window has arrived (lead time)
            reminder_time = (apt_dt - offset) if apt_dt else now

            if now >= reminder_time:
                customer_id = None
                if apt.call_id:
                    call_obj = await db.get(Call, apt.call_id)
                    if call_obj and call_obj.customer_id:
                        customer_id = call_obj.customer_id

                if not customer_id and apt.customer_phone:
                    c_res = await db.execute(select(Customer).where(Customer.phone == apt.customer_phone))
                    cust = c_res.scalars().first()
                    if cust:
                        customer_id = cust.id

                # Create CallJob
                job = CallJob(
                    id=gen_id("job"),
                    customer_id=customer_id,
                    business_profile_id=apt.business_profile_id,
                    reason="reminder",
                    scheduled_for=now,
                    status="pending",
                    related_appointment_id=apt.id,
                )
                db.add(job)
                apt.reminder_status = "queued"
                created_count += 1
                logger.info(f"[SCHEDULER] Queued reminder CallJob {job.id} for Appointment {apt.id}")

        # 2. Check Booking records
        b_res = await db.execute(
            select(Booking).where(
                Booking.reminder_enabled == True,
                Booking.reminder_status == "pending",
                Booking.status == "confirmed",
            )
        )
        bookings = b_res.scalars().all()
        for b in bookings:
            # 1 hour default lead time for bookings
            reminder_time = (b.start_at - timedelta(hours=1)) if b.start_at else now
            if now >= reminder_time:
                # Find matching appointment if exists to satisfy FK constraint
                matching_apt = (await db.execute(
                    select(Appointment).where(Appointment.id == b.reference)
                )).scalars().first()
                related_id = matching_apt.id if matching_apt else None

                # Check if CallJob already created for this reference
                existing_job = (await db.execute(
                    select(CallJob).where(
                        (CallJob.reason == f"reminder:{b.reference}") |
                        (CallJob.related_appointment_id == b.reference)
                    )
                )).scalars().first()
                if not existing_job:
                    job = CallJob(
                        id=gen_id("job"),
                        customer_id=b.customer_id,
                        business_profile_id=b.business_profile_id,
                        reason=f"reminder:{b.reference}",
                        scheduled_for=now,
                        status="pending",
                        related_appointment_id=related_id,
                    )
                    db.add(job)
                    b.reminder_status = "queued"
                    created_count += 1
                    logger.info(f"[SCHEDULER] Queued reminder CallJob {job.id} for Booking {b.reference}")

        if created_count > 0:
            await db.commit()

    return created_count


async def process_pending_call_jobs() -> int:
    """
    Poll pending CallJobs whose scheduled_for <= now and trigger outbound calls.
    Updates reminder_status on Appointment and Booking to 'called' or 'failed'.
    """
    processed_count = 0
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CallJob).where(
                CallJob.status.in_(["pending", "queued"]),
                CallJob.scheduled_for <= now,
            )
        )
        jobs = result.scalars().all()

        for job in jobs:
            phone = "+91-9876543210"  # Default fallback phone
            customer_name = "Valued Customer"
            reminder_details: Dict[str, Any] = {}

            if job.customer_id:
                cust = await db.get(Customer, job.customer_id)
                if cust:
                    phone = cust.phone
                    customer_name = cust.name

            # Fetch appointment or booking details for realistic speech synthesis
            apt_record = None
            book_record = None
            if job.related_appointment_id:
                apt_record = await db.get(Appointment, job.related_appointment_id)
                if not apt_record:
                    b_q = select(Booking).where(Booking.reference == job.related_appointment_id)
                    book_record = (await db.execute(b_q)).scalars().first()

            if not book_record and job.reason and job.reason.startswith("reminder:"):
                b_ref = job.reason.split(":", 1)[1]
                b_q = select(Booking).where(Booking.reference == b_ref)
                book_record = (await db.execute(b_q)).scalars().first()

            if apt_record:
                if apt_record.customer_phone:
                    phone = apt_record.customer_phone
                if apt_record.customer_name:
                    customer_name = apt_record.customer_name
                reminder_details = {
                    "entity": apt_record.practitioner_name or "our specialist",
                    "service": apt_record.service or "appointment",
                    "date": apt_record.date,
                    "time": apt_record.time,
                    "place": apt_record.notes or "our clinic",
                }
            elif book_record:
                reminder_details = {
                    "entity": book_record.service,
                    "service": book_record.service,
                    "date": book_record.start_at.strftime("%Y-%m-%d") if book_record.start_at else "scheduled date",
                    "time": book_record.start_at.strftime("%I:%M %p") if book_record.start_at else "scheduled time",
                    "place": book_record.notes or "our clinic",
                }

            try:
                await place_outbound_call(
                    phone=phone,
                    job_or_call_id=job.id,
                    call_reason=job.reason,
                    business_profile_id=job.business_profile_id,
                    customer_name=customer_name,
                    reminder_details=reminder_details,
                )
                job.status = "done"

                # Mark reminder_status = "called" and reminder_sent = True to prevent duplicate calls
                if apt_record:
                    apt_record.reminder_sent = True
                    apt_record.reminder_status = "called"
                if book_record:
                    book_record.reminder_status = "called"

                processed_count += 1
                logger.info(f"[SCHEDULER] Outbound reminder call dispatched successfully for Job {job.id}")
            except Exception as exc:
                job.status = "failed"
                if apt_record:
                    apt_record.reminder_status = "failed"
                if book_record:
                    book_record.reminder_status = "failed"
                logger.error(f"[SCHEDULER] Outbound reminder call failed for Job {job.id}: {exc}")

        if processed_count > 0:
            await db.commit()

    return processed_count


def start_scheduler():
    """Start APScheduler jobs."""
    if scheduler and not scheduler.running:
        scheduler.add_job(
            check_upcoming_reminders,
            "interval",
            minutes=2,
            id="check_upcoming_reminders",
            replace_existing=True,
        )
        scheduler.add_job(
            process_pending_call_jobs,
            "interval",
            minutes=1,
            id="process_pending_call_jobs",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("[SCHEDULER] APScheduler started for reminders and outbound calls.")
    elif scheduler is None:
        logger.info("[SCHEDULER] APScheduler not installed; background jobs disabled.")


def stop_scheduler():
    """Stop APScheduler."""
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] APScheduler stopped.")
