"""
Voice-Driven & Interactive Business Onboarding Engine.

Guides new business owners through a structured, conversational onboarding interview.
Collects common fields (name, category, location, operating schedule, breaks, slot duration)
plus industry-specific fields (Doctor specialty & fee, Hotel room inventory, Restaurant tables),
persists progress after every step, and allows review/publishing.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import BusinessProfile, User, gen_id
from app.api.routes.auth import get_current_user

router = APIRouter()


class OnboardingAnswerRequest(BaseModel):
    step: str
    field: str
    value: Any
    skip: bool = False


class OnboardingStepInfo(BaseModel):
    step_id: str
    title: str
    voice_prompt: str
    field_name: str
    input_type: str  # select, text, time_range, number, tags
    options: Optional[List[str]] = None
    is_optional: bool = False
    current_value: Any = None
    help_text: Optional[str] = None


class OnboardingSessionState(BaseModel):
    business_id: str
    business_name: Optional[str] = None
    category: str
    current_step: str
    current_step_info: OnboardingStepInfo
    progress_percentage: int
    answers: Dict[str, Any]
    status: str  # draft, in_progress, completed
    steps_completed: List[str]
    steps_pending: List[str]


# ─── Onboarding Flow Definition ───────────────────────────────────────────────

STEPS_COMMON = [
    {
        "step_id": "category",
        "title": "Business Category",
        "voice_prompt": "Welcome to AURA! I'll help you set up your business and configure your AI assistant. What type of business do you operate?",
        "field_name": "category",
        "input_type": "select",
        "options": ["Doctor / Clinic", "Hotel", "Restaurant", "Service Business", "Real Estate", "Education", "Other"],
        "is_optional": False,
        "help_text": "Select your industry to customize appointment types, schedule rules, and questions.",
    },
    {
        "step_id": "business_name",
        "title": "Business Name",
        "voice_prompt": "Great! What is the name of your business or clinic?",
        "field_name": "name",
        "input_type": "text",
        "is_optional": False,
        "help_text": "The public commercial name callers will hear from your AI agent.",
    },
    {
        "step_id": "location",
        "title": "Location & City",
        "voice_prompt": "Where is your business located? Please tell me your city and address.",
        "field_name": "location",
        "input_type": "text",
        "is_optional": False,
        "help_text": "City and physical address so nearby customers can find you.",
    },
    {
        "step_id": "operating_hours",
        "title": "Operating Hours & Days",
        "voice_prompt": "What are your business operating days and hours? For example, Monday to Friday from 10 AM to 5 PM.",
        "field_name": "operating_hours_text",
        "input_type": "text",
        "is_optional": False,
        "help_text": "Days of the week and daily opening/closing hours.",
    },
    {
        "step_id": "breaks",
        "title": "Daily Breaks",
        "voice_prompt": "Do you take any breaks during those hours, such as a lunch break from 1 PM to 2 PM?",
        "field_name": "breaks_text",
        "input_type": "text",
        "is_optional": True,
        "help_text": "Lunch or rest periods when customer appointments should not be scheduled.",
    },
    {
        "step_id": "slot_duration",
        "title": "Appointment Duration",
        "voice_prompt": "What is the standard duration of each appointment or session? For example, 30 minutes or 45 minutes.",
        "field_name": "slot_duration_minutes",
        "input_type": "number",
        "is_optional": False,
        "options": ["15", "30", "45", "60", "90"],
        "help_text": "Duration in minutes used by the engine to slice available booking slots.",
    },
]

# Industry-specific questions
INDUSTRY_STEPS = {
    "Doctor / Clinic": [
        {
            "step_id": "doctor_specialty",
            "title": "Medical Specialty & Doctor Name",
            "voice_prompt": "What type of doctor are you, and what is your medical specialty? For example, Dr. Sarah Jenkins, Cardiologist.",
            "field_name": "specialty_and_doctor",
            "input_type": "text",
            "is_optional": False,
            "help_text": "Doctor full name and primary specialty (e.g. Cardiologist, Dentist, General Physician).",
        },
        {
            "step_id": "consultation_details",
            "title": "Consultation Fee & Type",
            "voice_prompt": "What is your consultation fee, and do you offer in-person visits, online video consultations, or both?",
            "field_name": "consultation_details",
            "input_type": "text",
            "is_optional": True,
            "help_text": "Standard fee (e.g. ₹800) and whether visits are in-clinic or tele-consultation.",
        },
    ],
    "Hotel": [
        {
            "step_id": "room_types",
            "title": "Room Types & Nightly Rates",
            "voice_prompt": "What room types do you offer and what are their typical nightly rates? For example, Deluxe Room for ₹3500 and Suite for ₹6000.",
            "field_name": "room_types",
            "input_type": "text",
            "is_optional": False,
            "help_text": "Room categories, capacities, and base prices per night.",
        },
        {
            "step_id": "checkin_checkout",
            "title": "Check-in & Check-out Policy",
            "voice_prompt": "What are your standard check-in and check-out times?",
            "field_name": "checkin_checkout",
            "input_type": "text",
            "is_optional": True,
            "help_text": "e.g. Check-in 2:00 PM, Check-out 11:00 AM.",
        },
    ],
    "Restaurant": [
        {
            "step_id": "cuisine_menu",
            "title": "Cuisine & Specialties",
            "voice_prompt": "What type of cuisine does your restaurant serve, and what are your signature dishes?",
            "field_name": "cuisine_menu",
            "input_type": "text",
            "is_optional": False,
            "help_text": "Cuisine type (e.g. North Indian, Italian) and popular menu items.",
        },
        {
            "step_id": "reservation_capacity",
            "title": "Table Reservation Capacity",
            "voice_prompt": "What is your maximum party size for reservations, and do you require advance booking?",
            "field_name": "reservation_capacity",
            "input_type": "text",
            "is_optional": True,
            "help_text": "Table sizes, advance notice requirements, or cancellation policy.",
        },
    ],
    "Service Business": [
        {
            "step_id": "services_offerings",
            "title": "Services Offered & Pricing",
            "voice_prompt": "What specific services do you provide and what are their standard prices?",
            "field_name": "services_offerings",
            "input_type": "text",
            "is_optional": False,
            "help_text": "List of core services and pricing tiers.",
        },
    ],
}


def build_steps_for_profile(category: str) -> List[Dict[str, Any]]:
    """Assemble common steps + industry-specific steps + review step."""
    steps = [STEPS_COMMON[0]]  # category is always first
    # Add other common steps
    steps.extend(STEPS_COMMON[1:])
    # Add industry steps
    matched_industry = None
    for ind in INDUSTRY_STEPS:
        if ind.lower() in category.lower() or category.lower() in ind.lower():
            matched_industry = ind
            break
    if matched_industry:
        steps.extend(INDUSTRY_STEPS[matched_industry])

    # Final review step
    steps.append({
        "step_id": "review_publish",
        "title": "Review & Confirmation",
        "voice_prompt": "We've gathered all your business details. Please review your configuration and confirm to publish your AI assistant.",
        "field_name": "confirmed",
        "input_type": "confirm",
        "is_optional": False,
        "help_text": "Confirm all details to publish your live schedule and enable customer discovery.",
    })
    return steps


@router.get("/session", response_model=OnboardingSessionState)
async def get_or_create_onboarding_session(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the active onboarding session for the current business owner.
    If none exists, initializes a new draft profile.
    """
    profile = None
    if user.business_profile_id:
        profile = await db.get(BusinessProfile, user.business_profile_id)

    if not profile:
        # Create a new draft profile for this owner
        profile = BusinessProfile(
            id=gen_id("biz"),
            name="My New Business",
            industry="Doctor / Clinic",
            category="clinic_doctor",
            onboarding_status="draft",
            onboarding_step="category",
            onboarding_answers={},
            is_published=False,
            operating_hours={
                "monday": {"open": "10:00", "close": "17:00", "closed": False},
                "tuesday": {"open": "10:00", "close": "17:00", "closed": False},
                "wednesday": {"open": "10:00", "close": "17:00", "closed": False},
                "thursday": {"open": "10:00", "close": "17:00", "closed": False},
                "friday": {"open": "10:00", "close": "17:00", "closed": False},
                "saturday": {"open": "10:00", "close": "14:00", "closed": True},
                "sunday": {"open": "10:00", "close": "14:00", "closed": True},
            },
            breaks=[{"name": "Lunch Break", "start": "13:00", "end": "14:00", "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]}],
            slot_duration_minutes=30,
        )
        db.add(profile)
        user.business_profile_id = profile.id
        await db.commit()
        await db.refresh(profile)

    category = profile.industry or "Doctor / Clinic"
    all_steps = build_steps_for_profile(category)
    step_ids = [s["step_id"] for s in all_steps]

    curr_step_id = profile.onboarding_step or "category"
    if curr_step_id not in step_ids:
        curr_step_id = step_ids[0]

    # Find step index and calculate progress
    curr_idx = step_ids.index(curr_step_id)
    progress_pct = int((curr_idx / max(1, len(step_ids) - 1)) * 100)

    curr_step_def = all_steps[curr_idx]
    answers = profile.onboarding_answers or {}

    step_info = OnboardingStepInfo(
        step_id=curr_step_def["step_id"],
        title=curr_step_def["title"],
        voice_prompt=curr_step_def["voice_prompt"],
        field_name=curr_step_def["field_name"],
        input_type=curr_step_def["input_type"],
        options=curr_step_def.get("options"),
        is_optional=curr_step_def.get("is_optional", False),
        current_value=answers.get(curr_step_def["field_name"]),
        help_text=curr_step_def.get("help_text"),
    )

    return OnboardingSessionState(
        business_id=profile.id,
        business_name=profile.name,
        category=profile.industry,
        current_step=curr_step_id,
        current_step_info=step_info,
        progress_percentage=progress_pct,
        answers=answers,
        status=profile.onboarding_status,
        steps_completed=step_ids[:curr_idx],
        steps_pending=step_ids[curr_idx:],
    )


@router.post("/answer", response_model=OnboardingSessionState)
async def submit_onboarding_answer(
    req: OnboardingAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer for the current onboarding step (via voice transcript or typed form).
    Saves to the database, parses structured schedule/services, and advances to the next step.
    """
    if not user.business_profile_id:
        raise HTTPException(status_code=400, detail="No active business profile for this user.")

    profile = await db.get(BusinessProfile, user.business_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found.")

    answers = dict(profile.onboarding_answers or {})
    if not req.skip:
        answers[req.field] = req.value

    # Apply answer directly to the underlying database model
    val = req.value
    if req.step == "category" and val:
        profile.industry = str(val)
        if "clinic" in str(val).lower() or "doctor" in str(val).lower():
            profile.category = "clinic_doctor"
            profile.booking_unit_label = "appointment"
        elif "hotel" in str(val).lower():
            profile.category = "hotel"
            profile.booking_unit_label = "room"
        elif "restaurant" in str(val).lower():
            profile.category = "restaurant"
            profile.booking_unit_label = "table reservation"
        else:
            profile.category = "service_business"
            profile.booking_unit_label = "slot"

    elif req.step == "business_name" and val:
        profile.name = str(val).strip()

    elif req.step == "location" and val:
        loc_str = str(val).strip()
        profile.address = loc_str
        if "," in loc_str:
            profile.city = loc_str.split(",")[-1].strip()
        else:
            profile.city = loc_str

    elif req.step == "slot_duration" and val:
        try:
            profile.slot_duration_minutes = int(str(val).split()[0])
        except Exception:
            profile.slot_duration_minutes = 30

    elif req.step == "doctor_specialty" and val:
        text_val = str(val)
        # Parse specialty (e.g. Cardiologist)
        specialties = []
        for s in ["Cardiologist", "Dentist", "Physician", "Pediatrician", "Dermatologist", "Orthopedic", "Surgeon"]:
            if s.lower() in text_val.lower():
                specialties.append(s)
        if not specialties:
            specialties = [text_val.split(",")[-1].strip()]
        profile.specialties = specialties
        profile.practitioners = [{
            "id": "doc-1",
            "name": text_val.split(",")[0].strip() if "," in text_val else "Dr. In-Charge",
            "specialty": specialties[0],
            "consultation_type": "in-person and online",
            "fee": "Standard",
        }]

    elif req.step == "services_offerings" and val:
        profile.offerings = [{"name": str(val).strip(), "price": "Standard Pricing"}]

    elif req.step == "room_types" and val:
        profile.inventory = [{"type": str(val).strip(), "capacity": 2, "price": "Standard Rate"}]

    profile.onboarding_answers = answers

    # Determine next step
    all_steps = build_steps_for_profile(profile.industry or "Doctor / Clinic")
    step_ids = [s["step_id"] for s in all_steps]

    curr_idx = step_ids.index(req.step) if req.step in step_ids else 0
    next_idx = min(len(step_ids) - 1, curr_idx + 1)
    next_step_id = step_ids[next_idx]

    profile.onboarding_step = next_step_id
    profile.onboarding_status = "in_progress"
    await db.commit()
    await db.refresh(profile)

    return await get_or_create_onboarding_session(user, db)


@router.post("/publish")
async def finalize_and_publish_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm and publish the business profile.
    Sets is_published = True and makes the business live for real customer discovery.
    """
    if not user.business_profile_id:
        raise HTTPException(status_code=400, detail="No business profile linked to user.")

    profile = await db.get(BusinessProfile, user.business_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found.")

    profile.onboarding_status = "completed"
    profile.onboarding_step = "done"
    profile.is_published = True
    await db.commit()
    await db.refresh(profile)

    # Sync into runtime config
    from app.api.routes.business import activate_business_profile
    await activate_business_profile(profile.id, db)

    return {
        "status": "published",
        "business_id": profile.id,
        "business_name": profile.name,
        "category": profile.category,
        "is_published": profile.is_published,
        "message": f"'{profile.name}' is now live and published on AURA!",
    }
