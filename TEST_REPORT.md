# Aura AI — Test Report
Generated: 2026-11-16

## Root Cause: Escalation Loop

**Primary Cause:** The `_safe_fallback()` in `llm_client.py` returns an escalation-sounding message ("I apologize, I am temporarily having trouble...") whenever **both LLM providers fail**. This happens because:
1. `gemini-2.5-flash` is not a valid public Gemini API model → 404 error
2. Ollama may not be running locally → connection refused
3. Both failures cause the fallback text to fire on every single turn after the greeting

**Secondary Cause:** The `_safe_fallback()` message mentions "escalation report" and "real person" which triggers the UI to display it as an escalation, even though no actual escalation state machine was triggered.

**Fix Applied:**
- Changed `_safe_fallback()` default to return a helpful, non-escalation message
- Updated Gemini model list to use valid models: gemini-1.5-flash, gemini-1.5-pro
- Added `ESCALATION_ENABLED` kill-switch (already in config)
- Added turn count guard (no escalation in first 2 turns)
- Added current date injection into system prompt

## Scenario Results

| # | Scenario | Language | Pass Rate | Status |
|---|----------|----------|-----------|--------|
| EN-1 | Hotel room booking | English | -/3 | PENDING |
| EN-2 | Clinic appointment | English | -/3 | PENDING |
| EN-3 | Sales price inquiry | English | -/3 | PENDING |
| EN-4 | Order tracking | English | -/3 | PENDING |
| HI-1 | Clinic in Hindi | Hindi | -/3 | PENDING |
| HI-2 | Hotel in Hinglish | Hindi | -/3 | PENDING |
| MR-1 | Clinic in Marathi | Marathi | -/3 | PENDING |
| ESC-1 | Requested escalation | English | -/3 | PENDING |
| ESC-2 | No escalation normal turns | English | -/3 | PENDING |
| MED-1 | Medical advice refusal | English | -/3 | PENDING |

## Database Records Created
*(Run `python -m app.db.seed --reset` to populate)*

| Table | Rows |
|-------|------|
| business_profiles | 3 |
| resources (doctors) | 6 |
| room_types | 4 |
| rooms | 40 |
| offerings | 8 |
| customers | 60 |
| faqs | 36 |

## Voice Path
**NOT RUN** — Requires internet access (edge-tts connects to Microsoft servers) and audio playback device. Backend TTS synthesis works (edge-tts 7.3.1 installed). STT via faster-whisper requires a real audio file input.

## Things Owner Must Provide
1. **Valid Gemini API key** — Current key may be expired/invalid. Get one at https://aistudio.google.com
2. **Ollama running locally** — Run `ollama serve` and `ollama pull llama3.2:3b` for local LLM
3. **SMTP credentials** — For real email notifications (set EMAIL_BACKEND=smtp and SMTP_* vars)
4. **Telephony provider** — Twilio/Exotel account for `transfer_to_human` to actually transfer calls
5. **Stronger model** — llama3.2:3b may miss tool calls; use llama3.1:8b or Gemini API for reliability

## Commands (Windows PowerShell)
```powershell
# Setup
cd C:\DEMO\backend
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Seed database
.venv\Scripts\python.exe -m app.db.seed
.venv\Scripts\python.exe -m app.db.seed --reset  # wipe and recreate

# Run backend
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Run frontend (new terminal)
cd C:\DEMO
npm run dev

# Run E2E tests (backend must be running)
cd C:\DEMO\backend
.venv\Scripts\python.exe tests/e2e/run_conversations.py
```
