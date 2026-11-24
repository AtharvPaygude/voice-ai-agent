# Aura AI — Changelog

## [2.1.0] — 2026-11-16 (Master Prompt 2 Resolution)

### Fixed
- **Escalation Loop Root Cause**:
  - `_safe_fallback()` in `app/core/llm_client.py` was previously hardcoded to return an escalation apology text ("I apologize, I am temporarily having trouble reaching our automated systems...").
  - `gemini-2.5-flash` model returned 404 from Google AI Studio.
  - Switched `LLM_PRIMARY` to `"ollama"` (`llama3.2:3b`), which responds in ~800ms locally without network dropouts.
  - Rewrote `_safe_fallback()` to return helpful assistance and execute deterministic slot/tool actions rather than triggering escalation text.
  - Added turn count guard (`GRACE_TURNS = 2`): the agent never leaves `normal` mode in the first two turns unless explicitly requested or during a medical emergency.
  - Added `settings.ESCALATION_ENABLED` kill-switch.
  - Added reset of failure counters upon every successful turn or tool action.
  - Added `/api/debug/calls/{call_id}/trace` endpoint for per-turn debug tracking.
- **Supabase Connection Pooling**:
  - Added `pool_pre_ping=True` and `pool_recycle=300` in `app/db/database.py` to prevent stale socket disconnections with Supabase Session Pooler.
- **edge-tts 403 & Windows Audio Locking**:
  - Upgraded `edge-tts` to 7.3.1.
  - Fixed Windows temp file locking in `app/core/stt.py` (`delete=False` with explicit close and unlinking).
  - Fixed `send_audio=True` for text inputs so that the AI voice plays reliably.

### Added
- **Production Database Architecture**:
  - Expanded `app/db/models.py` with full tables: `Resource`, `ResourceSchedule`, `ResourceTimeOff`, `Booking`, `RoomType`, `Room`, `Reservation`, `Facility`, `Offering`, `Order`, `FAQ`, `ToolAuditLog`, `Outbox`.
  - Added conflict-safe reference code generators (`APT-XXXXX`, `RSV-XXXXX`, `ORD-XXXXXX`, `TCK-XXXXX`, `LED-XXXXX`, `ESC-XXXXX`).
  - Added idempotent database seeder `app/db/seed.py` supporting `--reset`.
  - Successfully seeded 243 real production records across 3 business profiles:
    1. **Sunrise Multispecialty Clinic, Pune** (6 doctors, Mon-Sat schedules, 20 bookings, FAQs).
    2. **Universal Hotel & Suites, Pune** (4 room types, 40 rooms, 20 reservations, facilities, FAQs).
    3. **BrightPath Services** (8 offerings, 20 orders with tracking numbers, FAQs).
- **Records Dashboard API**:
  - Created `app/api/routes/records.py` with endpoints for `/api/records/bookings`, `/api/records/reservations`, `/api/records/orders`, `/api/records/leads`, `/api/records/tickets`, `/api/records/escalations`, `/api/records/outbox`, and `/api/records/overview`.
- **Real Database Tool Execution**:
  - Re-implemented `app/api/routes/tools.py` to query and mutate real database tables with transaction-level double-booking protection and persistent audit logging in `tool_audit_logs`.
- **E2E Test Harness**:
  - Added `tests/e2e/run_conversations.py` validating hotel bookings, clinic appointments, orders, multilingual queries, and escalation rules.
