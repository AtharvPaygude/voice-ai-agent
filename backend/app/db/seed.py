"""
Seed script for Aura AI database.
Usage:
    python -m app.db.seed           # idempotent: skip existing businesses
    python -m app.db.seed --reset   # delete all seeded rows first, then re-seed
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone, timedelta

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal as async_session_maker, engine, Base
from app.db.models import (
    BusinessProfile, Customer, Resource, ResourceSchedule, ResourceTimeOff,
    Booking, RoomType, Room, Reservation, Facility, Offering, Order,
    FAQ, ToolAuditLog, Outbox, gen_id, gen_ref
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc).replace(tzinfo=None)


COUNTERS: dict[str, int] = {}


def inc(table: str, n: int = 1):
    COUNTERS[table] = COUNTERS.get(table, 0) + n


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

SEEDED_TABLES = [
    "messages",
    "call_jobs",
    "appointments",
    "leads",
    "tickets",
    "escalations",
    "reservations",
    "bookings",
    "calls",
    "customers",
    "rooms",
    "room_types",
    "resource_time_offs",
    "resource_schedules",
    "resources",
    "orders",
    "offerings",
    "facilities",
    "faqs",
    "tool_audit_logs",
    "outbox",
]


async def reset_all(session: AsyncSession):
    print("⚠️  Resetting seeded tables …")
    for tbl in SEEDED_TABLES:
        await session.execute(text(f"DELETE FROM {tbl}"))
    # Also delete business profiles created by seed (identified by name)
    for name in ["Sunrise Clinic", "Universal Hotel", "BrightPath Services"]:
        await session.execute(
            text("DELETE FROM business_profiles WHERE name = :n"), {"n": name}
        )
    await session.commit()
    print("   Done.\n")


# ---------------------------------------------------------------------------
# Business Profiles
# ---------------------------------------------------------------------------

BUSINESS_DEFS = [
    {
        "name": "Sunrise Clinic",
        "industry": "healthcare",
        "category": "clinic",
        "description": "Multi-specialty outpatient clinic in Pune offering affordable, quality care.",
        "address": "12, FC Road, Shivajinagar",
        "city": "Pune",
        "timezone": "Asia/Kolkata",
        "contact_email": "care@sunriseclinic.in",
        "contact_phone": "+912025671234",
        "booking_unit_label": "appointment",
        "persona": "empathetic",
        "speaking_style": "friendly",
    },
    {
        "name": "Universal Hotel",
        "industry": "hospitality",
        "category": "hotel",
        "description": "4-star business hotel in Pune city centre with 160 rooms and world-class amenities.",
        "address": "1, Bund Garden Road, Yerwada",
        "city": "Pune",
        "timezone": "Asia/Kolkata",
        "contact_email": "reservations@universalhotel.in",
        "contact_phone": "+912026781234",
        "booking_unit_label": "reservation",
        "persona": "professional",
        "speaking_style": "professional",
    },
    {
        "name": "BrightPath Services",
        "industry": "consulting",
        "category": "service_business",
        "description": "IT consulting and managed services provider based in Pune Hinjewadi tech park.",
        "address": "Block B, Phase 1, Hinjewadi IT Park",
        "city": "Pune",
        "timezone": "Asia/Kolkata",
        "contact_email": "hello@brightpath.in",
        "contact_phone": "+912022341234",
        "booking_unit_label": "appointment",
        "persona": "professional",
        "speaking_style": "professional",
    },
]


async def upsert_businesses(session: AsyncSession) -> dict[str, str]:
    """Return map of business name -> id, creating if absent."""
    biz_ids: dict[str, str] = {}
    for defn in BUSINESS_DEFS:
        result = await session.execute(
            select(BusinessProfile).where(BusinessProfile.name == defn["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            biz_ids[defn["name"]] = existing.id
            print(f"   Business '{defn['name']}' already exists – skipping.")
        else:
            bp = BusinessProfile(**defn)
            session.add(bp)
            await session.flush()
            biz_ids[defn["name"]] = bp.id
            inc("business_profiles")
            print(f"   Created business '{defn['name']}' → {bp.id}")
    await session.commit()
    return biz_ids


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

INDIAN_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohit Desai", "Sneha Kulkarni", "Amit Joshi",
    "Meera Nair", "Vikram Singh", "Pooja Mehta", "Rajesh Gupta", "Anjali Verma",
    "Suresh Iyer", "Kavitha Reddy", "Nitin Borse", "Swati Deshpande", "Kiran More",
    "Deepak Pawar", "Lata Bhosale", "Mahesh Yadav", "Rekha Chavan", "Sanjay Patil",
    "Alka Thakur", "Ravi Kumar", "Sunita Jagtap", "Nilesh Jadhav", "Pallavi Gaikwad",
    "Tushar Mane", "Ashwini Shinde", "Girish Thorat", "Nandini Kadam", "Prakash Waghmare",
    "Vidya Salvi", "Hemant Autade", "Bhavana Narkar", "Sachin Kale", "Manisha Tambe",
    "Yashwant Gavhane", "Ujwala Ghuge", "Dattatray Doke", "Shital Mulik", "Omkar Pawar",
    "Rahul Shirke", "Preethi Shetty", "Ganesh Bhoir", "Archana Surve", "Vinod Sawant",
    "Madhuri Jadhav", "Datta Mhatre", "Rutuja Khot", "Sandip Gawde", "Charu Naik",
    "Tejas Kolhe", "Shreya Bhatt", "Siddhesh Khandare", "Shraddha Dongre", "Nikhil More",
    "Divya Raut", "Parag Kamble", "Yogesh Ghosalkar", "Ranjana Pingle", "Abhijit Khade",
]

PHONE_BASE = 9000000000


def make_customers(biz_id: str, biz_index: int, count: int = 20) -> list[Customer]:
    customers = []
    for i in range(count):
        name = INDIAN_NAMES[(biz_index * 20 + i) % len(INDIAN_NAMES)]
        phone = f"+91{PHONE_BASE + biz_index * 100 + i}"
        c = Customer(
            id=gen_id("cust"),
            phone=phone,
            name=name,
            business_profile_id=biz_id,
        )
        customers.append(c)
    return customers


# ---------------------------------------------------------------------------
# Resources (doctors for clinic)
# ---------------------------------------------------------------------------

DOCTORS = [
    {"name": "Dr. Arvind Kulkarni", "specialty": "General Physician", "fee": 500, "languages": ["en", "mr", "hi"]},
    {"name": "Dr. Sunita Pawar",    "specialty": "Gynaecology",        "fee": 700, "languages": ["en", "mr"]},
    {"name": "Dr. Nikhil Desai",    "specialty": "Orthopaedics",       "fee": 800, "languages": ["en", "hi"]},
    {"name": "Dr. Priya Joshi",     "specialty": "Paediatrics",        "fee": 600, "languages": ["en", "mr", "hi"]},
    {"name": "Dr. Ramesh Shah",     "specialty": "Cardiology",         "fee": 1200, "languages": ["en", "hi"]},
    {"name": "Dr. Meena Iyer",      "specialty": "Dermatology",        "fee": 700, "languages": ["en", "mr"]},
]

WEEKDAYS = list(range(6))  # 0-5 Mon-Sat


def make_resources(clinic_id: str) -> list:
    resources = []
    schedules = []
    for doc in DOCTORS:
        r = Resource(
            id=gen_id("res"),
            business_profile_id=clinic_id,
            kind="doctor",
            name=doc["name"],
            specialty=doc["specialty"],
            fee=doc["fee"],
            languages=doc["languages"],
            slot_minutes=30,
            active=True,
        )
        resources.append(r)
        for wd in WEEKDAYS:
            s = ResourceSchedule(
                id=gen_id("rsch"),
                resource_id=r.id,
                weekday=wd,
                start_time="09:00",
                end_time="18:00",
                break_start="13:00",
                break_end="14:00",
            )
            schedules.append(s)
    return resources, schedules


# ---------------------------------------------------------------------------
# Room Types + Rooms for hotel
# ---------------------------------------------------------------------------

ROOM_TYPE_DEFS = [
    {"name": "Standard", "description": "Comfortable room with city view, queen bed.", "base_price": 3500, "max_guests": 2,
     "amenities": ["WiFi", "AC", "TV", "Tea/Coffee maker"], "inventory_count": 60},
    {"name": "Deluxe",   "description": "Spacious room with garden view, king bed.", "base_price": 5500, "max_guests": 2,
     "amenities": ["WiFi", "AC", "TV", "Mini-bar", "Tea/Coffee maker", "Safe"], "inventory_count": 50},
    {"name": "Executive Suite", "description": "Luxury suite with separate sitting area and panoramic views.", "base_price": 9000, "max_guests": 3,
     "amenities": ["WiFi", "AC", "TV", "Mini-bar", "Jacuzzi", "Safe", "Butler service"], "inventory_count": 30},
    {"name": "Family Room", "description": "Large interconnected room perfect for families.", "base_price": 7000, "max_guests": 4,
     "amenities": ["WiFi", "AC", "TV", "Mini-bar", "Extra beds", "Child amenities"], "inventory_count": 20},
]


def make_room_types_and_rooms(hotel_id: str) -> tuple:
    room_types = []
    rooms = []
    for idx, rtd in enumerate(ROOM_TYPE_DEFS):
        rt = RoomType(
            id=gen_id("rtyp"),
            business_profile_id=hotel_id,
            **rtd,
        )
        room_types.append(rt)
        count = rtd["inventory_count"] // rtd["inventory_count"] * 10  # 10 rooms per type for seed
        for r_num in range(1, 11):
            floor = idx + 1
            number = f"{floor}{r_num:02d}"
            room = Room(
                id=gen_id("room"),
                room_type_id=rt.id,
                number=number,
                floor=floor,
                status="available",
            )
            rooms.append(room)
    return room_types, rooms


# ---------------------------------------------------------------------------
# Facilities for hotel
# ---------------------------------------------------------------------------

FACILITY_DEFS = [
    {"name": "Rooftop Swimming Pool", "description": "Heated outdoor pool open year-round.", "opening_time": "06:00", "closing_time": "22:00", "location": "Rooftop, Level 10"},
    {"name": "Lotus Spa & Wellness", "description": "Full-service spa with Ayurvedic and western treatments.", "opening_time": "09:00", "closing_time": "21:00", "location": "Level 1, East Wing"},
    {"name": "FitZone Gymnasium", "description": "State-of-the-art gym with personal trainers.", "opening_time": "05:30", "closing_time": "23:00", "location": "Level 2"},
    {"name": "Spice Garden Restaurant", "description": "Multi-cuisine restaurant serving breakfast, lunch and dinner.", "opening_time": "07:00", "closing_time": "23:00", "location": "Level 1, Lobby"},
    {"name": "The Atrium Bar & Lounge", "description": "Premium cocktail bar with live music on weekends.", "opening_time": "17:00", "closing_time": "01:00", "location": "Level 1, West Wing"},
    {"name": "Business Centre", "description": "Co-working space with printing, conference rooms and high-speed WiFi.", "opening_time": "07:00", "closing_time": "22:00", "location": "Level 2, North Wing"},
]


def make_facilities(hotel_id: str) -> list:
    return [
        Facility(id=gen_id("fac"), business_profile_id=hotel_id, **fd)
        for fd in FACILITY_DEFS
    ]


# ---------------------------------------------------------------------------
# Offerings for BrightPath
# ---------------------------------------------------------------------------

OFFERING_DEFS = [
    {"category": "subscription", "name": "Starter Cloud Plan", "description": "Managed cloud hosting for small teams. Includes 2 vCPU, 4 GB RAM, 50 GB SSD.", "price": 4999, "billing_period": "monthly", "features": ["2 vCPU", "4 GB RAM", "50 GB SSD", "99.5% SLA", "Email support"]},
    {"category": "subscription", "name": "Business Cloud Plan", "description": "Managed cloud hosting for growing teams. Includes 8 vCPU, 16 GB RAM, 500 GB SSD.", "price": 14999, "billing_period": "monthly", "features": ["8 vCPU", "16 GB RAM", "500 GB SSD", "99.9% SLA", "24/7 phone support", "Daily backups"]},
    {"category": "subscription", "name": "Enterprise Cloud Plan", "description": "Dedicated infrastructure with SLA guarantee.", "price": 49999, "billing_period": "monthly", "features": ["32 vCPU", "64 GB RAM", "2 TB SSD", "99.99% SLA", "Dedicated account manager", "Hourly backups", "Disaster recovery"]},
    {"category": "service", "name": "IT Infrastructure Audit", "description": "Full audit of your IT setup with detailed report and remediation roadmap.", "price": 29999, "billing_period": "one-time", "features": ["On-site visit", "Security assessment", "Network topology review", "Written report", "30-day follow-up"]},
    {"category": "service", "name": "Cybersecurity Assessment", "description": "Penetration testing and vulnerability assessment.", "price": 49999, "billing_period": "one-time", "features": ["VAPT", "OWASP Top 10", "Compliance check", "Executive summary", "Technical report"]},
    {"category": "service", "name": "Cloud Migration Package", "description": "End-to-end migration of on-premise workloads to cloud.", "price": 99999, "billing_period": "one-time", "features": ["Discovery", "Architecture design", "Migration execution", "Testing", "90-day hypercare"]},
    {"category": "subscription", "name": "Managed IT Support", "description": "Round-the-clock helpdesk and proactive monitoring.", "price": 9999, "billing_period": "monthly", "features": ["24/7 helpdesk", "RMM monitoring", "Patch management", "Monthly reports"]},
    {"category": "service", "name": "ERP Implementation", "description": "End-to-end implementation of SAP / Oracle / Zoho ERP.", "price": 299999, "billing_period": "one-time", "features": ["Requirements analysis", "Configuration", "Data migration", "Training", "1-year support"]},
]


def make_offerings(biz_id: str) -> list:
    return [
        Offering(id=gen_id("off"), business_profile_id=biz_id, **od)
        for od in OFFERING_DEFS
    ]


# ---------------------------------------------------------------------------
# FAQs
# ---------------------------------------------------------------------------

CLINIC_FAQS = [
    {"language": "en", "category": "booking", "question": "How do I book an appointment?", "answer": "Call us at +912025671234 or ask our AI assistant to book one for you anytime."},
    {"language": "en", "category": "general", "question": "What are your clinic timings?", "answer": "We are open Monday to Saturday, 9 AM to 6 PM."},
    {"language": "en", "category": "billing", "question": "Do you accept insurance?", "answer": "Yes, we accept most major health insurance plans including Star Health, HDFC Ergo, and Medi Assist."},
    {"language": "hi", "category": "booking", "question": "अपॉइंटमेंट कैसे बुक करें?", "answer": "आप हमें +912025671234 पर कॉल कर सकते हैं या हमारे AI असिस्टेंट से बुकिंग करवा सकते हैं।"},
    {"language": "hi", "category": "general", "question": "क्लिनिक का समय क्या है?", "answer": "हम सोमवार से शनिवार, सुबह 9 बजे से शाम 6 बजे तक खुले हैं।"},
    {"language": "mr", "category": "booking", "question": "अपॉइंटमेंट कशी बुक करायची?", "answer": "तुम्ही +912025671234 वर फोन करू शकता किंवा आमच्या AI सहाय्यकाकडून बुकिंग करवू शकता."},
    {"language": "mr", "category": "general", "question": "क्लिनिकचे वेळापत्रक काय आहे?", "answer": "आम्ही सोमवार ते शनिवार, सकाळी 9 ते संध्याकाळी 6 पर्यंत उघडे असतो."},
]

HOTEL_FAQS = [
    {"language": "en", "category": "checkin", "question": "What is the check-in and check-out time?", "answer": "Check-in is from 2 PM and check-out is by 12 noon. Early check-in and late check-out subject to availability."},
    {"language": "en", "category": "booking", "question": "How do I modify or cancel my reservation?", "answer": "Call us at +912026781234 or use the AI assistant. Free cancellation up to 48 hours before check-in."},
    {"language": "en", "category": "amenities", "question": "Is breakfast included?", "answer": "Breakfast is included for Deluxe and Executive Suite bookings. Standard room guests may add it at ₹699 per person."},
    {"language": "hi", "category": "checkin", "question": "चेक-इन और चेक-आउट का समय क्या है?", "answer": "चेक-इन दोपहर 2 बजे से और चेक-आउट दोपहर 12 बजे तक है।"},
    {"language": "hi", "category": "amenities", "question": "क्या पार्किंग उपलब्ध है?", "answer": "हाँ, हमारे पास 200 गाड़ियों की क्षमता वाली अंडरग्राउंड पार्किंग है, जो ₹200 प्रति दिन के हिसाब से उपलब्ध है।"},
    {"language": "mr", "category": "checkin", "question": "चेक-इन आणि चेक-आउटची वेळ काय आहे?", "answer": "चेक-इन दुपारी 2 वाजल्यापासून आणि चेक-आउट दुपारी 12 वाजेपर्यंत आहे."},
    {"language": "mr", "category": "booking", "question": "रिझर्वेशन कसे करायचे?", "answer": "+912026781234 वर फोन करा किंवा AI सहाय्यक वापरा."},
]

BRIGHTPATH_FAQS = [
    {"language": "en", "category": "services", "question": "What services does BrightPath offer?", "answer": "We offer cloud hosting, IT audits, cybersecurity assessments, cloud migration, managed IT support, and ERP implementation."},
    {"language": "en", "category": "billing", "question": "What payment methods do you accept?", "answer": "We accept bank transfers, UPI, credit/debit cards, and corporate purchase orders."},
    {"language": "en", "category": "support", "question": "What is your support SLA?", "answer": "Our managed support plans guarantee response within 1 hour for critical issues, 4 hours for major, and 8 hours for minor."},
    {"language": "hi", "category": "services", "question": "BrightPath क्या सेवाएं प्रदान करता है?", "answer": "हम क्लाउड होस्टिंग, IT ऑडिट, साइबर सुरक्षा, क्लाउड माइग्रेशन और ERP कार्यान्वयन प्रदान करते हैं।"},
    {"language": "mr", "category": "services", "question": "BrightPath कोणत्या सेवा देते?", "answer": "आम्ही क्लाउड होस्टिंग, IT ऑडिट, सायबर सुरक्षा, क्लाउड माइग्रेशन आणि ERP अंमलबजावणी सेवा देतो."},
]

BIZ_FAQS = {
    "Sunrise Clinic": CLINIC_FAQS,
    "Universal Hotel": HOTEL_FAQS,
    "BrightPath Services": BRIGHTPATH_FAQS,
}


def make_faqs(biz_id: str, biz_name: str) -> list:
    faqs_data = BIZ_FAQS.get(biz_name, [])
    return [
        FAQ(id=gen_id("faq"), business_profile_id=biz_id, **fd)
        for fd in faqs_data
    ]


# ---------------------------------------------------------------------------
# Bookings (for clinic)
# ---------------------------------------------------------------------------

SERVICES = ["General Consultation", "Follow-up Visit", "Blood Test Referral", "ECG", "Physiotherapy"]
BOOKING_STATUSES = ["confirmed", "completed", "completed", "no_show", "cancelled"]


def make_bookings(clinic_id: str, customers: list, resources: list) -> list:
    bookings = []
    base_date = datetime(2026, 11, 1, 10, 0)
    for i in range(20):
        cust = customers[i % len(customers)]
        res = resources[i % len(resources)]
        start = base_date + timedelta(days=i, hours=(i % 8))
        end = start + timedelta(minutes=30)
        b = Booking(
            id=gen_id("book"),
            reference=gen_ref("APT"),
            business_profile_id=clinic_id,
            resource_id=res.id,
            customer_id=cust.id,
            service=SERVICES[i % len(SERVICES)],
            reason="Routine check-up",
            start_at=start,
            end_at=end,
            status=BOOKING_STATUSES[i % len(BOOKING_STATUSES)],
            reminder_enabled=True,
            reminder_offsets=["24h", "1h"],
            notes="",
        )
        bookings.append(b)
    return bookings


# ---------------------------------------------------------------------------
# Reservations (for hotel)
# ---------------------------------------------------------------------------

RES_STATUSES = ["confirmed", "confirmed", "completed", "cancelled", "pending"]


def make_reservations(hotel_id: str, customers: list, room_types: list, rooms: list) -> list:
    reservations = []
    base_date = datetime(2026, 11, 10)
    for i in range(20):
        cust = customers[i % len(customers)]
        rt = room_types[i % len(room_types)]
        room = rooms[i % len(rooms)]
        check_in = (base_date + timedelta(days=i * 2)).strftime("%Y-%m-%d")
        check_out = (base_date + timedelta(days=i * 2 + 2 + (i % 3))).strftime("%Y-%m-%d")
        nights = 2 + (i % 3)
        total = rt.base_price * nights
        rsv = Reservation(
            id=gen_id("rsrv"),
            reference=gen_ref("RSV"),
            business_profile_id=hotel_id,
            customer_id=cust.id,
            room_type_id=rt.id,
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=1 + (i % rt.max_guests),
            special_requests="Late check-in" if i % 5 == 0 else "",
            status=RES_STATUSES[i % len(RES_STATUSES)],
            total_price=total,
            cancellation_policy="Free cancellation up to 48 hours before check-in",
        )
        reservations.append(rsv)
    return reservations


# ---------------------------------------------------------------------------
# Orders (for BrightPath)
# ---------------------------------------------------------------------------

ORDER_STATUSES = ["placed", "confirmed", "shipped", "delivered", "cancelled"]
CARRIERS = ["BlueDart", "FedEx", "DTDC", "Delhivery", "India Post"]


def make_orders(biz_id: str, customers: list) -> list:
    orders = []
    for i in range(20):
        cust = customers[i % len(customers)]
        o = Order(
            id=gen_id("ord"),
            order_number=gen_ref("ORD"),
            business_profile_id=biz_id,
            customer_id=cust.id,
            status=ORDER_STATUSES[i % len(ORDER_STATUSES)],
            total=4999 * (1 + i % 5),
            tracking_id=f"TRK{100000 + i}",
            carrier=CARRIERS[i % len(CARRIERS)],
            eta=(datetime(2026, 11, 20) + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
        )
        orders.append(o)
    return orders


# ---------------------------------------------------------------------------
# Main seed
# ---------------------------------------------------------------------------

async def seed():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete seeded rows before seeding")
    args = parser.parse_args()

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        if args.reset:
            await reset_all(session)

        print("🌱 Seeding business profiles …")
        biz_ids = await upsert_businesses(session)

        clinic_id = biz_ids["Sunrise Clinic"]
        hotel_id = biz_ids["Universal Hotel"]
        brightpath_id = biz_ids["BrightPath Services"]

        # --- Customers ---
        print("👤 Seeding customers …")
        clinic_customers = make_customers(clinic_id, 0)
        hotel_customers = make_customers(hotel_id, 1)
        bp_customers = make_customers(brightpath_id, 2)

        all_customers = clinic_customers + hotel_customers + bp_customers
        for c in all_customers:
            session.add(c)
        await session.flush()
        inc("customers", len(all_customers))
        print(f"   {len(all_customers)} customers added.")

        # --- Resources (Clinic doctors) ---
        print("🩺 Seeding clinic resources & schedules …")
        resources, schedules = make_resources(clinic_id)
        for r in resources:
            session.add(r)
        await session.flush()
        for s in schedules:
            session.add(s)
        await session.flush()
        inc("resources", len(resources))
        inc("resource_schedules", len(schedules))
        print(f"   {len(resources)} doctors, {len(schedules)} schedule rows.")

        # ResourceTimeOff for first doctor
        rto = ResourceTimeOff(
            id=gen_id("rto"),
            resource_id=resources[0].id,
            start_at=datetime(2026, 12, 25, 0, 0),
            end_at=datetime(2026, 12, 26, 0, 0),
            reason="Christmas Leave",
        )
        session.add(rto)
        await session.flush()
        inc("resource_time_offs")

        # --- Room Types + Rooms ---
        print("🏨 Seeding hotel room types and rooms …")
        room_types, rooms = make_room_types_and_rooms(hotel_id)
        for rt in room_types:
            session.add(rt)
        await session.flush()
        for rm in rooms:
            session.add(rm)
        await session.flush()
        inc("room_types", len(room_types))
        inc("rooms", len(rooms))
        print(f"   {len(room_types)} room types, {len(rooms)} rooms.")

        # --- Facilities ---
        print("🏊 Seeding hotel facilities …")
        facilities = make_facilities(hotel_id)
        for f in facilities:
            session.add(f)
        await session.flush()
        inc("facilities", len(facilities))
        print(f"   {len(facilities)} facilities.")

        # --- Offerings ---
        print("📦 Seeding BrightPath offerings …")
        offerings = make_offerings(brightpath_id)
        for o in offerings:
            session.add(o)
        await session.flush()
        inc("offerings", len(offerings))
        print(f"   {len(offerings)} offerings.")

        # --- Bookings ---
        print("📅 Seeding clinic bookings …")
        bookings = make_bookings(clinic_id, clinic_customers, resources)
        for b in bookings:
            session.add(b)
        await session.flush()
        inc("bookings", len(bookings))
        print(f"   {len(bookings)} bookings.")

        # --- Reservations ---
        print("🛎️  Seeding hotel reservations …")
        reservations = make_reservations(hotel_id, hotel_customers, room_types, rooms)
        for r in reservations:
            session.add(r)
        await session.flush()
        inc("reservations", len(reservations))
        print(f"   {len(reservations)} reservations.")

        # --- Orders ---
        print("📦 Seeding BrightPath orders …")
        orders = make_orders(brightpath_id, bp_customers)
        for o in orders:
            session.add(o)
        await session.flush()
        inc("orders", len(orders))
        print(f"   {len(orders)} orders.")

        # --- FAQs ---
        print("❓ Seeding FAQs …")
        all_faqs = []
        for biz_name, biz_id in biz_ids.items():
            faqs = make_faqs(biz_id, biz_name)
            all_faqs.extend(faqs)
            for faq in faqs:
                session.add(faq)
        await session.flush()
        inc("faqs", len(all_faqs))
        print(f"   {len(all_faqs)} FAQs.")

        await session.commit()

    print("\n✅ Seed complete! Row counts per table:")
    for table, count in sorted(COUNTERS.items()):
        print(f"   {table:<30} {count:>5}")
    total = sum(COUNTERS.values())
    print(f"   {'TOTAL':<30} {total:>5}")


if __name__ == "__main__":
    asyncio.run(seed())
