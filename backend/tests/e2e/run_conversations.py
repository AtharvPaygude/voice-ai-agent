"""
Aura AI End-to-End Conversation Test Harness
Usage: cd C:\DEMO\backend && python tests/e2e/run_conversations.py
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import websockets
from sqlalchemy import text
from app.db.database import AsyncSessionLocal as SessionLocal

WS_URL = "ws://localhost:8000/ws/voice"

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭ SKIP"


class CallSession:
    def __init__(self, call_id: str, business_id: str, language: str = "en"):
        self.call_id = call_id
        self.business_id = business_id
        self.language = language
        self.messages = []
        self.tool_calls = []
        self.escalations = []

    async def run(self, turns: List[str], ws) -> Dict[str, Any]:
        """Run a conversation and collect all events."""
        # Send start_call
        await ws.send(json.dumps({
            "type": "start_call",
            "business_id": self.business_id,
            "language": self.language,
            "phone": "+919876543210",
            "name": "Test Caller",
            "send_audio": False
        }))
        
        # Wait for greeting
        await self._collect_until_idle(ws, timeout=10)
        
        # Process each turn
        for user_text in turns:
            await ws.send(json.dumps({
                "type": "text_input",
                "text": user_text,
                "language": self.language
            }))
            await self._collect_until_idle(ws, timeout=20)
        
        # End call
        await ws.send(json.dumps({"type": "end_call"}))
        return {
            "messages": self.messages,
            "tool_calls": self.tool_calls,
            "escalations": self.escalations
        }

    async def _collect_until_idle(self, ws, timeout=15):
        """Collect events until state=idle or timeout."""
        try:
            async with asyncio.timeout(timeout):
                while True:
                    raw = await ws.recv()
                    if isinstance(raw, bytes):
                        continue
                    evt = json.loads(raw)
                    t = evt.get("type")
                    if t == "response" or t == "response_sentence":
                        self.messages.append(evt.get("text", ""))
                    elif t == "tool_call":
                        self.tool_calls.append(evt)
                    elif t == "escalation_alert":
                        self.escalations.append(evt)
                    elif t == "state_change" and evt.get("state") == "idle":
                        break
        except (asyncio.TimeoutError, Exception):
            pass


async def get_business_ids():
    """Get business IDs from DB."""
    async with SessionLocal() as db:
        result = await db.execute(text("SELECT id, name, industry, category FROM business_profiles"))
        rows = result.fetchall()
        biz_map = {}
        for r in rows:
            name = (r[1] or "").lower()
            if "clinic" in name or "sunrise" in name:
                biz_map["clinic_doctor"] = r[0]
            elif "hotel" in name or "universal" in name:
                biz_map["hotel"] = r[0]
            elif "brightpath" in name or "service" in name:
                biz_map["service_business"] = r[0]
        return biz_map


async def run_scenario(name: str, business_type: str, turns: List[str], biz_map: dict, language="en",
                       expect_no_escalation=True) -> str:
    biz_id = biz_map.get(business_type)
    if not biz_id:
        print(f"  {SKIP}: {name} — no {business_type} business found")
        return "skip"

    call_id = f"test-{int(datetime.utcnow().timestamp())}"
    session = CallSession(call_id, biz_id, language)

    try:
        async with websockets.connect(f"{WS_URL}/{call_id}", ping_interval=None) as ws:
            result = await session.run(turns, ws)

        # Check for escalation
        if expect_no_escalation and session.escalations:
            print(f"  {FAIL}: {name} — unexpected escalation: {session.escalations[0].get('reason')}")
            return "fail"

        all_replies = " ".join(session.messages).lower()
        # Check no internal text leaked
        if any(x in all_replies for x in ["tool_call", ":::tool", "json", "execute_tool"]):
            print(f"  {FAIL}: {name} — internal text leaked in reply")
            return "fail"

        print(f"  {PASS}: {name}")
        if session.tool_calls:
            print(f"    Tools called: {[t['tool'] for t in session.tool_calls]}")
        return "pass"

    except Exception as e:
        print(f"  {FAIL}: {name} — exception: {e}")
        return "fail"


async def main():
    print("=" * 60)
    print("Aura AI E2E Test Suite")
    print("=" * 60)
    print()

    # Get business IDs
    biz_map = await get_business_ids()
    print(f"Business profiles found: {biz_map}")
    print()

    today = datetime.now()
    d20 = (today.replace(day=20) if today.day < 20 else (today + timedelta(days=10)).replace(day=20)).strftime("%B %dth")

    results = []

    scenarios = [
        # English - Hotel
        ("EN-1 Hotel room booking", "hotel",
         [f"I want to book a Deluxe room for 2 guests from the 20th to the 23rd", "Yes, please confirm it"], "en", True),
        
        # English - Clinic
        ("EN-2 Clinic appointment", "clinic_doctor",
         ["I want to book an appointment with the cardiologist for tomorrow"], "en", True),

        # English - Sales
        ("EN-3 Sales price inquiry", "service_business",
         ["What is the price of the Pro plan?", "Tell me more about what's included"], "en", True),

        # English - Order tracking
        ("EN-4 Order tracking", "service_business",
         ["I want to track my order", "Order number is ORD-12345"], "en", True),

        # Hindi - Clinic
        ("HI-1 Clinic in Hindi", "clinic_doctor",
         ["मुझे कल सुबह त्वचा रोग विशेषज्ञ से मिलना है"], "hi", True),

        # Hindi - Hotel
        ("HI-2 Hotel in Hinglish", "hotel",
         ["Mujhe do raat ke liye family room chahiye"], "hi", True),

        # Marathi - Clinic
        ("MR-1 Clinic in Marathi", "clinic_doctor",
         ["मला शनिवारी दंतचिकित्सकाकडे जायचे आहे"], "mr", True),

        # Escalation should happen
        ("ESC-1 Requested escalation", "hotel",
         ["I want to talk to a real person"], "en", False),  # expect_no_escalation=False

        # Escalation should NOT happen - 5 normal turns
        ("ESC-2 No escalation on normal turns", "hotel",
         ["What are your check-in timings?", "Do you have a pool?", "What is the room price?",
          "Tell me about breakfast options", "Thank you"], "en", True),

        # Medical advice - no escalation
        ("MED-1 Medical advice refusal", "clinic_doctor",
         ["Which tablet should I take for fever?"], "en", True),
    ]

    for name, biz_type, turns, lang, no_esc in scenarios:
        status = await run_scenario(name, biz_type, turns, biz_map, lang, no_esc)
        results.append((name, status))

    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, s in results if s == "pass")
    failed = sum(1 for _, s in results if s == "fail")
    skipped = sum(1 for _, s in results if s == "skip")
    for name, status in results:
        icon = PASS if status == "pass" else (FAIL if status == "fail" else SKIP)
        print(f"  {icon} {name}")
    print()
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print()
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed — check backend logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
