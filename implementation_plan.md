# Implementation Plan: Interactive Real-Time Voice Agent & Backend LLM Integration

This plan details how we will transition Aura Voice AI from a hardcoded frontend demo simulation to a fully working, real-time voice agent. It wires the React frontend and FastAPI backend together using WebSockets and integrates local/cloud LLMs with tool execution.

---

## User Review Required

We propose a **hybrid voice processing architecture** that combines **browser-native speech APIs (STT/TTS)** with a **backend LLM (Ollama / Gemini API)**.

> [!NOTE]
> **Why Browser-Native STT & TTS?**
> 1. **Ultra-Low Latency:** Zero server network roundtrips for audio compression and upload, resulting in sub-200ms turnaround.
> 2. **Zero System Resource Overhead:** Running models like Whisper or Edge-TTS locally on Python requires heavy GPU/CPU resources, large package downloads (PyTorch), and can be slow/sluggish on standard CPUs.
> 3. **Native Indic Support:** Google Chrome, Microsoft Edge, and Safari have excellent, free built-in support for Speech Recognition and Synthesis in **English, Hindi, and Marathi**.
> 4. **Microphone Audio Analyzer:** We will use the Web Audio API to capture the user's real mic volume and animate the 3D WebGL Orb in real-time.

Please confirm if you are comfortable with this hybrid approach (fast, local, and zero-dependency) or if you specifically require a server-side audio streaming pipeline (which would require downloading Whisper weights and setting up PyTorch).

---

## Proposed Changes

### 1. Backend: Real LLM Inference, History, & Tool Calling

#### [MODIFY] [websocket.py](file:///c:/AI%20VOICE%20AGENT/backend/app/api/websocket.py)
- Replace mock `text_input` handling with a real LLM connection.
- Integrates local **Ollama** (`http://localhost:11434/api/chat` with `llama3.1:8b`) or **Gemini API** (if `GEMINI_API_KEY` is present in the environment), with a smart rule-based fallback if no LLM server is running.
- Parse the LLM's intent to invoke tools (e.g. `book_appointment`, `get_product_price`) defined in [`tools.py`](file:///c:/AI%20VOICE%20AGENT/backend/app/api/routes/tools.py), execute the tool, and feed the result back to the LLM to formulate a response.
- Send state changes (`listening`, `thinking`, `speaking`, `tool_action`) over the WebSocket to drive the frontend 3D Orb.

#### [NEW] [llm_client.py](file:///c:/AI%20VOICE%20AGENT/backend/app/core/llm_client.py)
- Helper class to handle async HTTP requests to Ollama or Gemini APIs.
- Manages conversation history, structures the system prompt configured in the frontend, and formats tools schemas for function calling.

---

### 2. Frontend: Real-Time Audio, Speech API, & WebSocket Synchronization

#### [MODIFY] [callStore.ts](file:///c:/AI%20VOICE%20AGENT/frontend/src/stores/callStore.ts)
- Replace `runDemoScenario` and simulated timers with actual WebSocket life-cycle handling:
  - **`startCall`**: Instantiates a real WebSocket connection to `ws://localhost:8000/ws/voice/call-live-session`, launches the Web Audio API mic analyzer, and starts browser `SpeechRecognition`.
  - **`endCall`**: Closes the WebSocket connection, stops microphone recording, and halts speech.
  - **`toggleMute`**: Pauses/resumes the mic input stream and SpeechRecognition.
- Manage incoming WebSocket messages:
  - `transcript`: Render incoming user transcripts.
  - `response`: Feed text to browser `SpeechSynthesis` to speak aloud, set Orb state to `speaking`.
  - `state_change`: Transition 3D Orb visual states.
  - `tool_call`: Display tool status (running, success, etc.) and update CRM widgets.

#### [MODIFY] [Dashboard.tsx](file:///c:/AI%20VOICE%20AGENT/frontend/src/pages/Dashboard.tsx)
- Connect input bars, mute buttons, and start/end controls to call store websocket events.
- Bind the text input box to send text messages over the active WebSocket channel instead of using front-end mocks.

#### [NEW] [audioManager.ts](file:///c:/AI%20VOICE%20AGENT/frontend/src/utils/audioManager.ts)
- Utility helper to manage Web Audio API `AudioContext` and an `AnalyserNode` to sample microphone volume level at 30fps and update `audioLevel` in store.
- Simulates natural voice breathing waveforms for the AI when SpeechSynthesis is talking.

---

### 3. Settings & Credentials

#### [NEW] [.env](file:///c:/AI%20VOICE%20AGENT/.env)
- Copy `.env.example` to `.env` to configure settings locally.

---

## Verification Plan

### Manual Verification
1. **Connect & Initiate Call:** Click "Initiate Voice Call". Ensure the 3D Orb transitions to `listening` and pulses gently.
2. **Speak (STT test):** Speak into your microphone in English, Hindi, or Marathi (e.g. *"Hello, what is the price of the premium plan?"*). Check if the live transcript populates with your exact words.
3. **LLM Processing & Tool Trigger:** Watch the 3D Orb spin in its purple `thinking` wireframe mode while the backend fetches the answer (or calls the CRM pricing tool).
4. **AI Responds (TTS test):** Hear the AI speak back to you (e.g. *"Our premium plan starts at ₹999..."*). Verify that the 3D Orb pulses green/blue in sync with the spoken audio level.
5. **Interactive Conversation:** Speak a follow-up (e.g. *"Yes, book the 2 PM slot for me"*). Verify that the calendar booking tool triggers and completes successfully.

---

## Universal AURA Platform Task Queue

This is the incremental work queue for evolving the existing project into a configurable multilingual platform. Complete tasks in order; each task should be validated before moving to the next one.

### Completed Foundation

- [x] **U-01: Add universal agent configuration contract**
  - Added business identity, agent identity, capabilities, knowledge sources, tools, workflows, permissions, and policies.
  - Preserved the existing language, persona, prompt, and voice settings.
- [x] **U-02: Connect configuration to the conversation core**
  - The WebSocket conversation path now projects the active configuration into the existing generic LLM prompt.
- [x] **U-03: Extend business profile persistence**
  - Added profile fields and additive SQLite startup migrations without replacing existing tables.
- [x] **U-04: Expose the active profile in the existing UI**
  - Added compact profile and capability/tool surfaces to Dashboard and Studio while preserving the Stitch visual system and 3D orb.

### Execution Queue

- [x] **U-05: Build the configurable agent editor**
  - Add a Studio editor for business name/type, agent role, personality, languages, capabilities, knowledge sources, tools, workflows, permissions, and policies.
  - Keep the current persona and system prompt controls working.
  - Acceptance: an operator can edit all universal profile fields in Studio without changing the existing call UI.

- [x] **U-06: Connect Studio to the configuration API**
  - Load `/api/config/current` on Studio mount and save through `/api/config/update`.
  - Replaced frontend hardcoded fallback with Zustand `useConfigStore`, typed API client, and inline saving/synced/error banners.
  - Added disk persistence (`agent_config.json`) in the backend so saved configs survive restarts and reloads.
  - Acceptance: refresh and backend restarts preserve the saved profile returned by the backend; frontend build and backend TestClient pass cleanly.

- [x] **U-07: Add configurable profile selection**
  - Created `/profiles` page with full CRUD — list, search, create (modal with capabilities/tools/workflows selectors), and one-click activate.
  - Activate calls `POST /api/business/{id}/activate` which projects the BusinessProfile into the active AgentConfig runtime.
  - Active profile synced into `configStore.selectedProfileId` and `callStore.selectedProfileId` for use by new calls.
  - Added "Profiles" nav item to desktop sidebar, mobile drawer, and mobile bottom nav.
  - Stats bar shows total profiles, active profile name, unique industries, and total tools.
  - Acceptance: switching profiles changes the visible business/agent context; frontend build and typecheck pass cleanly.

- [x] **U-08: Bind calls to the selected business profile**
  - Send the selected profile ID with `start_call` and resolve its business description, offerings, knowledge, and policies in the WebSocket session.
  - Frontend call startup sends the selected profile as `business_id` / `business_profile_id`; the WebSocket session resolves it, persists it on the `Call`, returns it in `call_started`, and keeps it scoped for subsequent tool calls.
  - Tool calls now receive the active call's `business_id` automatically so offering, availability, booking, and profile-aware records stay bound to the selected business.
  - Call summaries expose `business_profile_id` for verification and operator visibility.
  - Preserve conversation history and automatic language switching within the call.
  - Acceptance: two profiles can use the same WebSocket pipeline with different context and no industry-specific branching.

- [x] **U-09: Enforce capabilities, tools, and permissions server-side**
  - Reject disabled tools before execution and enforce `permissions` and policy confirmation requirements.
  - Tool execution now resolves the active business profile from explicit params or the saved call profile.
  - Disabled profile tools return a clear permission error before execution, including legacy tool alias handling.
  - `execute_tools`, `transfer_to_human`, and configured confirmation requirements are enforced server-side.
  - Return a clear tool error to the conversation and UI.
  - Acceptance: a tool absent from the active profile cannot execute, even if the LLM requests it.

- [x] **U-10: Add healthcare safety behavior**
  - Add explicit configuration-driven safeguards for diagnosis, treatment, medication, and emergency requests.
  - WebSocket turns now check the active profile's `healthcare_safety` policy before LLM generation.
  - Diagnosis, treatment, medication, dosage, symptom, and emergency requests receive a safe non-medical response and attempted human handoff.
  - Administrative clinic workflows such as appointment booking, timings, location, reminders, rescheduling, and cancellation continue through the normal flow.
  - Escalate high-risk requests to a human and keep administrative clinic workflows available.
  - Acceptance: appointment, timings, location, and reminders work; diagnosis/treatment requests do not produce medical advice.

- [x] **U-11: Preserve and harden multilingual switching**
  - Add tests for English -> Hinglish -> Hindi/Marathi -> English continuity.
  - Live call language switching now uses configured `confidence_threshold` and `stability_count` before changing recognition language.
  - Manual language selection still applies immediately, while automatic detection ignores unsupported `auto` values and low-confidence one-off detections.
  - Config/profile load and save paths propagate language switching settings into the call store.
  - Verify confidence/stability hysteresis prevents switching on one isolated word.
  - Acceptance: language changes retain the same call history and the configured language set remains intact.

- [x] **U-12: Add focused automated tests**
  - Cover configuration validation, profile CRUD, prompt projection, tool restrictions, healthcare escalation, and language switching.
  - Added a lightweight backend `unittest` suite for configuration language-switch defaults, tool alias enforcement, confirmation responses, and healthcare safety classification.
  - Backend tests run with `python -m unittest discover -s tests`.
  - Frontend build/typecheck passes with `npm run build`; backend compile passes with `python -m compileall app tests`.
  - Acceptance: backend tests pass in the virtual environment and frontend build/typecheck remains green.

- [x] **U-13: Add real integration adapters behind generic tools**
  - Implement optional adapters for CRM, calendar/reservations, orders, email, SMS, and telephony.
  - Keep mock/local adapters available for development.
  - Added environment-configured webhook adapters: `CRM_ADAPTER_URL`, `CALENDAR_ADAPTER_URL`, `ORDER_ADAPTER_URL`, `EMAIL_ADAPTER_URL`, `SMS_ADAPTER_URL`, and `TELEPHONY_ADAPTER_URL`.
  - Generic tools call adapters first when configured and fall back to local SQLite/mock behavior when adapters are absent or fail.
  - Added explicit `httpx` backend dependency for adapter and LLM HTTP calls.
  - Acceptance: integrations are selected by configuration and generic tool names remain stable.

- [x] **U-14: Update documentation and deployment configuration**
  - Document profile configuration, API usage, tool permissions, healthcare safeguards, and production migration requirements.
  - Updated `.env.example` with optional integration adapter URLs.
  - Updated `SETUP.md` with profile operation, permission enforcement, healthcare safeguards, adapter contracts, and validation commands.
  - Updated `README.md` and `backend/README.md` with operator workflow, backend API usage, and adapter/deployment notes.
  - Acceptance: a new operator can configure and run two different business profiles from the documented steps.

### Working Rule

Work on one unchecked task at a time. After each task, run its narrow validation first, then update its checkbox and record any follow-up discovered during validation.
