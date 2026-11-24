# Aura Voice AI Backend

FastAPI backend for profile-scoped voice calls, configuration, generic tools, and optional integration adapters.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

API docs: `http://localhost:8000/docs`

## Key APIs

- `GET /api/config/current`: read active agent configuration
- `POST /api/config/update`: save active agent configuration to `agent_config.json`
- `GET /api/business`: list business profiles
- `POST /api/business`: create a business profile
- `POST /api/business/{profile_id}/activate`: project a profile into the active runtime config
- `POST /api/tools/execute`: execute a generic tool with backend permission checks
- `ws://localhost:8000/ws/voice/{call_id}`: realtime call WebSocket

## Profile and Tool Enforcement

Calls send `business_id` / `business_profile_id` in the `start_call` WebSocket message. The backend resolves that profile, stores it on the call, injects it into later tool calls, and includes `business_profile_id` in call summaries.

Tool execution enforces the active profile's enabled tools, `execute_tools`, `transfer_to_human`, and `require_confirmation_for` policies before any local or external adapter runs.

## Healthcare Safeguards

If the active profile has `policies.healthcare_safety=true`, diagnosis, treatment, medication, dosage, symptom, and emergency requests are intercepted before LLM generation. The backend returns a safe non-medical response and attempts `transfer_to_human`. Administrative clinic workflows remain available.

## Integration Adapters

Set these optional environment variables to call provider webhooks before local fallback logic:

```env
CRM_ADAPTER_URL=
CALENDAR_ADAPTER_URL=
ORDER_ADAPTER_URL=
EMAIL_ADAPTER_URL=
SMS_ADAPTER_URL=
TELEPHONY_ADAPTER_URL=
```

Adapters receive:

```json
{"action":"send_sms","payload":{"to":"+10000000000","message":"Hello"}}
```

Return a JSON object with optional `status`, `message`, and provider-specific result fields.

## Validation

```powershell
python -m compileall app tests
python -m unittest discover -s tests
```
