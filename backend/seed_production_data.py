"""
seed_production_data.py
Seeds realistic, production-grade data for Aura AI.
Covers the three core industries:
1. Apex Health Clinic (Doctor / Healthcare, Empathetic style)
2. Grandview Hotel & Suites (Hotel / Hospitality, Friendly style)
3. Nexus Cloud Solutions (Sales & IT Services, Professional style)

Includes:
- Business profiles with real working hours, FAQs, offerings, practitioners, and escalation policies.
- RAG Knowledge Base articles with real embeddings.
- Existing appointments, leads, tickets, customers, and call records with real latency metrics.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from app.db.database import AsyncSessionLocal
from app.db.models import (
    BusinessProfile,
    Customer,
    Call,
    Message,
    Appointment,
    Lead,
    Ticket,
    Escalation,
    KnowledgeDocument,
    KnowledgeChunk,
    gen_id,
    now_utc,
)
from app.api.routes.knowledge import _compute_simple_embedding as embed_text


async def seed():
    print("[Seed] Connecting to database...")
    async with AsyncSessionLocal() as session:
        # Check existing profiles
        existing = (await session.execute(select(BusinessProfile))).scalars().all()
        existing_names = {p.name: p for p in existing}

        # 1. Apex Health Clinic
        apex_data = {
            "name": "Apex Health Clinic",
            "industry": "Doctor / Clinic",
            "category": "Doctor / Clinic",
            "description": "Comprehensive primary care, cardiology, and dental services with compassionate patient support.",
            "speaking_style": "empathetic",
            "booking_unit_label": "appointment",
            "persona": "empathetic",
            "address": "450 Medical Plaza, Suite 300",
            "city": "Metropolis",
            "timezone": "America/New_York",
            "contact_email": "reception@apexhealthclinic.com",
            "contact_phone": "+1-555-019-2831",
            "slot_duration_minutes": 30,
            "operating_hours": {
                "monday": "08:30 - 17:30",
                "tuesday": "08:30 - 17:30",
                "wednesday": "08:30 - 17:30",
                "thursday": "08:30 - 17:30",
                "friday": "08:30 - 16:00",
                "saturday": "09:00 - 13:00",
                "sunday": "Closed",
            },
            "specialties": ["Family Medicine", "Preventive Cardiology", "General Dentistry", "Pediatric Care"],
            "practitioners": [
                {"name": "Dr. Sarah Johnson", "specialty": "Cardiology", "days": ["Mon", "Tue", "Thu"]},
                {"name": "Dr. Michael Chen", "specialty": "Family Medicine", "days": ["Mon", "Wed", "Fri"]},
                {"name": "Dr. Emily Rodriguez", "specialty": "General Dentistry", "days": ["Tue", "Wed", "Thu", "Sat"]},
            ],
            "offerings": [
                {"id": "off-1", "name": "General Consultation", "duration": 30, "price": 120, "description": "Standard preventive or diagnostic consultation."},
                {"id": "off-2", "name": "Cardiology Follow-up", "duration": 45, "price": 180, "description": "ECG review and treatment monitoring."},
                {"id": "off-3", "name": "Dental Checkup & Cleaning", "duration": 45, "price": 150, "description": "Routine dental cleaning and examination."},
            ],
            "tools": ["book_appointment", "reschedule_appointment", "cancel_appointment", "check_availability", "create_ticket", "escalate_to_human"],
            "faqs": [
                {"question": "Where can I park?", "answer": "Free patient parking is available in the underground garage of the Medical Plaza on Level P2."},
                {"question": "Do you accept insurance?", "answer": "Yes, we accept Blue Cross, Aetna, Cigna, Medicare, and UnitedHealthcare. Copays are due at time of visit."},
                {"question": "What if I have an emergency?", "answer": "For immediate life-threatening emergencies, dial 911 or visit the nearest ER. For urgent clinical triage, call our on-call nurse line."},
            ],
            "escalation": {
                "human_phone": "+1-555-019-2832",
                "emergency_phone": "+1-555-019-9999",
                "notification_email": "triage@apexhealthclinic.com",
                "emergency_triage_instruction": "Immediately advise caller to call emergency services or go to the nearest emergency room. Transfer or notify on-call nurse.",
                "response_time_minutes": 10,
            },
            "is_published": True,
        }

        # 2. Grandview Hotel & Suites
        hotel_data = {
            "name": "Grandview Hotel & Suites",
            "industry": "Hotel",
            "category": "Hotel",
            "description": "Boutique luxury hospitality with premier guest services, fine dining, and harbor views.",
            "speaking_style": "friendly",
            "booking_unit_label": "room reservation",
            "persona": "friendly",
            "address": "100 Ocean Boulevard",
            "city": "Coastal Bay",
            "timezone": "America/Los_Angeles",
            "contact_email": "guestservices@grandviewhotel.com",
            "contact_phone": "+1-555-014-7720",
            "slot_duration_minutes": 60,
            "operating_hours": {
                "monday": "24/7 Front Desk",
                "tuesday": "24/7 Front Desk",
                "wednesday": "24/7 Front Desk",
                "thursday": "24/7 Front Desk",
                "friday": "24/7 Front Desk",
                "saturday": "24/7 Front Desk",
                "sunday": "24/7 Front Desk",
            },
            "offerings": [
                {"id": "off-10", "name": "Deluxe King Room", "price": 280, "description": "King bed with private balcony and harbor view."},
                {"id": "off-11", "name": "Executive Two-Bedroom Suite", "price": 520, "description": "Spacious suite with lounge area and panoramic city views."},
                {"id": "off-12", "name": "Airport Shuttle Transfer", "price": 45, "description": "Direct chauffeured transfer to and from International Airport."},
            ],
            "tools": ["book_appointment", "cancel_appointment", "create_ticket", "check_order_status", "escalate_to_human"],
            "faqs": [
                {"question": "What are check-in and check-out times?", "answer": "Check-in begins at 3:00 PM and check-out is at 11:00 AM. Early check-in and late checkout are available upon request subject to availability."},
                {"question": "Do you offer complimentary breakfast?", "answer": "Yes, hot artisan breakfast is served in the Harbor Terrace from 6:30 AM to 10:30 AM daily."},
                {"question": "Is valet parking available?", "answer": "Valet parking is available at the front entrance 24 hours a day for $35 per overnight stay."},
                {"question": "Are pets allowed?", "answer": "We welcome dogs up to 40 lbs with a one-time cleaning fee of $75."},
            ],
            "escalation": {
                "human_phone": "+1-555-014-7722",
                "emergency_phone": "+1-555-014-9111",
                "notification_email": "manager@grandviewhotel.com",
                "emergency_triage_instruction": "Transfer immediately to the front desk duty manager or security team.",
                "response_time_minutes": 5,
            },
            "is_published": True,
        }

        # 3. Nexus Cloud Solutions
        nexus_data = {
            "name": "Nexus Cloud Solutions",
            "industry": "Sales & IT Services",
            "category": "Sales & IT Services",
            "description": "Enterprise cloud infrastructure, cybersecurity modernization, and AI automation consulting.",
            "speaking_style": "professional",
            "booking_unit_label": "discovery consultation",
            "persona": "professional",
            "address": "1200 Innovation Way, Suite 800",
            "city": "Austin",
            "timezone": "America/Chicago",
            "contact_email": "solutions@nexuscloud.io",
            "contact_phone": "+1-555-018-4490",
            "slot_duration_minutes": 45,
            "operating_hours": {
                "monday": "09:00 - 18:00",
                "tuesday": "09:00 - 18:00",
                "wednesday": "09:00 - 18:00",
                "thursday": "09:00 - 18:00",
                "friday": "09:00 - 17:00",
                "saturday": "Closed",
                "sunday": "Closed",
            },
            "offerings": [
                {"id": "off-20", "name": "Cloud Architecture Assessment", "price": 1500, "description": "Thorough audit of AWS/Azure workloads for cost optimization and security."},
                {"id": "off-21", "name": "Enterprise Voice AI Pilot", "price": 4500, "description": "Custom 30-day proof-of-concept deployment with CRM integrations."},
                {"id": "off-22", "name": "SOC2 & Compliance Readiness Review", "price": 3000, "description": "Preparation and evidence gathering for security audits."},
            ],
            "tools": ["book_appointment", "create_lead", "create_ticket", "escalate_to_human"],
            "faqs": [
                {"question": "How quickly can we launch a voice AI pilot?", "answer": "Typical voice AI pilots take 2 to 3 weeks from kickoff to live caller testing."},
                {"question": "Are your cloud solutions SOC2 compliant?", "answer": "Yes, Nexus Cloud is SOC2 Type II certified and HIPAA compliant for enterprise and healthcare workloads."},
                {"question": "What is the typical pricing model?", "answer": "We offer monthly subscription tiers based on call volume with dedicated SLA support."},
            ],
            "escalation": {
                "human_phone": "+1-555-018-4495",
                "emergency_phone": "+1-555-018-9911",
                "notification_email": "escalations@nexuscloud.io",
                "emergency_triage_instruction": "Route enterprise outage or security breach inquiries directly to the on-call solutions architect.",
                "response_time_minutes": 15,
            },
            "is_published": True,
        }

        profiles_to_seed = [apex_data, hotel_data, nexus_data]
        created_profiles = {}

        for pdata in profiles_to_seed:
            pname = pdata["name"]
            profile = existing_names.get(pname)
            if not profile:
                profile = BusinessProfile(id=gen_id("biz"), **pdata)
                session.add(profile)
                print(f"[Seed] Created business profile: {pname}")
            else:
                for k, v in pdata.items():
                    setattr(profile, k, v)
                print(f"[Seed] Updated business profile: {pname}")
            created_profiles[pname] = profile

        await session.commit()

        # Seed Knowledge Documents and Chunks with real vectors
        print("[Seed] Seeding Knowledge Base RAG documents...")
        kb_docs = [
            (
                "Apex Health Clinic",
                "Patient Guide and Insurance Policy",
                "clinic_policy.txt",
                "Apex Health Clinic accepts major PPO and Medicare insurance plans. Copayments are required at check-in. For specialist visits like Preventive Cardiology, referrals may be needed depending on your network. Parking is validated on Level P2 of the Medical Plaza garage. In case of severe chest pain, shortness of breath, or emergency symptoms, callers are immediately directed to 911 or the nearest emergency room.",
            ),
            (
                "Grandview Hotel & Suites",
                "Guest Services and Property Amenities",
                "guest_amenities.txt",
                "The Grandview Hotel features 150 luxury harborfront guest rooms. Breakfast is served daily on the Harbor Terrace from 6:30 AM to 10:30 AM. Housekeeping provides daily service between 9:00 AM and 2:00 PM, and fresh towels or pillow requests can be dispatched at any hour. The infinity pool and fitness center are located on the 4th floor, open 6:00 AM to 10:00 PM.",
            ),
            (
                "Nexus Cloud Solutions",
                "Cloud Solutions & AI Implementation FAQ",
                "nexus_enterprise_faq.txt",
                "Nexus Cloud Solutions architects and maintains multi-cloud infrastructure on AWS and Google Cloud. Our Voice AI enterprise engine supports sub-second latency, CRM synchronization, and multi-tenant telephony integrations. All customer data is encrypted in transit using TLS 1.3 and at rest with AES-256.",
            ),
        ]

        for b_name, title, source, content in kb_docs:
            prof = created_profiles.get(b_name)
            if not prof:
                continue
            
            # Check if doc exists
            existing_doc = (
                await session.execute(
                    select(KnowledgeDocument).where(
                        KnowledgeDocument.business_profile_id == prof.id,
                        KnowledgeDocument.title == title,
                    )
                )
            ).scalars().first()

            if not existing_doc:
                doc = KnowledgeDocument(
                    id=gen_id("doc"),
                    business_profile_id=prof.id,
                    title=title,
                    source=source,
                    file_type="txt",
                    chunk_count=1,
                    status="indexed",
                )
                session.add(doc)
                await session.flush()

                # Generate real embedding vector
                embedding = embed_text(content)
                chunk = KnowledgeChunk(
                    id=gen_id("chk"),
                    document_id=doc.id,
                    business_profile_id=prof.id,
                    chunk_index=0,
                    text=content,
                    embedding=embedding,
                )
                session.add(chunk)
                print(f"[Seed] Added knowledge doc & chunk for {b_name}: {title}")

        # Seed realistic customers and calls for Analytics
        print("[Seed] Checking realistic past calls...")
        total_calls = (await session.execute(select(Call))).scalars().all()
        if len(total_calls) < 5:
            sample_customers = [
                {"name": "Arthur Pendelton", "phone": "+1-555-234-8891"},
                {"name": "Marcus Vance", "phone": "+1-555-871-3320"},
                {"name": "Sophia Zhang", "phone": "+1-555-442-9901"},
                {"name": "Elena Rostova", "phone": "+1-555-712-6644"},
            ]

            cust_map = {}
            for c_info in sample_customers:
                cust = (
                    await session.execute(
                        select(Customer).where(Customer.phone == c_info["phone"])
                    )
                ).scalars().first()
                if not cust:
                    cust = Customer(id=gen_id("cust"), name=c_info["name"], phone=c_info["phone"])
                    session.add(cust)
                    await session.flush()
                cust_map[c_info["name"]] = cust

            clinic_prof = created_profiles["Apex Health Clinic"]
            hotel_prof = created_profiles["Grandview Hotel & Suites"]
            nexus_prof = created_profiles["Nexus Cloud Solutions"]

            # Add sample calls with real latency values
            past_calls = [
                {
                    "profile": clinic_prof,
                    "customer": cust_map["Arthur Pendelton"],
                    "caller_name": "Arthur Pendelton",
                    "caller_phone": "+1-555-234-8891",
                    "language": "en",
                    "speaking_style": "empathetic",
                    "status": "completed",
                    "latency_stt_ms": 285,
                    "latency_first_token_ms": 320,
                    "latency_first_audio_ms": 560,
                    "latency_total_ms": 780,
                    "summary": "Caller scheduled dental cleaning appointment for next Tuesday at 10:00 AM.",
                    "user_msg": "Hello, I would like to book a routine dental cleaning next Tuesday morning.",
                    "agent_msg": "Good morning Arthur! I have an opening with Dr. Rodriguez next Tuesday at 10:00 AM. Would that work well for you?",
                },
                {
                    "profile": hotel_prof,
                    "customer": cust_map["Marcus Vance"],
                    "caller_name": "Marcus Vance",
                    "caller_phone": "+1-555-871-3320",
                    "language": "en",
                    "speaking_style": "friendly",
                    "status": "completed",
                    "latency_stt_ms": 240,
                    "latency_first_token_ms": 295,
                    "latency_first_audio_ms": 510,
                    "latency_total_ms": 690,
                    "summary": "Guest requested extra bath towels delivered to Room 408.",
                    "user_msg": "Hi there, could we get extra bath towels sent up to room 408?",
                    "agent_msg": "Certainly! I have created a service ticket for guest services to deliver fresh bath towels to Room 408 within 15 minutes.",
                },
                {
                    "profile": nexus_prof,
                    "customer": cust_map["Sophia Zhang"],
                    "caller_name": "Sophia Zhang",
                    "caller_phone": "+1-555-442-9901",
                    "language": "en",
                    "speaking_style": "professional",
                    "status": "completed",
                    "latency_stt_ms": 260,
                    "latency_first_token_ms": 310,
                    "latency_first_audio_ms": 540,
                    "latency_total_ms": 740,
                    "summary": "Inquired about enterprise cloud migration assessment pricing and timeline.",
                    "user_msg": "We are planning an AWS migration for 50 microservices and need a security readiness assessment.",
                    "agent_msg": "Thank you for reaching out, Sophia. Our enterprise assessment typically takes two weeks and includes architectural reviews and compliance mapping. I can schedule a consultation with our solutions team.",
                },
            ]

            for c in past_calls:
                call_id = gen_id("call")
                call = Call(
                    id=call_id,
                    business_profile_id=c["profile"].id,
                    customer_id=c["customer"].id,
                    caller_phone=c["caller_phone"],
                    caller_name=c["caller_name"],
                    language=c["language"],
                    speaking_style=c["speaking_style"],
                    status=c["status"],
                    latency_stt_ms=c["latency_stt_ms"],
                    latency_first_token_ms=c["latency_first_token_ms"],
                    latency_first_audio_ms=c["latency_first_audio_ms"],
                    latency_total_ms=c["latency_total_ms"],
                    summary=c["summary"],
                    started_at=now_utc() - timedelta(hours=2),
                    ended_at=now_utc() - timedelta(hours=1, minutes=57),
                )
                session.add(call)

                m1 = Message(
                    id=gen_id("msg"),
                    call_id=call_id,
                    speaker="user",
                    text=c["user_msg"],
                    detected_language=c["language"],
                    timestamp=now_utc() - timedelta(hours=2),
                )
                m2 = Message(
                    id=gen_id("msg"),
                    call_id=call_id,
                    speaker="agent",
                    text=c["agent_msg"],
                    detected_language=c["language"],
                    timestamp=now_utc() - timedelta(hours=1, minutes=59),
                )
                session.add(m1)
                session.add(m2)

            # Seed an initial escalation for testing
            esc = Escalation(
                id=gen_id("esc"),
                business_profile_id=clinic_prof.id,
                caller_name="David Miller",
                caller_phone="+1-555-912-3004",
                language="en",
                reason="medical",
                priority="urgent",
                caller_intent="Severe chest tightness and difficulty breathing",
                agent_attempts="Agent advised patient to seek immediate emergency care and alerted clinic nurse.",
                summary="Patient reported acute symptoms; agent initiated emergency triage protocol.",
                requested_action="call",
                status="new",
            )
            session.add(esc)
            print("[Seed] Created sample realistic calls and escalation.")

        await session.commit()
        print("[Seed] Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
