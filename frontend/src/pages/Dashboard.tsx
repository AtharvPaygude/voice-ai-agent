import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AiOrb } from '../components/orb/AiOrb';
import { LiveCallQueue } from '../components/call/LiveCallQueue';
import { LiveTranscript } from '../components/transcript/LiveTranscript';
import { SentimentPanel } from '../components/analytics/SentimentPanel';
import { DiscoveryPanel } from '../components/discovery/DiscoveryPanel';
import { useCallStore } from '../stores/callStore';
import { useConfigStore } from '../stores/configStore';
import { ACTIVE_AGENT_PROFILE } from '../types';
import type { OrbState, SupportedLanguage } from '../types';
import type { SpeakingStyle } from '../stores/callStore';
import { getLanguageMeta, UNIVERSAL_LANGUAGE_REGISTRY } from '../utils/languages';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const isCallActive = useCallStore((state) => state.isCallActive);
  const orbState = useCallStore((state) => state.orbState);
  const currentLanguage = useCallStore((state) => state.currentLanguage);
  const languageConfidence = useCallStore((state) => state.languageConfidence);
  const metrics = useCallStore((state) => state.metrics);
  const latencyBreakdown = useCallStore((state) => state.latencyBreakdown);
  const startCall = useCallStore((state) => state.startCall);
  const endCall = useCallStore((state) => state.endCall);
  const toggleMute = useCallStore((state) => state.toggleMute);
  const isMicMuted = useCallStore((state) => state.isMicMuted);
  const setLanguage = useCallStore((state) => state.setLanguage);
  const interruptSpeaking = useCallStore((state) => state.interruptSpeaking);
  const voicePipeline = useCallStore((state) => state.voicePipeline);
  const setVoicePipeline = useCallStore((state) => state.setVoicePipeline);
  const speakingStyle = useCallStore((state) => state.speakingStyle);
  const setSpeakingStyle = useCallStore((state) => state.setSpeakingStyle);
  const callerName = useCallStore((state) => state.callerName);
  const callerPhone = useCallStore((state) => state.callerPhone);
  const callerEmail = useCallStore((state) => state.callerEmail);
  const setCallerInfo = useCallStore((state) => state.setCallerInfo);
  const lastEscalation = useCallStore((state) => state.lastEscalation);
  const clearEscalationAlert = useCallStore((state) => state.clearEscalationAlert);

  const [inputCallerName, setInputCallerName] = useState(callerName);
  const [inputCallerPhone, setInputCallerPhone] = useState(callerPhone);
  const [inputCallerEmail, setInputCallerEmail] = useState(callerEmail);

  const config = useConfigStore((state) => state.config);
  const loadConfig = useConfigStore((state) => state.loadConfig);
  const profiles = useConfigStore((state) => state.profiles);
  const selectedProfileId = useConfigStore((state) => state.selectedProfileId);
  const loadProfiles = useConfigStore((state) => state.loadProfiles);
  const selectAndActivateProfile = useConfigStore((state) => state.selectAndActivateProfile);
  const isActivating = useConfigStore((state) => state.isActivating);

  useEffect(() => {
    if (!config) {
      loadConfig();
    }
    if (profiles.length === 0) {
      loadProfiles();
    }
  }, [config, loadConfig, profiles.length, loadProfiles]);

  const activeBusinessName = config?.business?.name || ACTIVE_AGENT_PROFILE.business.name;
  const activeIndustry = config?.business?.industry || ACTIVE_AGENT_PROFILE.business.industry;
  const activeAgentName = config?.agent?.name || ACTIVE_AGENT_PROFILE.agent.name;
  const activeAgentRole = config?.agent?.role || ACTIVE_AGENT_PROFILE.agent.role;
  const activeCapabilities = config?.capabilities?.length ? config.capabilities : ACTIVE_AGENT_PROFILE.capabilities;

  const handleStartCall = () => {
    setCallerInfo(inputCallerName, inputCallerPhone, inputCallerEmail);
    startCall();
  };

  const getOrbStateLabel = (st: OrbState) => {
    switch (st) {
      case 'listening': return 'LISTENING FOR CALLER SPEECH...';
      case 'thinking': return 'NEURAL INTENT & RAG PROCESSING...';
      case 'speaking': return 'VOICE SYNTHESIS ACTIVE (TTS)';
      case 'interrupted': return '⚡ CALLER BARGE-IN — AUDIO PLAYBACK HALTED';
      case 'language_switch': return 'AUTOMATIC LANGUAGE SWITCHING...';
      case 'tool_action': return 'EXECUTING BUSINESS TOOL API...';
      case 'success': return 'ACTION COMPLETED SUCCESSFULLY';
      case 'error': return 'TELEMETRY EXCEPTION DETECTED';
      case 'human_transfer': return 'TRANSFERRING TO HUMAN SUPERVISOR';
      case 'idle':
      default: return 'STANDBY — READY FOR INCOMING CALL';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">
      {/* LEFT COLUMN: Call Queue & Agents (3 Cols) */}
      <div className="lg:col-span-3 flex flex-col gap-6">
        <LiveCallQueue />

        <div className="glass-panel rounded-xl p-5 gradient-border-top">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div>
              <p className="text-[10px] font-mono uppercase tracking-widest text-[#00f0ff]">Active Agent Profile</p>
              <h3 className="font-['Sora'] font-semibold text-base text-[#dde2f8] mt-1">{activeBusinessName}</h3>
            </div>
            <span className="text-[10px] font-mono uppercase text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-2 py-1 rounded">
              {activeIndustry}
            </span>
          </div>

          {profiles.length > 0 && (
            <div className="mb-3">
              <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1 flex items-center justify-between">
                <span>Select Business Profile</span>
                {isActivating && <span className="text-[#00f0ff] animate-pulse">Switching...</span>}
              </label>
              <select
                value={selectedProfileId || ''}
                onChange={(e) => {
                  if (e.target.value) {
                    selectAndActivateProfile(e.target.value);
                  }
                }}
                disabled={isActivating}
                className="w-full bg-[#080e1d] border border-white/15 rounded-lg px-2.5 py-1.5 text-xs font-mono text-[#00f0ff] focus:outline-none focus:border-[#00f0ff] cursor-pointer"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id} className="bg-[#080e1d] text-[#dde2f8]">
                    {p.name} ({p.industry})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-2 text-xs font-mono text-[#b9cacb] mb-3">
            <span className="material-symbols-outlined text-[16px] text-[#d0bcff]">smart_toy</span>
            <span>{activeAgentName} · {activeAgentRole}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {activeCapabilities.map((capability) => (
              <span key={capability} className="text-[10px] font-mono text-[#b9cacb] bg-[#080e1d] border border-white/10 px-2 py-1 rounded">
                {capability}
              </span>
            ))}
          </div>
        </div>

        {/* Provider Discovery Panel */}
        <DiscoveryPanel />
      </div>

      {/* CENTER COLUMN: Main AI Core View & 3D Orb (5 Cols) */}
      <div className="lg:col-span-5 flex flex-col gap-6">
        {/* Escalation Alert Banner if active */}
        {lastEscalation && (
          <div className="bg-[#93000a]/30 border border-[#ffb4ab] rounded-xl p-4 flex items-center justify-between shadow-[0_0_20px_rgba(255,180,171,0.2)]">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#ffb4ab] text-[24px] animate-pulse">warning</span>
              <div>
                <div className="text-xs font-bold text-[#ffdad6] uppercase tracking-wider flex items-center gap-2">
                  <span>Escalation Alert ({lastEscalation.priority || 'Urgent'})</span>
                  <span className="text-[10px] font-mono text-[#ffb4ab] bg-[#93000a] px-1.5 py-0.5 rounded">
                    {lastEscalation.reason}
                  </span>
                </div>
                <div className="text-xs text-[#ffb4ab] mt-0.5">
                  Caller: {lastEscalation.caller_name || 'Caller'} ({lastEscalation.caller_phone || 'No phone'})
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/escalations')}
                className="px-3 py-1.5 bg-[#ffb4ab] hover:bg-[#ffdad6] text-[#690005] font-semibold text-xs rounded-lg transition-all"
              >
                View Escalation
              </button>
              <button
                onClick={clearEscalationAlert}
                className="p-1 text-[#ffb4ab] hover:text-[#ffdad6]"
                title="Dismiss"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
          </div>
        )}

        {/* Main 3D Orb Live AI Core Card from Stitch */}
        <div className="glass-panel-active rounded-xl flex-1 relative overflow-hidden flex flex-col items-center justify-center min-h-[440px] p-6">
          {/* Top Label */}
          <div className="absolute top-4 left-6 flex items-center gap-2 z-10">
            <div className="w-2 h-2 rounded-full bg-[#00f0ff] pulse-ring shadow-[0_0_10px_rgba(0,240,255,0.8)]"></div>
            <span className="font-mono text-xs text-[#00f0ff] tracking-widest uppercase font-semibold">Live AI Core</span>
          </div>

          {/* Top Right Quick Language Selector & Voice Engine */}
          <div className="absolute top-4 right-6 flex flex-col items-end gap-1.5 z-10">
            <div className="flex items-center gap-1.5">
              {(['en', 'hi', 'mr', 'hinglish', 'ja'] as SupportedLanguage[]).map((lang) => {
                const meta = getLanguageMeta(lang);
                return (
                  <button
                    key={lang}
                    onClick={() => setLanguage(lang, 0.99, 'Manual selection override')}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase transition-all cursor-pointer flex items-center gap-1 ${
                      currentLanguage === lang
                        ? 'bg-[#00f0ff] text-[#00363a] font-bold shadow-[0_0_10px_rgba(0,240,255,0.4)]'
                        : 'bg-[#2f3445] text-[#b9cacb] hover:text-[#dde2f8]'
                    }`}
                  >
                    <span>{meta.flag}</span>
                    <span>{lang}</span>
                  </button>
                );
              })}

              {/* Worldwide Languages Dropdown */}
              <select
                value={currentLanguage}
                onChange={(e) => setLanguage(e.target.value as SupportedLanguage, 0.99, 'Manual worldwide language override')}
                className="bg-[#191f2f] text-[#00f0ff] border border-white/10 rounded px-1.5 py-0.5 text-[10px] font-mono cursor-pointer focus:outline-none"
                title="Worldwide Languages"
              >
                <option value="" disabled>More Languages</option>
                <optgroup label="Indian Languages">
                  {Object.values(UNIVERSAL_LANGUAGE_REGISTRY)
                    .filter((l) => l.region === 'India' && !['en', 'hi', 'mr', 'hinglish'].includes(l.code))
                    .map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.flag} {l.name} [{l.status.toUpperCase()}]
                      </option>
                    ))}
                </optgroup>
                <optgroup label="Worldwide Global">
                  {Object.values(UNIVERSAL_LANGUAGE_REGISTRY)
                    .filter((l) => l.region !== 'India')
                    .map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.flag} {l.name} [{l.status.toUpperCase()}]
                      </option>
                    ))}
                </optgroup>
              </select>
            </div>

            {/* Voice engine toggle */}
            <div
              className={`flex items-center gap-1 bg-[#191f2f]/80 rounded-full p-0.5 border border-white/10 ${isCallActive ? 'opacity-50 pointer-events-none' : ''}`}
              title={isCallActive ? "End the call to switch voice engine" : "Choose the voice engine"}
            >
              <button
                onClick={() => setVoicePipeline('browser')}
                className={`px-2 py-0.5 rounded-full text-[9px] font-mono uppercase transition-all cursor-pointer ${
                  voicePipeline === 'browser'
                    ? 'bg-[#65f2b5] text-[#00363a] font-bold'
                    : 'text-[#b9cacb] hover:text-[#dde2f8]'
                }`}
              >
                Browser
              </button>
              <button
                onClick={() => setVoicePipeline('server')}
                className={`px-2 py-0.5 rounded-full text-[9px] font-mono uppercase transition-all cursor-pointer ${
                  voicePipeline === 'server'
                    ? 'bg-[#65f2b5] text-[#00363a] font-bold'
                    : 'text-[#b9cacb] hover:text-[#dde2f8]'
                }`}
              >
                Server AI
              </button>
            </div>
          </div>

          {/* 3D Orb Centerpiece */}
          <div className="relative w-full h-[260px] flex items-center justify-center">
            <AiOrb />
          </div>

          {/* Speaking Style Selector Pills */}
          <div className="flex items-center gap-2 mb-2 z-10">
            <span className="text-[10px] font-mono text-[#849495] uppercase">Style:</span>
            {(['friendly', 'professional', 'empathetic'] as SpeakingStyle[]).map((style) => (
              <button
                key={style}
                onClick={() => setSpeakingStyle(style)}
                className={`px-2.5 py-1 rounded-full text-[10px] font-mono uppercase transition-all cursor-pointer border ${
                  speakingStyle === style
                    ? 'bg-[#00f0ff]/20 border-[#00f0ff] text-[#00f0ff] font-bold shadow-[0_0_10px_rgba(0,240,255,0.3)]'
                    : 'bg-[#191f2f] border-white/10 text-[#849495] hover:text-[#dde2f8]'
                }`}
              >
                {style}
              </button>
            ))}
          </div>

          {/* Status Overlay Bottom */}
          <div className="w-full flex flex-col items-center mt-1 z-10">
            {(() => {
              const curMeta = getLanguageMeta(currentLanguage);
              return (
                <h2 className="font-['Sora'] font-semibold text-lg text-[#dde2f8] mb-1 flex items-center gap-2">
                  <span>Voice Agent Active</span>
                  <span className="text-xs font-mono text-[#65f2b5] px-2 py-0.5 rounded bg-[#65f2b5]/10 border border-[#65f2b5]/20 flex items-center gap-1">
                    <span>{curMeta.flag}</span>
                    <span>{curMeta.name.toUpperCase()}</span>
                    <span className="text-[10px] text-[#b9cacb]">({(languageConfidence * 100).toFixed(0)}%)</span>
                  </span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase border ${
                    curMeta.status === 'supported'
                      ? 'text-[#65f2b5] bg-[#65f2b5]/10 border-[#65f2b5]/30'
                      : curMeta.status === 'partially_supported'
                      ? 'text-[#f59e0b] bg-[#f59e0b]/10 border-[#f59e0b]/30'
                      : 'text-[#849495] bg-white/5 border-white/10'
                  }`}>
                    {curMeta.status.replace('_', ' ')}
                  </span>
                </h2>
              );
            })()}
            <p className="font-mono text-xs text-[#00f0ff] mb-2 text-center tracking-wider">
              {getOrbStateLabel(orbState)}
            </p>

            <div className="flex gap-4 items-center bg-[#2f3445]/80 px-4 py-1.5 rounded-full border border-white/10 backdrop-blur-md">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#00f0ff] text-[15px]">multiline_chart</span>
                <span className="font-mono text-xs text-[#b9cacb]">
                  <strong className="text-[#00f0ff]">{metrics.activeStreams}</strong> Stream
                </span>
              </div>
              <div className="w-px h-3 bg-white/20"></div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#65f2b5] text-[15px]">bolt</span>
                <span className="font-mono text-xs text-[#b9cacb]">
                  <strong className="text-[#65f2b5]">{metrics.latencyMs || '—'}ms</strong> Latency
                </span>
              </div>
            </div>
          </div>

          {/* Caller Profile Form when not in call */}
          {!isCallActive && (
            <div className="mt-3 w-full max-w-md flex items-center gap-2 z-10">
              <input
                type="text"
                placeholder="Caller Name"
                value={inputCallerName}
                onChange={(e) => setInputCallerName(e.target.value)}
                className="w-1/3 bg-[#080e1d] border border-white/10 rounded-lg px-2.5 py-1 text-xs font-mono text-[#dde2f8] placeholder:text-[#849495] focus:outline-none focus:border-[#00f0ff]"
              />
              <input
                type="text"
                placeholder="Phone"
                value={inputCallerPhone}
                onChange={(e) => setInputCallerPhone(e.target.value)}
                className="w-1/3 bg-[#080e1d] border border-white/10 rounded-lg px-2.5 py-1 text-xs font-mono text-[#dde2f8] placeholder:text-[#849495] focus:outline-none focus:border-[#00f0ff]"
              />
              <input
                type="email"
                placeholder="Email (for report)"
                value={inputCallerEmail}
                onChange={(e) => setInputCallerEmail(e.target.value)}
                className="w-1/3 bg-[#080e1d] border border-white/10 rounded-lg px-2.5 py-1 text-xs font-mono text-[#dde2f8] placeholder:text-[#849495] focus:outline-none focus:border-[#00f0ff]"
              />
            </div>
          )}

          {/* Call Action Bar at Bottom */}
          <div className="mt-3 flex items-center gap-3 z-10">
            {isCallActive ? (
              <>
                <button
                  onClick={toggleMute}
                  className={`p-2.5 rounded-full border transition-all cursor-pointer ${
                    isMicMuted
                      ? 'bg-[#93000a]/30 border-[#ffb4ab] text-[#ffb4ab]'
                      : 'bg-[#191f2f] border-white/10 text-[#00f0ff] hover:border-[#00f0ff]'
                  }`}
                  title={isMicMuted ? "Unmute Microphone" : "Mute Microphone"}
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {isMicMuted ? 'mic_off' : 'mic'}
                  </span>
                </button>

                {/* Real-time Barge-In Interruption button active during speech */}
                {orbState === 'speaking' && (
                  <button
                    onClick={() => interruptSpeaking('Manual Barge-In Button')}
                    className="px-3.5 py-1.5 bg-[#f43f5e]/20 hover:bg-[#f43f5e]/35 text-[#fda4af] border border-[#f43f5e]/50 font-mono font-semibold text-xs rounded-full flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(244,63,94,0.35)] animate-pulse cursor-pointer"
                    title="Stop AI speech immediately"
                  >
                    <span className="material-symbols-outlined text-[16px] text-[#f43f5e]">flash_on</span>
                    <span>Barge-In (Stop AI)</span>
                  </button>
                )}

                <button
                  onClick={endCall}
                  className="px-4 py-2 bg-[#93000a] hover:bg-[#ffb4ab] hover:text-[#690005] text-[#ffdad6] font-semibold text-xs rounded-full border border-[#ffb4ab]/40 transition-all flex items-center gap-1.5 cursor-pointer shadow-[0_0_15px_rgba(255,100,100,0.3)]"
                >
                  <span className="material-symbols-outlined text-[16px]">call_end</span>
                  <span>End Call</span>
                </button>
              </>
            ) : (
              <button
                onClick={handleStartCall}
                className="px-6 py-2.5 bg-[#00f0ff] hover:bg-[#7df4ff] text-[#00363a] font-bold text-xs rounded-full shadow-[0_0_20px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">call</span>
                <span>Start Call</span>
              </button>
            )}
          </div>
        </div>

        {/* Bottom Metrics Grid with Real Latency Breakdown */}
        <div className="grid grid-cols-3 gap-4">
          <div className="glass-panel rounded-xl p-4 flex flex-col justify-center relative overflow-hidden">
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-[#00f0ff] opacity-70"></div>
            <div className="font-mono text-xs text-[#b9cacb] mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">speed</span> Total Latency
              </span>
              {latencyBreakdown.sttMs && (
                <span className="text-[10px] text-[#00f0ff]">STT: {latencyBreakdown.sttMs}ms</span>
              )}
            </div>
            <div className="font-['Sora'] font-semibold text-xl text-[#dde2f8]">
              {metrics.latencyMs ? metrics.latencyMs : '—'}<span className="text-xs text-[#00f0ff] ml-1">ms</span>
            </div>
            {latencyBreakdown.firstTokenMs && (
              <div className="text-[10px] font-mono text-[#849495] mt-1 flex justify-between">
                <span>TTFT: {latencyBreakdown.firstTokenMs}ms</span>
                <span>TTS: {latencyBreakdown.firstAudioMs || '—'}ms</span>
              </div>
            )}
          </div>

          <div className="glass-panel rounded-xl p-4 flex flex-col justify-center relative overflow-hidden">
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-[#65f2b5] opacity-70"></div>
            <div className="font-mono text-xs text-[#b9cacb] mb-1 flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">psychology</span> Style
            </div>
            <div className="font-['Sora'] font-semibold text-lg text-[#dde2f8] capitalize">
              {speakingStyle}
            </div>
            <div className="text-[10px] font-mono text-[#65f2b5] mt-1">
              Active prosody tuned
            </div>
          </div>

          <div className="glass-panel rounded-xl p-4 flex flex-col justify-center relative overflow-hidden">
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-[#8b5cf6] opacity-70"></div>
            <div className="font-mono text-xs text-[#b9cacb] mb-1 flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">record_voice_over</span> Call Pipeline
            </div>
            <div className="font-['Sora'] font-semibold text-lg text-[#dde2f8] uppercase">
              {voicePipeline === 'server' ? 'Whisper+Edge' : 'Browser WebAPI'}
            </div>
            <div className="text-[10px] font-mono text-[#d0bcff] mt-1">
              {isCallActive ? 'Live streaming' : 'Ready'}
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN: Real-time Sentiment & Live Transcript (4 Cols) */}
      <div className="lg:col-span-4 flex flex-col gap-6">
        <SentimentPanel />
        <div className="flex-1">
          <LiveTranscript />
        </div>
      </div>
    </div>
  );
};
