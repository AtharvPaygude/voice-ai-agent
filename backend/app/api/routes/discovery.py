"""
Customer Discovery API Routes.

Queries real registered, active, and published business profiles from the database.
Supports category discovery (doctors/clinics, hotels, restaurants, services),
keyword search across specialties/practitioners/offerings, and location filtering.
"""
from datetime import date, timedelta
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import BusinessProfile
from app.core.availability import get_business_availability

router = APIRouter()


class ProviderResult(BaseModel):
    id: str
    name: str
    category: str
    industry: str
    description: str
    address: str
    city: str
    booking_unit_label: str
    specialties: List[str]
    practitioners: List[Dict[str, Any]]
    offerings: List[Dict[str, Any]]
    sample_available_slots: List[str] = []
    earliest_available_date: Optional[str] = None


class DiscoverySearchResponse(BaseModel):
    query: str
    category: Optional[str] = None
    location: Optional[str] = None
    total_found: int
    providers: List[ProviderResult]
    message: str


CATEGORY_SYNONYMS = {
    "doctor": "clinic_doctor",
    "clinic": "clinic_doctor",
    "hospital": "clinic_doctor",
    "physician": "clinic_doctor",
    "cardiologist": "clinic_doctor",
    "dentist": "clinic_doctor",
    "hotel": "hotel",
    "resort": "hotel",
    "stay": "hotel",
    "room": "hotel",
    "restaurant": "restaurant",
    "cafe": "restaurant",
    "dining": "restaurant",
    "food": "restaurant",
    "service": "service_business",
    "consultant": "service_business",
}


def normalize_category(cat: Optional[str]) -> Optional[str]:
    """Map user-spoken category terms to internal category keys."""
    if not cat:
        return None
    c_lower = cat.strip().lower()
    for key, val in CATEGORY_SYNONYMS.items():
        if key in c_lower:
            return val
    return c_lower


@router.get("/search", response_model=DiscoverySearchResponse)
async def search_providers(
    q: Optional[str] = Query(None, description="Search term (e.g. cardiologist, deluxe room, pizza)"),
    category: Optional[str] = Query(None, description="Category filter (clinic_doctor, hotel, restaurant)"),
    location: Optional[str] = Query(None, description="City or address filter"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search real providers stored in the database.
    Never returns mock or fake data.
    """
    normalized_cat = normalize_category(category)
    query_str = (q or "").strip()
    loc_str = (location or "").strip()

    stmt = select(BusinessProfile).where(BusinessProfile.is_published == True)

    if normalized_cat:
        stmt = stmt.where(
            or_(
                BusinessProfile.category.ilike(f"%{normalized_cat}%"),
                BusinessProfile.industry.ilike(f"%{normalized_cat}%"),
            )
        )

    if loc_str:
        stmt = stmt.where(
            or_(
                BusinessProfile.city.ilike(f"%{loc_str}%"),
                BusinessProfile.address.ilike(f"%{loc_str}%"),
            )
        )

    result = await db.execute(stmt)
    profiles = result.scalars().all()

    # If query string is given, filter matching profiles by specialty, practitioner, offering, name, or desc
    matching_providers = []
    tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    for p in profiles:
        match = True
        if query_str:
            q_lower = query_str.lower()
            text_haystack = " ".join([
                p.name or "",
                p.description or "",
                p.industry or "",
                p.category or "",
                p.city or "",
                p.address or "",
                str(p.specialties or []),
                str(p.practitioners or []),
                str(p.offerings or []),
            ]).lower()
            if q_lower not in text_haystack:
                match = False

        if match:
            # Query real available slots for tomorrow
            slots, _ = await get_business_availability(p.id, tomorrow_str, db)
            sample_slots = [s["time"] for s in slots[:4]]
            earliest_date = tomorrow_str if slots else None

            matching_providers.append(ProviderResult(
                id=p.id,
                name=p.name,
                category=p.category or p.industry,
                industry=p.industry,
                description=p.description or "",
                address=p.address or "",
                city=p.city or "",
                booking_unit_label=p.booking_unit_label or "slot",
                specialties=p.specialties or [],
                practitioners=p.practitioners or [],
                offerings=p.offerings or [],
                sample_available_slots=sample_slots,
                earliest_available_date=earliest_date,
            ))

    total = len(matching_providers)
    if total > 0:
        msg = f"Found {total} matching registered provider(s)."
    else:
        msg = "No registered providers found matching that criteria."

    return DiscoverySearchResponse(
        query=query_str,
        category=normalized_cat,
        location=loc_str,
        total_found=total,
        providers=matching_providers,
        message=msg,
    )


@router.get("/categories")
async def list_available_categories(db: AsyncSession = Depends(get_db)):
    """List all categories that have at least one registered and published business."""
    stmt = select(BusinessProfile.category, BusinessProfile.industry).where(BusinessProfile.is_published == True)
    res = await db.execute(stmt)
    rows = res.fetchall()
    cats = sorted(list({r[0] or r[1] for r in rows if (r[0] or r[1])}))
    return {"categories": cats}
