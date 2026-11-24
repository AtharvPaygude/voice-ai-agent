"""
Business Profile CRUD API routes for Aura AI.
Allows creating, reading, updating, deleting, and activating business profiles
including speaking style, escalation settings, offerings, and FAQs.
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import BusinessProfile, gen_id

router = APIRouter()


class BusinessProfileCreate(BaseModel):
    name: str
    industry: str = "service_business"
    description: str = ""
    offerings: List[dict] = []
    capabilities: List[str] = []
    knowledge_base: List[str] = []
    tools: List[str] = []
    workflows: List[str] = []
    permissions: dict = {}
    policies: dict = {}
    booking_unit_label: str = "appointment"
    persona: str = "professional"
    speaking_style: str = "friendly"
    category: str = "service_business"
    address: str = ""
    city: str = ""
    timezone: str = "UTC"
    contact_email: str = ""
    contact_phone: str = ""
    operating_hours: dict = {}
    breaks: List[dict] = []
    slot_duration_minutes: int = 30
    specialties: List[str] = []
    practitioners: List[dict] = []
    inventory: List[dict] = []
    holidays: List[str] = []
    faqs: List[dict] = []
    escalation: dict = {}


class BusinessProfileUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    offerings: Optional[List[dict]] = None
    capabilities: Optional[List[str]] = None
    knowledge_base: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    workflows: Optional[List[str]] = None
    permissions: Optional[dict] = None
    policies: Optional[dict] = None
    booking_unit_label: Optional[str] = None
    persona: Optional[str] = None
    speaking_style: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    operating_hours: Optional[dict] = None
    breaks: Optional[List[dict]] = None
    slot_duration_minutes: Optional[int] = None
    specialties: Optional[List[str]] = None
    practitioners: Optional[List[dict]] = None
    inventory: Optional[List[dict]] = None
    holidays: Optional[List[str]] = None
    faqs: Optional[List[dict]] = None
    escalation: Optional[dict] = None


class BusinessProfileResponse(BaseModel):
    id: str
    name: str
    industry: str
    description: str
    offerings: List[Any]
    capabilities: List[str]
    knowledge_base: List[str]
    tools: List[str]
    workflows: List[str]
    permissions: dict
    policies: dict
    booking_unit_label: str
    persona: str
    speaking_style: str
    category: str
    address: str
    city: str
    timezone: str
    contact_email: str
    contact_phone: str
    operating_hours: dict
    breaks: List[Any]
    slot_duration_minutes: int
    specialties: List[str]
    practitioners: List[Any]
    inventory: List[Any]
    holidays: List[str]
    faqs: List[Any]
    escalation: dict
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[BusinessProfileResponse])
async def list_business_profiles(db: AsyncSession = Depends(get_db)):
    """List all business profiles."""
    result = await db.execute(select(BusinessProfile).order_by(BusinessProfile.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=BusinessProfileResponse, status_code=201)
async def create_business_profile(data: BusinessProfileCreate, db: AsyncSession = Depends(get_db)):
    """Create a new business profile."""
    profile = BusinessProfile(
        id=gen_id("biz"),
        name=data.name,
        industry=data.industry,
        description=data.description,
        offerings=data.offerings,
        capabilities=data.capabilities,
        knowledge_base=data.knowledge_base,
        tools=data.tools,
        workflows=data.workflows,
        permissions=data.permissions,
        policies=data.policies,
        booking_unit_label=data.booking_unit_label,
        persona=data.persona,
        speaking_style=data.speaking_style,
        category=data.category,
        address=data.address,
        city=data.city,
        timezone=data.timezone,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        operating_hours=data.operating_hours,
        breaks=data.breaks,
        slot_duration_minutes=data.slot_duration_minutes,
        specialties=data.specialties,
        practitioners=data.practitioners,
        inventory=data.inventory,
        holidays=data.holidays,
        faqs=data.faqs,
        escalation=data.escalation,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=BusinessProfileResponse)
async def get_business_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a single business profile."""
    profile = await db.get(BusinessProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    return profile


@router.put("/{profile_id}", response_model=BusinessProfileResponse)
async def update_business_profile(
    profile_id: str, data: BusinessProfileUpdate, db: AsyncSession = Depends(get_db)
):
    """Update business profile fields."""
    profile = await db.get(BusinessProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(profile, field, val)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
async def delete_business_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a business profile."""
    profile = await db.get(BusinessProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    await db.delete(profile)
    await db.commit()
    return {"status": "deleted", "id": profile_id}
