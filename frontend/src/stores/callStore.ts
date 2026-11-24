import { create } from 'zustand';
import type { OrbState, SupportedLanguage, TranscriptMessage, LanguageSwitchEvent, ToolAction, CallMetrics } from '../types';
import {
  startMicAnalysis, stopMicAnalysis, startSpeechAnalysis, stopSpeechAnalysis,
  startVoiceRecording, stopVoiceRecording, enqueueSynthesizedAudio, stopSynthesizedAudioPlayback,
  releaseMicStream,
} from '../utils/audioManager';

export type VoicePipeline = 'browser' | 'server';
export type SpeakingStyle = 'friendly' | 'professional' | 'empathetic';

export interface LatencyBreakdown {
  sttMs?: number;
  firstTokenMs?: number;
  firstAudioMs?: number;
  totalMs?: number;
}

interface CallState {
  isCallActive: boolean;
  isMicMuted: boolean;
  orbState: OrbState;
  currentLanguage: SupportedLanguage;
  previousLanguage: SupportedLanguage;
  languageConfidence: number;
  codeSwitchProbability: number;
  transcript: TranscriptMessage[];
  interimTranscript: string;
  switchEvents: LanguageSwitchEvent[];
  recentTools: ToolAction[];
  metrics: CallMetrics;
  latencyBreakdown: LatencyBreakdown;
  selectedPersona: 'professional' | 'friendly' | 'energetic';
  speakingStyle: SpeakingStyle;
  audioLevel: number;
  voicePipeline: VoicePipeline;
  selectedProfileId: string | null;
  callerName: string;
  callerPhone: string;
  callerEmail: string;
  lastEscalation: any | null;
  languageSwitchThreshold: number;
  languageSwitchStabilityCount: number;
  pendingLanguage: SupportedLanguage | null;
  pendingLanguageCount: number;

  // Actions
  startCall: () => void;
  endCall: () => void;
  toggleMute: () => void;
  setOrbState: (state: OrbState) => void;
  setLanguage: (lang: SupportedLanguage, confidence?: number, reason?: string) => void;
  setSpeakingStyle: (style: SpeakingStyle) => void;
  setCallerInfo: (name: string, phone: string, email?: string) => void;
  addTranscriptMessage: (msg: Omit<TranscriptMessage, 'id' | 'timestamp'>) => void;
  triggerToolAction: (tool: string, params: Record<string, any>, result?: Record<string, any>) => void;
  setPersona: (persona: 'professional' | 'friendly' | 'energetic') => void;
  setAudioLevel: (level: number) => void;
  setSelectedProfileId: (id: string | null) => void;
  runDemoScenario: () => void;
  sendMessage: (text: string) => void;
  interruptSpeaking: (reason?: string) => void;
  setVoicePipeline: (pipeline: VoicePipeline) => void;
  configureLanguageSwitching: (threshold?: number, stabilityCount?: number) => void;
  clearEscalationAlert: () => void;
}

const configuredApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const configuredWsUrl = import.meta.env.VITE_WS_URL || configuredApiUrl.replace(/^http/, 'ws');

// Module-level WebSocket and SpeechRecognition references
let socket: WebSocket | null = null;
let recognition: any = null;

// Adaptive silence endpointing state
let ambientNoiseSamples: number[] = [];
let calibratedNoiseFloor = 0.02;
let lastKnownUtteranceText = '';
const MIN_SPEECH_MS = 450;
let silenceTimer: ReturnType<typeof setTimeout> | null = null;
let speechStartedAt: number | null = null;

let agentTurnOpen = false;
let isQueueDrained = true;
let serverTurnComplete = false;
let resumeGuardTimer: ReturnType<typeof setTimeout> | null = null;

const maybeResumeListening = () => {
  if (resumeGuardTimer) {
    clearTimeout(resumeGuardTimer);
    resumeGuardTimer = null;
  }
  resumeGuardTimer = setTimeout(() => {
    resumeGuardTimer = null;
    const state = useCallStore.getState();
    if (state.isCallActive && !state.isMicMuted && !agentTurnOpen) {
      state.setOrbState('listening');
      if (state.voicePipeline === 'server') {
        startServerListening().catch(console.error);
      } else {
        startBrowserListening();
      }
    }
  }, 500);
};

const onQueueDrained = () => {
  isQueueDrained = true;
  if (serverTurnComplete) {
    agentTurnOpen = false;
    maybeResumeListening();
  }
};

const handleTurnComplete = () => {
  serverTurnComplete = true;
  if (isQueueDrained) {
    agentTurnOpen = false;
    maybeResumeListening();
  }
};

const getAdaptiveSilenceThreshold = () => {
  return Math.min(0.08, Math.max(0.015, calibratedNoiseFloor * 1.5));
};

const getAdaptiveSilenceDuration = () => {
  const trimmed = lastKnownUtteranceText.trim();
  // Quick end for clearly finished questions or sentences
  if (trimmed.endsWith('?') || trimmed.endsWith('.') || trimmed.endsWith('!')) {
    return 600;
  }
  // Longer wait if ends with trailing words, comma, or ellipsis
  if (trimmed.endsWith(',') || trimmed.endsWith('...') || / (um|uh|and|or|so|but)$/i.test(trimmed)) {
    return 1200;
  }
  return 850;
};

const clearSilenceTimer = () => {
  if (silenceTimer) {
    clearTimeout(silenceTimer);
    silenceTimer = null;
  }
};

const initSpeechRecognition = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("SpeechRecognition not supported in this browser.");
    return null;
  }

  const rec = new SpeechRecognition();
  rec.continuous = true;
  rec.interimResults = true; // Enabled for real-time live transcript display

  rec.onresult = (event: any) => {
    let interimText = '';
    let finalText = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalText += event.results[i][0].transcript;
      } else {
        interimText += event.results[i][0].transcript;
      }
    }

    const state = useCallStore.getState();

    // Show interim words in UI
    if (interimText) {
      useCallStore.setState({ interimTranscript: interimText.trim() });
      lastKnownUtteranceText = interimText.trim();
    }

    // REAL-TIME BARGE-IN INTERRUPTION: If agent is speaking, halt speech immediately
    if ((interimText || finalText) && state.orbState === 'speaking') {
      state.interruptSpeaking('Caller speech detected');
    }

    // Final speech result from browser recognition
    if (finalText.trim()) {
      useCallStore.setState({ interimTranscript: '' });
      lastKnownUtteranceText = finalText.trim();

      if (state.isCallActive && !state.isMicMuted && socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
          type: 'text_input',
          text: finalText.trim(),
          language: state.currentLanguage
        }));
      }
    }
  };

  rec.onend = () => {
    const state = useCallStore.getState();
    if (state.isCallActive && !state.isMicMuted) {
      try {
        rec.start();
      } catch (e) {}
    }
  };

  rec.onerror = (e: any) => {
    console.error("SpeechRecognition error:", e);
  };

  return rec;
};

const speakResponse = (text: string, lang: SupportedLanguage) => {
  if (!('speechSynthesis' in window)) {
    console.warn("SpeechSynthesis not supported.");
    return;
  }

  window.speechSynthesis.cancel();
  stopSpeechAnalysis();

  const cleanText = text.replace(/:::TOOL_CALL:::.*?:::END_TOOL_CALL:::/gs, '').trim();
  if (!cleanText) return;

  const utterance = new SpeechSynthesisUtterance(cleanText);
  let utteranceLang = 'en-US';
  if (lang === 'hi' || lang === 'hinglish') utteranceLang = 'hi-IN';
  else if (lang === 'mr') utteranceLang = 'mr-IN';

  utterance.lang = utteranceLang;
  
  const voices = window.speechSynthesis.getVoices();
  const matchingVoice = voices.find(v => v.lang.startsWith(utteranceLang));
  if (matchingVoice) {
    utterance.voice = matchingVoice;
  }
  utterance.rate = 1.05;

  utterance.onstart = () => {
    useCallStore.getState().setOrbState('speaking');
    startSpeechAnalysis((level) => {
      useCallStore.setState({ audioLevel: level });
    });

    // Ensure recognition remains active in background for real-time barge-in detection
    if (recognition && !useCallStore.getState().isMicMuted) {
      try {
        recognition.start();
      } catch (e) {}
    }
  };

  utterance.onend = () => {
    stopSpeechAnalysis();
    useCallStore.setState({ audioLevel: 0 });
    resumeListening();
  };

  utterance.onerror = (e) => {
    console.error("TTS synthesis error:", e);
    stopSpeechAnalysis();
    useCallStore.setState({ audioLevel: 0 });
    resumeListening();
  };

  window.speechSynthesis.speak(utterance);
};

const resumeListening = () => {
  const state = useCallStore.getState();
  if (state.isCallActive && !state.isMicMuted) {
    state.setOrbState('listening');
    startMicAnalysis((level) => {
      useCallStore.setState({ audioLevel: level });
    }).catch(console.error);

    if (recognition) {
      try {
        recognition.start();
      } catch (e) {}
    }
  } else {
    state.setOrbState('idle');
  }
};

const startBrowserListening = () => {
  if (!recognition) {
    recognition = initSpeechRecognition();
  }

  if (recognition) {
    const lang = useCallStore.getState().currentLanguage;
    recognition.lang = lang === 'hi' || lang === 'hinglish' ? 'hi-IN' : lang === 'mr' ? 'mr-IN' : 'en-US';
    try {
      recognition.start();
    } catch (error) {
      console.debug('Speech recognition is already running.', error);
    }
  }

  if (!useCallStore.getState().isMicMuted) {
    startMicAnalysis((level) => useCallStore.setState({ audioLevel: level })).catch(console.error);
  }
};

// ─── Server-side voice pipeline (real STT/TTS via faster-whisper and edge-tts) ──

const handleServerPipelineLevel = (level: number) => {
  useCallStore.setState({ audioLevel: level });

  const state = useCallStore.getState();
  if (state.orbState !== 'listening') return;

  // Calibrate ambient noise floor continuously during silence
  if (speechStartedAt === null) {
    ambientNoiseSamples.push(level);
    if (ambientNoiseSamples.length > 40) ambientNoiseSamples.shift();
    const sorted = [...ambientNoiseSamples].sort((a, b) => a - b);
    calibratedNoiseFloor = sorted[Math.floor(sorted.length / 2)] || 0.015;
  }

  const threshold = getAdaptiveSilenceThreshold();

  if (level > threshold) {
    if (speechStartedAt === null) {
      console.log(`[AUDIO VAD] Speech detected! (level: ${level.toFixed(3)} > threshold: ${threshold.toFixed(3)})`);
      speechStartedAt = Date.now();
    }
    clearSilenceTimer();
  } else if (speechStartedAt !== null) {
    // Max duration safety ceiling (12 seconds)
    if (Date.now() - speechStartedAt > 12000) {
      console.log('[AUDIO VAD] Max utterance duration (12s) reached, finalizing.');
      speechStartedAt = null;
      clearSilenceTimer();
      finishVoiceUtterance();
      return;
    }

    if (!silenceTimer) {
      const waitMs = getAdaptiveSilenceDuration();
      silenceTimer = setTimeout(() => {
        const spoke = speechStartedAt !== null && Date.now() - speechStartedAt >= MIN_SPEECH_MS;
        console.log(`[AUDIO VAD] Silence detected for ${waitMs}ms. Valid speech turn: ${spoke}`);
        speechStartedAt = null;
        clearSilenceTimer();
        if (spoke) finishVoiceUtterance();
      }, waitMs);
    }
  }
};

const startServerListening = async () => {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;
  speechStartedAt = null;
  clearSilenceTimer();

  try {
    console.log('[AUDIO] Activating server-side microphone listening...');
    const recordingStream = await startVoiceRecording((chunk) => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(chunk);
      }
    });
    await startMicAnalysis(handleServerPipelineLevel, recordingStream);
    console.log('[AUDIO] Microphone listening active and analyzed.');
  } catch (err) {
    console.error('[AUDIO] Failed to start microphone recording:', err);
  }
};

const finishVoiceUtterance = async () => {
  console.log('[AUDIO] Finalizing voice utterance, stopping recorder...');
  useCallStore.getState().setOrbState('thinking');
  await stopVoiceRecording();
  stopMicAnalysis();
  clearSilenceTimer();
  speechStartedAt = null;

  if (socket && socket.readyState === WebSocket.OPEN) {
    console.log('[AUDIO] Sending voice_input event to backend STT...');
    socket.send(JSON.stringify({ type: 'voice_input', language: useCallStore.getState().currentLanguage }));
  }
};

const playServerAudio = (bytes: ArrayBuffer) => {
  useCallStore.getState().setOrbState('speaking');
  enqueueSynthesizedAudio(
    bytes,
    (level) => useCallStore.setState({ audioLevel: level }),
    onQueueDrained
  );
};

const INITIAL_TRANSCRIPT: TranscriptMessage[] = [
  {
    id: 't-init',
    speaker: 'system',
    text: "Aura AI Ready — Click 'Start Call' to connect.",
    language: 'en',
    confidence: 1.0,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
];

const SUPPORTED_CALL_LANGUAGES: SupportedLanguage[] = ['en', 'hi', 'mr', 'hinglish'];

export const useCallStore = create<CallState>((set, get) => ({
  isCallActive: false,
  isMicMuted: false,
  orbState: 'idle',
  currentLanguage: 'en',
  previousLanguage: 'en',
  languageConfidence: 1.0,
  codeSwitchProbability: 0.0,
  transcript: INITIAL_TRANSCRIPT,
  interimTranscript: '',
  switchEvents: [],
  recentTools: [],
  metrics: {
    latencyMs: 0,
    tokensPerSec: 0,
    activeStreams: 0,
    durationSeconds: 0,
    leadScore: 0,
    sentiment: 'neutral',
    sentimentScore: 0.5,
    intent: 'None'
  },
  latencyBreakdown: {},
  selectedPersona: 'professional',
  speakingStyle: 'friendly',
  callerName: 'Unknown caller',
  callerPhone: '',
  callerEmail: '',
  lastEscalation: null,
  audioLevel: 0.0,
  voicePipeline: 'server', // Server pipeline enabled by default for real STT/TTS
  selectedProfileId: null,
  languageSwitchThreshold: 0.7,
  languageSwitchStabilityCount: 2,
  pendingLanguage: null,
  pendingLanguageCount: 0,
  setSelectedProfileId: (id: string | null) => set({ selectedProfileId: id }),
  setCallerInfo: (name: string, phone: string, email = '') => set({
    callerName: name.trim() || 'Unknown caller',
    callerPhone: phone.trim(),
    callerEmail: email.trim(),
  }),
  clearEscalationAlert: () => set({ lastEscalation: null }),

  setSpeakingStyle: (style: SpeakingStyle) => {
    set({ speakingStyle: style });
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'set_style',
        style: style,
      }));
    }
  },

  startCall: () => {
    if (get().isCallActive) return;

    set({
      isCallActive: true,
      orbState: 'listening',
      transcript: [],
      interimTranscript: '',
      switchEvents: [],
      recentTools: [],
      lastEscalation: null,
      metrics: {
        latencyMs: 0, // Truthful: 0 until first turn completes
        tokensPerSec: 0,
        activeStreams: 1,
        durationSeconds: 0,
        leadScore: 0,
        sentiment: 'neutral',
        sentimentScore: 0.5,
        intent: 'Connecting'
      },
      latencyBreakdown: {}
    });

    const callId = `call-${Date.now()}`;
    socket = new WebSocket(`${configuredWsUrl}/ws/voice/${callId}`);
    socket.binaryType = 'arraybuffer';

    socket.onopen = () => {
      if (socket) {
        const profileId = get().selectedProfileId;
        socket.send(JSON.stringify({
          type: 'start_call',
          business_id: profileId,
          business_profile_id: profileId,
          language: get().currentLanguage,
          send_audio: get().voicePipeline === 'server',
          speaking_style: get().speakingStyle,
          caller_name: get().callerName,
          caller_phone: get().callerPhone,
          caller_email: get().callerEmail,
        }));
      }
    };

    socket.onmessage = (event) => {
      // Binary frame = synthesized TTS audio from server pipeline
      if (event.data instanceof ArrayBuffer) {
        agentTurnOpen = true;
        serverTurnComplete = false;
        isQueueDrained = false;
        stopVoiceRecording();
        stopMicAnalysis();
        playServerAudio(event.data);
        return;
      }

      try {
        const msg = JSON.parse(event.data);
        const { type } = msg;

        if (type === 'audio_start') {
          agentTurnOpen = true;
          serverTurnComplete = false;
          isQueueDrained = false;
          stopVoiceRecording();
          stopMicAnalysis();
          return;
        }

        if (type === 'state_change') {
          const usingServerPipeline = get().voicePipeline === 'server';
          if (usingServerPipeline) {
            if (msg.state !== 'idle' && msg.state !== 'listening') {
              set({ orbState: msg.state });
            }
          } else {
            if (msg.state !== 'listening') {
              stopMicAnalysis();
            } else if (!get().isMicMuted) {
              startMicAnalysis((lvl) => set({ audioLevel: lvl })).catch(console.error);
            }
            set({ orbState: msg.state });
          }
        }

        else if (type === 'turn_complete') {
          handleTurnComplete();
        }

        else if (type === 'turn_error') {
          stopSynthesizedAudioPlayback();
          agentTurnOpen = false;
          maybeResumeListening();
        }
        
        else if (type === 'agent_greeting_started') {
          set({ orbState: 'speaking' });
          get().addTranscriptMessage({
            speaker: 'system',
            text: `Agent speaks first for ${msg.business_name || 'Aura AI'}...`,
            language: get().currentLanguage,
            confidence: 1.0
          });
        }

        else if (type === 'audio_interrupted') {
          set({ orbState: 'interrupted', audioLevel: 0 });
          stopSynthesizedAudioPlayback();
          if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
          }
          stopSpeechAnalysis();
          agentTurnOpen = false;
          maybeResumeListening();
        }

        else if (type === 'transcript') {
          const { speaker, text, language, confidence } = msg;
          if (speaker === 'user') {
            const currentLang = get().currentLanguage;
            if (currentLang !== language) {
              get().setLanguage(language, confidence, "Detected in STT voice transcription stream");
            }
          }
          get().addTranscriptMessage({ speaker, text, language, confidence });
        }

        else if (type === 'response_sentence') {
          // Streaming sentence delivery from backend LLM pipeline
          const { text, language } = msg;
          const tr = get().transcript;
          const lastMsg = tr[tr.length - 1];

          if (lastMsg && lastMsg.speaker === 'agent') {
            // Append to existing agent utterance turn
            const updated = tr.slice(0, -1);
            set({
              transcript: [
                ...updated,
                { ...lastMsg, text: `${lastMsg.text} ${text}`.trim() }
              ]
            });
          } else {
            get().addTranscriptMessage({
              speaker: 'agent',
              text: text,
              language: language || get().currentLanguage,
              confidence: 1.0,
            });
          }
        }
        
        else if (type === 'response') {
          const { text, language, has_audio } = msg;
          // In browser pipeline, synthesize via speechSynthesis
          if (!has_audio) {
            speakResponse(text, language);
          }
        }

        else if (type === 'latency_metrics') {
          // Real backend latency measurement
          const { latency_stt_ms, latency_first_token_ms, latency_first_audio_ms, latency_total_ms } = msg;
          set({
            latencyBreakdown: {
              sttMs: latency_stt_ms,
              firstTokenMs: latency_first_token_ms,
              firstAudioMs: latency_first_audio_ms,
              totalMs: latency_total_ms,
            },
            metrics: {
              ...get().metrics,
              latencyMs: latency_total_ms || latency_first_audio_ms || 0,
            }
          });
        }

        else if (type === 'escalation_alert') {
          set({ lastEscalation: msg });
          get().addTranscriptMessage({
            speaker: 'system',
            text: `⚠️ Escalation Alert: ${msg.reason || 'Support'} (${msg.priority || 'medium'} priority). Transfer/notification initiated.`,
            language: get().currentLanguage,
            confidence: 1.0,
          });
        }
        
        else if (type === 'tool_call') {
          const { tool, result } = msg;
          get().triggerToolAction(tool, {}, result);
        }
        
        else if (type === 'call_started') {
          get().addTranscriptMessage({
            speaker: 'system',
            text: `Connected to ${msg.business_name || 'Aura AI'}. Agent speaking first...`,
            language: 'en',
            confidence: 1.0
          });
          // Mic will start after greeting finishes playing via maybeResumeListening()
        }
        
        else if (type === 'call_summary') {
          get().addTranscriptMessage({
            speaker: 'system',
            text: `Call Concluded. Summary: ${msg.summary}`,
            language: 'en',
            confidence: 1.0
          });
        }
      } catch (err) {
        console.error("Error processing websocket message:", err);
      }
    };

    socket.onclose = () => {
      set({ isCallActive: false, orbState: 'idle' });
      stopMicAnalysis();
      stopSpeechAnalysis();
      stopVoiceRecording();
      stopSynthesizedAudioPlayback();
      releaseMicStream();
    };

    socket.onerror = () => {
      set({ orbState: 'error' });
      stopMicAnalysis();
      stopSpeechAnalysis();
      stopVoiceRecording();
      stopSynthesizedAudioPlayback();
      releaseMicStream();
    };
  },

  endCall: () => {
    if (socket) {
      try {
        socket.send(JSON.stringify({ type: 'end_call' }));
        socket.close();
      } catch (e) {}
      socket = null;
    }
    
    if (recognition) {
      try {
        recognition.stop();
      } catch (e) {}
    }
    
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    stopMicAnalysis();
    stopSpeechAnalysis();
    stopVoiceRecording();
    stopSynthesizedAudioPlayback();
    releaseMicStream();
    clearSilenceTimer();
    speechStartedAt = null;
    if (resumeGuardTimer) {
      clearTimeout(resumeGuardTimer);
      resumeGuardTimer = null;
    }
    agentTurnOpen = false;
    isQueueDrained = true;
    serverTurnComplete = false;
    
    set({
      isCallActive: false,
      orbState: 'idle',
      audioLevel: 0,
      interimTranscript: ''
    });
  },

  toggleMute: () => {
    const nextMuted = !get().isMicMuted;
    set({ isMicMuted: nextMuted });
    const usingServerPipeline = get().voicePipeline === 'server';

    if (nextMuted) {
      stopMicAnalysis();
      if (usingServerPipeline) {
        stopVoiceRecording();
        clearSilenceTimer();
        speechStartedAt = null;
      }
      set({ audioLevel: 0 });
      if (recognition) {
        try {
          recognition.stop();
        } catch (e) {}
      }
      set({ orbState: 'idle' });
    } else {
      if (get().isCallActive) {
        set({ orbState: 'listening' });
        if (usingServerPipeline) {
          startServerListening().catch(console.error);
        } else {
          startMicAnalysis((lvl) => set({ audioLevel: lvl })).catch(console.error);
          if (recognition) {
            let recLang = 'en-US';
            const lang = get().currentLanguage;
            if (lang === 'hi') recLang = 'hi-IN';
            else if (lang === 'mr') recLang = 'mr-IN';
            else if (lang === 'hinglish') recLang = 'hi-IN';
            recognition.lang = recLang;
            try {
              recognition.start();
            } catch (e) {}
          }
        }
      }
    }
  },

  setOrbState: (state) => set({ orbState: state }),

  setLanguage: (lang, confidence = 0.95, reason = 'Dynamic detection') => {
    if (!SUPPORTED_CALL_LANGUAGES.includes(lang)) return;

    const prev = get().currentLanguage;
    if (prev !== lang) {
      const isManualOverride = reason.toLowerCase().includes('manual');
      const threshold = get().languageSwitchThreshold;
      const requiredStableDetections = get().languageSwitchStabilityCount;

      if (!isManualOverride) {
        if (confidence < threshold) {
          set({ pendingLanguage: null, pendingLanguageCount: 0 });
          return;
        }

        const pendingLanguage = get().pendingLanguage;
        const nextCount = pendingLanguage === lang ? get().pendingLanguageCount + 1 : 1;
        set({ pendingLanguage: lang, pendingLanguageCount: nextCount });

        if (nextCount < requiredStableDetections) {
          return;
        }
      }

      const newEvent: LanguageSwitchEvent = {
        id: `sw-${Date.now()}`,
        from: prev,
        to: lang,
        confidence,
        reason,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      set({
        previousLanguage: prev,
        currentLanguage: lang,
        languageConfidence: confidence,
        orbState: 'language_switch',
        pendingLanguage: null,
        pendingLanguageCount: 0,
        switchEvents: [newEvent, ...get().switchEvents]
      });

      if (recognition && get().isCallActive && !get().isMicMuted) {
        try {
          recognition.stop();
        } catch (e) {}
        
        let recLang = 'en-US';
        if (lang === 'hi') recLang = 'hi-IN';
        else if (lang === 'mr') recLang = 'mr-IN';
        else if (lang === 'hinglish') recLang = 'hi-IN';
        recognition.lang = recLang;

        setTimeout(() => {
          if (get().isCallActive && !get().isMicMuted && get().orbState !== 'speaking') {
            try {
              recognition.start();
            } catch (e) {}
          }
        }, 300);
      }

      setTimeout(() => {
        if (get().orbState === 'language_switch') {
          set({ orbState: get().isMicMuted ? 'idle' : 'listening' });
        }
      }, 1400);
    }
  },

  addTranscriptMessage: (msg) => {
    const newMessage: TranscriptMessage = {
      ...msg,
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    set({
      transcript: [...get().transcript, newMessage]
    });
  },

  triggerToolAction: (tool, parameters, result) => {
    const actionId = `tool-${Date.now()}`;
    const newTool: ToolAction = {
      id: actionId,
      tool,
      parameters,
      result,
      status: 'running',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    set({
      orbState: 'tool_action',
      recentTools: [newTool, ...get().recentTools],
      metrics: {
        ...get().metrics,
        intent: tool.replace(/_/g, ' ')
      }
    });

    setTimeout(() => {
      set({
        orbState: 'success',
        recentTools: get().recentTools.map(t => t.id === actionId ? { ...t, status: 'success', result: result || { status: 'ok' } } : t)
      });
      setTimeout(() => {
        set({ orbState: 'speaking' });
      }, 800);
    }, 1200);
  },

  setPersona: (persona) => set({ selectedPersona: persona }),
  setAudioLevel: (audioLevel) => set({ audioLevel }),

  interruptSpeaking: (reason = 'Caller interrupted') => {
    if (get().orbState === 'speaking') {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      stopSynthesizedAudioPlayback();
      stopSpeechAnalysis();
      agentTurnOpen = false;
      serverTurnComplete = true;
      isQueueDrained = true;
      set({ orbState: 'interrupted', audioLevel: 0 });

      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'interrupt' }));
      }

      get().addTranscriptMessage({
        speaker: 'system',
        text: `⚡ BARGE-IN: Caller interrupted (${reason}). Playback immediately stopped.`,
        language: get().currentLanguage,
        confidence: 1.0,
        isInterrupted: true,
      });

      maybeResumeListening();
    }
  },

  runDemoScenario: () => {
    // Flow: Connect -> Inquire -> Barge-in -> Multilingual -> Confirmation
    if (!get().isCallActive || !socket || socket.readyState !== WebSocket.OPEN) {
      get().startCall();
    }

    setTimeout(() => {
      get().sendMessage("Hello, can you tell me what services you provide?");
    }, 2000);

    setTimeout(() => {
      get().interruptSpeaking("Caller requested instant pricing");
      get().sendMessage("Wait, before that, what are your consultation fees?");
    }, 5500);

    setTimeout(() => {
      get().sendMessage("Kya aap Saturday ko appointments book kar sakte hain?");
    }, 10000);

    setTimeout(() => {
      get().sendMessage("Mi udya sakali 10 vajta yeu shakto ka?");
    }, 15000);

    setTimeout(() => {
      get().sendMessage("Yes please, book me for tomorrow at 10 AM.");
    }, 20000);
  },

  sendMessage: (text: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'text_input',
        text: text,
        language: get().currentLanguage
      }));
    }
  },

  setVoicePipeline: (pipeline: VoicePipeline) => {
    if (get().isCallActive) {
      console.warn('Cannot switch voice pipeline while a call is active. End the call first.');
      return;
    }
    set({ voicePipeline: pipeline });
  },

  configureLanguageSwitching: (threshold = 0.7, stabilityCount = 2) => {
    set({
      languageSwitchThreshold: threshold,
      languageSwitchStabilityCount: Math.max(1, stabilityCount),
      pendingLanguage: null,
      pendingLanguageCount: 0,
    });
  }
}));
