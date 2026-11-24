# Aura Voice AI — Manual Additions and Setup Checklist

This file lists the things that are not automatically included in the project and must be added manually when running or deploying the app.

---

## 1. Required Local Installation

### Python

Install Python 3.11 or newer.

### Node.js and npm

Install Node.js 20 or newer and npm.

### Browser

Use Chrome or Microsoft Edge for best support with microphone access and browser speech APIs.

### Git

Only needed if you are cloning or updating the project from a repository.

---

## 2. Backend Dependencies to Install Manually

From the backend folder:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs packages such as:

- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- AioSQLite
- WebSockets
- Faster-Whisper
- Edge-TTS

If PowerShell blocks activation, run once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 3. Frontend Dependencies to Install Manually

From the frontend folder:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
npm install
```

This installs:

- React
- Vite
- TypeScript
- Tailwind
- React Router
- Three.js
- Framer Motion
- Zustand

---

## 4. Environment Variables to Add Manually

### Backend .env

Create a backend environment file if needed:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
Copy-Item ..\.env.example .env
```

Then configure values such as:

```env
CORS_ORIGINS=http://localhost:5173
DATABASE_URL=sqlite:///./aura_voice.db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
GEMINI_API_KEY=
WHISPER_MODEL_SIZE=base
TTS_ENGINE=edge-tts
```

Important:

- Do not commit your .env file
- Store API keys securely
- Never push secrets to version control

### Frontend .env

Create a frontend env file if needed:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
Copy-Item .env.example .env
```

Typical local values:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 5. External Services You May Need to Add

### Ollama

For real LLM responses, install Ollama and run:

```powershell
ollama pull llama3.1:8b
ollama serve
```

This is optional because the app has a built-in fallback mode.

### Gemini API

If you want Gemini-backed responses, add an API key in the backend .env file:

```env
GEMINI_API_KEY=your_key_here
```

### Speech and TTS models

The server voice pipeline may download Whisper models such as:

- base
- small
- medium

This may require internet access and local disk space.

---

## 6. API or External Integrations to Add Later

The project architecture is ready for integrations, but you may need to add the following manually depending on your deployment needs:

- Real CRM API integration
- Email sending service
- Calendar booking API
- Authentication and user identity service
- Database migration setup for production
- Storage for conversation logs
- Monitoring and observability tools
- Deployment hosting credentials

---

## 7. Production Deployment Additions

For a public deployment, you must manually configure:

- HTTPS for the frontend
- WSS for the WebSocket connection
- CORS origins for the exact production frontend URL
- A production database instead of local SQLite
- Secret management for API keys
- Reverse proxy to support WebSocket upgrades
- Hosting environment such as Azure, Vercel, or a custom server

---

## 8. Optional Manual Enhancements

These are not mandatory for initial running, but are often added in real usage:

- real authentication system
- admin dashboard
- user roles and permissions
- external analytics dashboard
- conversation history database
- call recording and archiving
- escalation workflow to human operators
- customer CRM sync
- voice quality tuning

---

## 9. Manual Checklist Before Running the App

Use this checklist:

- [ ] Python installed
- [ ] Node.js and npm installed
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] .env file created for backend if needed
- [ ] .env file created for frontend if needed
- [ ] Ollama or Gemini configured if using AI responses
- [ ] Browser microphone permission enabled
- [ ] Backend server started
- [ ] Frontend server started

---

## 10. Final Note

This project is mostly ready to run locally, but some services, integrations, and production settings must be added by hand. Those include environment files, API keys, model setup, and deployment-specific infrastructure.
