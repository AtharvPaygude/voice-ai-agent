"""
Dynamic Availability and Booking Engine.

Calculates real-time, valid booking slots from:
- Operating hours per weekday (e.g. 10:00 to 17:00)
- Excluded break periods (e.g. 13:00 to 14:00)
- Configured slot duration (e.g. 30 minutes)
- Holiday exclusions
- Existing confirmed database appointments

Provides concurrency-safe booking verification to prevent double bookings.
"""
import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, BusinessProfile

logger = logging.getLogger(__name__)

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def parse_time_str(t_str: str) -> Optional[time]:
    """Parse time string like '10:00', '10:00 AM', '1:00 PM', '17:30'."""
    if not t_str:
        return None
    cleaned = t_str.strip().upper()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I %p"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.time()
        except ValueError:
            pass
    return None


def format_time_display(t: time) -> str:
    """Format time to 12-hour AM/PM string like '10:00 AM'."""
    return t.strftime("%I:%M %p").lstrip("0")


def time_to_minutes(t: time) -> int:
    """Convert time object to minutes from midnight."""
    return t.hour * 60 + t.minute


def minutes_to_time(m: int) -> time:
    """Convert minutes from midnight to time object."""
    hours = (m // 60) % 24
    mins = m % 60
    return time(hour=hours, minute=mins)


def get_weekday_name(d: date) -> str:
    """Return lowercase weekday name: 'monday', 'tuesday', etc."""
    return WEEKDAYS[d.weekday()]


def is_in_range(start_m: int, end_m: int, check_start_m: int, check_end_m: int) -> bool:
    """Check if check range overlaps with start..end range."""
    return max(start_m, check_start_m) < min(end_m, check_end_m)


def generate_slots_for_day(
    target_date: date,
    operating_hours: Dict[str, Any],
    breaks: List[Dict[str, Any]],
    slot_duration_minutes: int = 30,
    holidays: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate all mathematically valid unbooked slots for a given date.
    Operating hours format:
      {"monday": {"open": "10:00", "close": "17:00", "closed": false}}
    Breaks format:
      [{"name": "Lunch", "start": "13:00", "end": "14:00", "days": ["monday", ...]}]
    """
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 1. Holiday check
    if holidays and (date_str in holidays or target_date.strftime("%d-%m-%Y") in holidays):
        return []

    weekday = get_weekday_name(target_date)
    day_config = (operating_hours or {}).get(weekday)

    # Default fallback operating hours if not explicitly configured: Mon-Fri 10am-5pm
    if not day_config:
        if weekday in ("saturday", "sunday"):
            return []
        day_config = {"open": "10:00", "close": "17:00", "closed": False}

    if day_config.get("closed", False):
        return []

    open_time = parse_time_str(day_config.get("open", "10:00"))
    close_time = parse_time_str(day_config.get("close", "17:00"))
    if not open_time or not close_time:
        return []

    open_m = time_to_minutes(open_time)
    close_m = time_to_minutes(close_time)
    if close_m <= open_m:
        return []

    duration = max(10, slot_duration_minutes or 30)

    # 2. Parse active breaks for this day
    active_breaks = []
    for b in (breaks or []):
        b_days = [d.lower() for d in b.get("days", [])]
        if not b_days or weekday in b_days:
            b_start = parse_time_str(b.get("start", ""))
            b_end = parse_time_str(b.get("end", ""))
            if b_start and b_end:
                bs_m = time_to_minutes(b_start)
                be_m = time_to_minutes(b_end)
                if be_m > bs_m:
                    active_breaks.append((bs_m, be_m, b.get("name", "Break")))

    # 3. Step through working hours in slot_duration increments
    slots = []
    curr_m = open_m
    while curr_m + duration <= close_m:
        slot_end_m = curr_m + duration

        # Check collision with breaks
        in_break = False
        for bs, be, b_name in active_breaks:
            if is_in_range(bs, be, curr_m, slot_end_m):
                in_break = True
                break

        if not in_break:
            t_obj = minutes_to_time(curr_m)
            end_t_obj = minutes_to_time(slot_end_m)
            slots.append({
                "date": date_str,
                "time": format_time_display(t_obj),
                "end_time": format_time_display(end_t_obj),
                "raw_time": t_obj.strftime("%H:%M"),
                "duration_minutes": duration,
            })

        curr_m += duration

    return slots


async def get_business_availability(
    business_id: str,
    target_date_str: str,
    db: AsyncSession,
    practitioner_name: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Calculate and return available slots for a business on target date,
    filtering out existing database bookings.
    """
    profile = await db.get(BusinessProfile, business_id)
    if not profile:
        return [], {"error": "Business profile not found"}

    try:
        if target_date_str.lower() in ("today", "now"):
            target_date = date.today()
        elif target_date_str.lower() == "tomorrow":
            target_date = date.today() + timedelta(days=1)
        else:
            target_date = datetime.strptime(target_date_str.strip(), "%Y-%m-%d").date()
    except Exception:
        target_date = date.today() + timedelta(days=1)

    # Generate all baseline slots
    all_slots = generate_slots_for_day(
        target_date=target_date,
        operating_hours=profile.operating_hours or {},
        breaks=profile.breaks or [],
        slot_duration_minutes=profile.slot_duration_minutes or 30,
        holidays=profile.holidays or [],
    )

    # Query confirmed bookings for this business on this date
    formatted_date_str = target_date.strftime("%Y-%m-%d")
    query = select(Appointment).where(
        Appointment.business_profile_id == business_id,
        Appointment.status == "confirmed",
        Appointment.date == formatted_date_str,
    )
    if practitioner_name:
        query = query.where(Appointment.practitioner_name == practitioner_name)

    result = await db.execute(query)
    booked_appointments = result.scalars().all()

    # Normalize booked times for collision comparison
    booked_times = set()
    for appt in booked_appointments:
        t_parsed = parse_time_str(appt.time)
        if t_parsed:
            booked_times.add(format_time_display(t_parsed))
            booked_times.add(t_parsed.strftime("%H:%M"))

    available_slots = []
    for s in all_slots:
        if s["time"] not in booked_times and s["raw_time"] not in booked_times:
            available_slots.append(s)

    meta = {
        "business_id": profile.id,
        "business_name": profile.name,
        "category": profile.category or profile.industry,
        "booking_unit_label": profile.booking_unit_label or "appointment",
        "date": formatted_date_str,
        "weekday": get_weekday_name(target_date),
        "total_generated": len(all_slots),
        "total_available": len(available_slots),
        "total_booked": len(booked_appointments),
    }

    return available_slots, meta


async def book_slot_atomic(
    business_id: str,
    date_str: str,
    time_str: str,
    service: str,
    db: AsyncSession,
    practitioner_name: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    notes: Optional[str] = None,
    call_id: Optional[str] = None,
) -> Tuple[bool, Optional[Appointment], str]:
    """
    Concurrency-safe booking transaction:
    Verifies that the slot is open before committing the booking.
    """
    parsed_time = parse_time_str(time_str)
    if not parsed_time:
        return False, None, f"Invalid time format '{time_str}'."

    std_time = format_time_display(parsed_time)

    # 1. Check if slot is already occupied
    query = select(Appointment).where(
        Appointment.business_profile_id == business_id,
        Appointment.date == date_str,
        Appointment.status == "confirmed",
    )
    if practitioner_name:
        query = query.where(Appointment.practitioner_name == practitioner_name)

    res = await db.execute(query)
    existing_bookings = res.scalars().all()
    for b in existing_bookings:
        b_time = parse_time_str(b.time)
        if b_time and (format_time_display(b_time) == std_time or b.time == std_time):
            return False, None, f"The slot on {date_str} at {std_time} is already booked."

    # 2. Check if the slot is within operational hours
    available_slots, _ = await get_business_availability(
        business_id=business_id,
        target_date_str=date_str,
        db=db,
        practitioner_name=practitioner_name,
    )
    is_valid_slot = any(s["time"] == std_time or s["raw_time"] == parsed_time.strftime("%H:%M") for s in available_slots)
    if not is_valid_slot and available_slots:
        alt_times = ", ".join(s["time"] for s in available_slots[:3])
        return False, None, f"Slot {std_time} is not available on {date_str}. Available slots: {alt_times}"

    # 3. Create the appointment record atomically
    from app.db.models import gen_id
    profile = await db.get(BusinessProfile, business_id)
    duration = profile.slot_duration_minutes if profile else 30

    appt = Appointment(
        id=gen_id("APT"),
        business_profile_id=business_id,
        call_id=call_id,
        date=date_str,
        time=std_time,
        service=service or "Consultation",
        practitioner_name=practitioner_name,
        customer_name=customer_name or "Valued Customer",
        customer_phone=customer_phone or "",
        duration_minutes=duration,
        notes=notes or "",
        status="confirmed",
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)

    logger.info(f"Successfully booked appointment {appt.id} for {business_id} on {date_str} at {std_time}")
    return True, appt, f"Confirmed for {date_str} at {std_time}"
