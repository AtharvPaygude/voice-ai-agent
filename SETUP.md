# Aura Voice AI Setup Guide

This guide explains what must be installed or configured manually, how to run the application locally, and what is needed for production deployment.

## Project Requirements

Install these tools manually:

- Python 3.11 or newer
- Node.js 20 or newer
- npm
- A modern browser such as Chrome or Microsoft Edge
- Git, only if you are cloning the project from a repository

The application has two parts:

- `backend`: FastAPI API, WebSocket server, database, LLM integration, and optional server voice processing
- `frontend`: React and Vite dashboard

## Required Installation

### 1. Backend dependencies

Open PowerShell in the project folder:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation, run this once in an Administrator PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Frontend dependencies

Open a second PowerShell terminal:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
npm install
```

## Manual Configuration

### Backend environment file

Create the backend environment file from the supplied template:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
Copy-Item ..\.env.example .env
```

Edit `backend\.env` when needed:

- `CORS_ORIGINS`: frontend URLs allowed to call the backend
- `DATABASE_URL`: database connection string
- `OLLAMA_BASE_URL`: Ollama server URL
- `OLLAMA_MODEL`: installed Ollama model name
- `GEMINI_API_KEY`: optional Gemini API key
- `WHISPER_MODEL_SIZE`: server speech-to-text model size
- `TTS_ENGINE`: server text-to-speech engine

Never commit `.env` or API keys. The project `.gitignore` excludes them.

### Frontend environment file

The frontend defaults to a local backend. To configure the URLs explicitly:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
Copy-Item .env.example .env
```

For local development, the values should be:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

For production, replace these with the public HTTPS and secure WebSocket URLs:

```env
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com
```

## Optional Services

### Ollama local LLM

The application works without Ollama by using its built-in rule-based fallback. For real local LLM responses, install Ollama from https://ollama.com/download and run:

```powershell
ollama pull llama3.1:8b
ollama serve
```

Keep Ollama running while using the application with the Ollama backend.

### Gemini API

Instead of Ollama, add a Gemini API key to `backend\.env`:

```env
GEMINI_API_KEY=your_key_here
```

The backend tries Gemini first, then Ollama, then the built-in fallback.

### Server voice pipeline

The backend requirements include `faster-whisper` and `edge-tts`. They are needed only when the dashboard voice engine is set to **Server AI**.

On first use, faster-whisper downloads the configured Whisper model. This requires internet access and can use significant disk space and CPU. The default model is `base`.

The **Browser** voice engine is the recommended first test because it uses the browser's SpeechRecognition and SpeechSynthesis APIs.

## Run Locally

### Terminal 1: Start the backend

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
.\.venv\Scripts\Activate.ps1
python main.py
```

The backend runs at:

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Swagger documentation: http://localhost:8000/docs
- WebSocket: `ws://localhost:8000/ws/voice/{call_id}`

### Terminal 2: Start the frontend

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
npm run dev
```

Open the Vite URL shown in the terminal, normally:

http://localhost:5173

## Use the Voice Agent

1. Open the frontend in Chrome or Microsoft Edge.
2. Allow microphone access when prompted.
3. Open **Profiles** and create or activate the business profile you want calls to use.
4. Leave the voice engine set to **Browser** for the first test.
5. Click **Initiate Voice Call**.
6. Speak a request such as `What is the price of the standard offering?`.
7. Confirm that the transcript, tool action, response, and orb state update.
8. Use the text input in the transcript panel to test without a microphone.
9. Click the microphone button to mute or unmute.
10. Click **End Session** when finished.

Microphone access normally works on `localhost`. A deployed version must use HTTPS for microphone and browser speech APIs to work reliably.

## Configure Business Profiles

Use **Profiles** to create reusable business contexts. Each profile controls the business name, industry, description, offerings, capabilities, tools, workflows, permissions, policies, booking label, and persona. Activating a profile projects it into the active agent configuration and new calls send that selected profile ID to the WebSocket session.

Use **Studio** to edit the active agent configuration in more detail. Studio saves through `/api/config/update`, and the backend persists the active configuration in `backend\agent_config.json`.

To verify two-profile operation:

1. Create one profile for a clinic and one profile for a service or sales business.
2. Give each profile different offerings and tools.
3. Activate the first profile, start a call, and ask about its offering.
4. End the call, activate the second profile, start a new call, and ask the same question.
5. Confirm that the response and tool results match the selected profile.

## Tool Permissions and Safeguards

Tools are enforced on the backend. If a tool is not listed on the active profile, it cannot execute even if the LLM asks for it. The backend also enforces:

- `execute_tools`: disables all tool execution when set to `false`
- `transfer_to_human`: disables human transfer when set to `false`
- `require_confirmation_for`: returns `requires_confirmation` for configured high-risk actions such as cancellation

Healthcare safety is controlled by the profile policy `healthcare_safety`. When enabled, diagnosis, treatment, medication, dosage, symptom, and emergency requests receive a safe non-medical response and a human handoff attempt. Administrative requests such as appointments, timings, location, reminders, rescheduling, and cancellation continue normally.

## Integration Adapters

The generic tools can call real provider adapters by setting webhook URLs in `backend\.env`:

```env
CRM_ADAPTER_URL=
CALENDAR_ADAPTER_URL=
ORDER_ADAPTER_URL=
EMAIL_ADAPTER_URL=
SMS_ADAPTER_URL=
TELEPHONY_ADAPTER_URL=
```

Each adapter receives a JSON POST body:

```json
{"action":"book_slot","payload":{"business_id":"biz-123","date":"2026-10-05"}}
```

If an adapter URL is missing or the adapter fails, the backend falls back to local SQLite/mock behavior so development remains usable.

## Production Build

Build the frontend:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
npm run build
```

The production files are generated in `frontend\dist`.

Preview the production build locally:

```powershell
npm run preview
```

Start the backend without the development reloader in production with a process manager or hosting platform:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000
```

For a public deployment, configure:

- A public frontend host serving `frontend\dist`
- A public backend host running FastAPI
- HTTPS for the frontend
- WSS for the WebSocket connection
- `CORS_ORIGINS` set to the exact frontend origin
- A persistent database instead of local SQLite when multiple backend instances are used
- Secret storage for `GEMINI_API_KEY` and other credentials
- A reverse proxy configured to support WebSocket upgrades

## Verify the Backend

Health check from PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected result includes:

```json
{"status":"online","service":"Aura Voice AI","version":"0.1.0"}
```

Run backend tests:

```powershell
cd backend
python -m unittest discover -s tests
```

Run backend compile validation:

```powershell
cd backend
python -m compileall app tests
```

## Common Problems

### `npm run build` says `tsc` is not recognized

Run `npm install` from the `frontend` directory, then run the build there. Do not run the command from the parent Downloads folder.

### `ModuleNotFoundError: No module named 'fastapi'`

Activate the backend virtual environment and install the requirements again:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### The dashboard cannot connect

Confirm that the backend terminal is running and that the frontend `.env` contains:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

Restart Vite after changing environment variables.

### No LLM response from Ollama

The backend still responds using its fallback rules. To use Ollama, confirm that `ollama serve` is running and that `ollama list` shows the model configured in `OLLAMA_MODEL`.

### No microphone input

Check browser permissions, use Chrome or Edge, close other applications using the microphone, and make sure the page is served from `localhost` or HTTPS.
