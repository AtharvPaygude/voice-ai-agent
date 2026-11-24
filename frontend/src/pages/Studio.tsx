import React, { useState, useEffect } from 'react';
import { useCallStore } from '../stores/callStore';
import { useConfigStore } from '../stores/configStore';
import type { AgentConfig } from '../types';

export const Studio: React.FC = () => {
  const selectedPersona = useCallStore((state) => state.selectedPersona);
  const setPersona = useCallStore((state) => state.setPersona);
  const currentLanguage = useCallStore((state) => state.currentLanguage);
  const setLanguage = useCallStore((state) => state.setLanguage);

  const config = useConfigStore((state) => state.config);
  const isLoading = useConfigStore((state) => state.isLoading);
  const isSaving = useConfigStore((state) => state.isSaving);
  const configError = useConfigStore((state) => state.error);
  const lastSavedAt = useConfigStore((state) => state.lastSavedAt);
  const loadConfig = useConfigStore((state) => state.loadConfig);
  const saveConfig = useConfigStore((state) => state.saveConfig);
  const clearError = useConfigStore((state) => state.clearError);

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [autoSwitch, setAutoSwitch] = useState(true);
  const [isPlayingVoice, setIsPlayingVoice] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState(
`You are Aura, an enterprise-grade AI voice agent specialized in multilingual sales, customer service, and appointment scheduling.

CORE INSTRUCTIONS:
1. Always converse in the exact language or dialect the caller speaks (English, Hindi, Marathi, or Hinglish).
2. If the caller switches languages mid-sentence (code-switching), adapt fluidly without re-starting context.
3. Keep spoken replies concise (1-2 sentences), warm, and human-like.
4. Execute tools seamlessly: check pricing, book appointments, track orders, or handoff to human support.`
  );

  const [profile, setProfile] = useState({
    businessName: 'Aura Universal Demo',
    industry: 'Service Business',
    agentName: 'Ava',
    role: 'Universal Voice Agent',
    personality: 'Friendly professional',
    languages: ['en', 'hi', 'mr', 'hinglish'],
    capabilities: ['Sales', 'Customer Support', 'Bookings', 'FAQ + RAG', 'Human Handoff'],
    tools: ['check_availability', 'book_slot', 'check_order', 'transfer_to_human'],
    workflows: ['General inquiry', 'Booking', 'Support', 'Human handoff'],
  });

  // Load configuration from API on mount
  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // Synchronize API configuration when fetched
  useEffect(() => {
    if (config) {
      setProfile({
        businessName: config.business?.name || 'Aura Universal Demo',
        industry: config.business?.industry || 'Service Business',
        agentName: config.agent?.name || 'Ava',
        role: config.agent?.role || 'Universal Voice Agent',
        personality: config.agent?.personality || 'Friendly professional',
        languages: config.supported_languages || ['en', 'hi', 'mr', 'hinglish'],
        capabilities: config.capabilities || ['Sales', 'Customer Support', 'Bookings'],
        tools: config.tools || ['check_availability', 'book_slot', 'check_order', 'transfer_to_human'],
        workflows: config.workflows || ['General inquiry', 'Booking', 'Support', 'Human handoff'],
      });

      if (config.system_prompt) {
        setSystemPrompt(config.system_prompt);
      }
      if (config.auto_language_switch !== undefined) {
        setAutoSwitch(config.auto_language_switch);
      }
      if (config.persona && ['professional', 'friendly', 'energetic'].includes(config.persona)) {
        setPersona(config.persona as any);
      }
      if (config.primary_language && ['en', 'hi', 'mr', 'hinglish'].includes(config.primary_language)) {
        setLanguage(config.primary_language as any);
      }
    }
  }, [config, setPersona, setLanguage]);

  const businessTypeOptions = [
    'Doctor / Clinic',
    'Hotel',
    'Restaurant',
    'E-commerce',
    'Real Estate',
    'Education',
    'Service Business',
    'Other',
  ];

  const availableLanguages = [
    { code: 'en', label: 'English' },
    { code: 'hi', label: 'Hindi' },
    { code: 'mr', label: 'Marathi' },
    { code: 'hinglish', label: 'Hinglish' },
  ];

  const capabilityOptions = [
    'Sales',
    'Customer Support',
    'Service',
    'Reception',
    'Appointment Booking',
    'Reservations',
    'Order Tracking',
    'Lead Qualification',
    'CRM',
    'Ticket Creation',
    'FAQ',
    'RAG',
    'Email',
    'SMS',
    'Human Handoff',
    'Follow-up',
  ];

  const toolOptions = [
    'get_offering_price',
    'get_offering_details',
    'check_availability',
    'book_slot',
    'confirm_slot',
    'reschedule_slot',
    'cancel_slot',
    'set_reminder_preference',
    'check_order',
    'create_lead',
    'create_ticket',
    'send_email',
    'send_sms',
    'get_customer',
    'transfer_to_human',
  ];

  const workflowOptions = [
    'General inquiry',
    'Booking',
    'Support',
    'Human handoff',
    'Lead qualification',
    'Follow-up',
    'Reservation',
    'Scheduling',
  ];

  const toggleListValue = (key: 'languages' | 'capabilities' | 'tools' | 'workflows', value: string) => {
    setProfile((current) => {
      const values = [...current[key]];
      const index = values.indexOf(value);
      if (index >= 0) {
        values.splice(index, 1);
      } else {
        values.push(value);
      }
      return { ...current, [key]: values };
    });
  };

  const handleInputChange = (field: 'businessName' | 'industry' | 'agentName' | 'role' | 'personality', value: string) => {
    setProfile((current) => ({ ...current, [field]: value }));
  };

  const handleSave = async () => {
    clearError();
    const updatedPayload: AgentConfig = {
      business: {
        name: profile.businessName,
        industry: profile.industry,
        description: config?.business?.description || `${profile.businessName} serving clients in ${profile.industry}.`,
      },
      agent: {
        name: profile.agentName,
        role: profile.role,
        personality: profile.personality,
      },
      capabilities: profile.capabilities,
      knowledge_base: config?.knowledge_base || ['business_info', 'offerings', 'policies'],
      tools: profile.tools,
      workflows: profile.workflows,
      permissions: config?.permissions || {
        read_knowledge: true,
        execute_tools: true,
        transfer_to_human: true,
      },
      policies: config?.policies || {
        require_confirmation_for: ['cancellation', 'refund'],
        healthcare_safety: true,
        escalation_rules: ['high-risk request', 'caller asks for a human'],
      },
      primary_language: currentLanguage,
      auto_language_switch: autoSwitch,
      persona: selectedPersona,
      system_prompt: systemPrompt,
      supported_languages: profile.languages,
      tts_voice_map: config?.tts_voice_map || {
        en: 'en-US-GuyNeural',
        hi: 'hi-IN-MadhurNeural',
        mr: 'mr-IN-ManoharNeural',
        hinglish: 'hi-IN-MadhurNeural',
      },
      confidence_threshold: config?.confidence_threshold ?? 0.7,
      stability_count: config?.stability_count ?? 2,
    };

    const success = await saveConfig(updatedPayload);
    if (success) {
      setNotification({
        type: 'success',
        message: `Configuration saved and persisted to backend at ${new Date().toLocaleTimeString()}!`,
      });
      setTimeout(() => setNotification(null), 4000);
    } else {
      setNotification({
        type: 'error',
        message: configError || 'Failed to save configuration to backend.',
      });
    }
  };

  const handleAutoOptimizePrompt = () => {
    const optimized = `You are ${profile.agentName}, an enterprise AI voice assistant for ${profile.businessName} (${profile.industry}).
Tone & Persona: ${profile.personality}.

RULES:
1. Converse naturally in the language spoken by the caller (${profile.languages.join(', ')}).
2. For code-switching (e.g. Hinglish), seamlessly adapt without restarting the session.
3. Keep spoken replies concise (1-2 sentences), warm, and human-like.
4. Autonomous tool operations: ${profile.tools.join(', ')}.
5. Never provide medical diagnosis or hazardous advice; escalate complex requests to human staff.`;
    setSystemPrompt(optimized);
    setNotification({
      type: 'success',
      message: 'System prompt optimized for voice latency and active tools!',
    });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleVoicePreview = () => {
    setIsPlayingVoice(true);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const previewText = `Hello! I am ${profile.agentName}, representing ${profile.businessName}. Multilingual neural speech synthesis is operational.`;
      const utterance = new SpeechSynthesisUtterance(previewText);
      utterance.rate = 1.0;
      utterance.onend = () => setIsPlayingVoice(false);
      utterance.onerror = () => setIsPlayingVoice(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => setIsPlayingVoice(false), 2000);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Notifications Banner */}
      {notification && (
        <div
          className={`flex items-center justify-between px-4 py-3 rounded-lg border text-xs font-mono transition-all animate-fadeIn ${
            notification.type === 'success'
              ? 'bg-[#65f2b5]/15 border-[#65f2b5]/40 text-[#65f2b5]'
              : 'bg-red-500/15 border-red-500/40 text-red-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">
              {notification.type === 'success' ? 'check_circle' : 'error'}
            </span>
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-white/60 hover:text-white cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Global Config Error Banner */}
      {configError && !notification && (
        <div className="flex items-center justify-between px-4 py-3 rounded-lg border bg-red-500/15 border-red-500/40 text-red-300 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">warning</span>
            <span>Backend Sync Issue: {configError}</span>
          </div>
          <button
            onClick={() => loadConfig()}
            className="px-2 py-1 bg-red-500/20 hover:bg-red-500/30 rounded text-[11px] underline cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Page Header from Stitch */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-3 mb-4">
        <div>
          <h1 className="font-['Sora'] font-bold text-2xl text-[#dde2f8] mb-1">Global Agent Configuration</h1>
          <p className="text-sm text-[#b9cacb]">
            Define cognitive parameters, phonetic traits, and automatic language switching behavior.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isLoading && (
            <div className="flex items-center gap-2 text-xs font-mono text-[#00f0ff]">
              <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
              <span>Syncing with API...</span>
            </div>
          )}
          {lastSavedAt && !isLoading && (
            <span className="font-mono text-[11px] text-[#65f2b5]">
              Synced ({lastSavedAt})
            </span>
          )}
          <div className="flex items-center gap-2 bg-[#2f3445] px-3 py-1.5 rounded-full border border-white/10">
            <div className="w-2 h-2 rounded-full bg-[#65f2b5] animate-pulse"></div>
            <span className="font-mono text-xs text-[#b9cacb]">
              Active: {profile.businessName || 'Default'}
            </span>
          </div>
        </div>
      </div>

      {/* Universal Blueprint Banner */}
      <div className="glass-panel rounded-xl p-5 gradient-border-top">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-[#00f0ff]">Universal Agent Blueprint</p>
            <h2 className="font-['Sora'] font-semibold text-lg text-[#dde2f8] mt-1">
              {profile.agentName} · {profile.role}
            </h2>
            <p className="font-mono text-xs text-[#b9cacb] mt-1">
              {profile.businessName} / {profile.industry}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 md:max-w-[55%] md:justify-end">
            {profile.tools.map((tool) => (
              <span key={tool} className="text-[10px] font-mono text-[#d0bcff] bg-[#571bc1]/15 border border-[#571bc1]/40 px-2 py-1 rounded">
                {tool}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Universal Agent Editor Section */}
      <div className="glass-panel rounded-xl p-5 gradient-border-top">
        <div className="flex items-center justify-between mb-4">
          <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] uppercase">
            <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">settings_suggest</span>
            Universal Agent Editor
          </label>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={isSaving || isLoading}
              className="px-3 py-1.5 rounded-lg border border-[#00f0ff]/30 bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] text-[10px] font-mono uppercase tracking-wider cursor-pointer disabled:opacity-50 transition-all flex items-center gap-1.5"
            >
              {isSaving ? (
                <>
                  <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[14px]">save</span>
                  <span>Save Draft</span>
                </>
              )}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Business name</label>
            <input
              value={profile.businessName}
              onChange={(event) => handleInputChange('businessName', event.target.value)}
              className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Business type</label>
            <select
              value={profile.industry}
              onChange={(event) => handleInputChange('industry', event.target.value)}
              className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] appearance-none"
            >
              {businessTypeOptions.map((industry) => (
                <option key={industry} value={industry}>{industry}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Agent name</label>
            <input
              value={profile.agentName}
              onChange={(event) => handleInputChange('agentName', event.target.value)}
              className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Agent role</label>
            <input
              value={profile.role}
              onChange={(event) => handleInputChange('role', event.target.value)}
              className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Agent personality</label>
            <input
              value={profile.personality}
              onChange={(event) => handleInputChange('personality', event.target.value)}
              className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
            />
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Languages</label>
            <div className="flex flex-wrap gap-2">
              {availableLanguages.map((language) => {
                const active = profile.languages.includes(language.code);
                return (
                  <button
                    key={language.code}
                    type="button"
                    onClick={() => toggleListValue('languages', language.code)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active
                        ? 'bg-[#00f0ff]/15 border-[#00f0ff]/40 text-[#00f0ff]'
                        : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >
                    {language.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Workflows</label>
            <div className="flex flex-wrap gap-2">
              {workflowOptions.map((workflow) => {
                const active = profile.workflows.includes(workflow);
                return (
                  <button
                    key={workflow}
                    type="button"
                    onClick={() => toggleListValue('workflows', workflow)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active
                        ? 'bg-[#571bc1]/15 border-[#571bc1]/40 text-[#d0bcff]'
                        : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >
                    {workflow}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Capabilities</label>
            <div className="flex flex-wrap gap-2">
              {capabilityOptions.map((capability) => {
                const active = profile.capabilities.includes(capability);
                return (
                  <button
                    key={capability}
                    type="button"
                    onClick={() => toggleListValue('capabilities', capability)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active
                        ? 'bg-[#65f2b5]/15 border-[#65f2b5]/40 text-[#65f2b5]'
                        : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >
                    {capability}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Tools</label>
            <div className="flex flex-wrap gap-2">
              {toolOptions.map((tool) => {
                const active = profile.tools.includes(tool);
                return (
                  <button
                    key={tool}
                    type="button"
                    onClick={() => toggleListValue('tools', tool)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active
                        ? 'bg-[#f59e0b]/15 border-[#f59e0b]/40 text-[#fbbf24]'
                        : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >
                    {tool}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Bento Grid Layout from Stitch */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (Configuration) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {/* Language Settings Module from Stitch */}
          <div className="glass-panel rounded-xl p-5 gradient-border-top">
            <div className="mb-5">
              <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] mb-2 uppercase">
                <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">translate</span>
                Primary Language Base
              </label>
              <div className="relative">
                <select 
                  value={currentLanguage}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  className="w-full bg-[#080e1d] border border-white/10 rounded-lg py-2.5 px-4 text-xs font-mono text-[#dde2f8] appearance-none focus:outline-none focus:border-[#00f0ff] focus:ring-1 focus:ring-[#00f0ff] transition-all cursor-pointer"
                >
                  <option value="en">English (Global Universal)</option>
                  <option value="hinglish">Hinglish (Conversational Code-Switch)</option>
                  <option value="hi">Hindi (हिंदी - Standard/Regional)</option>
                  <option value="mr">Marathi (मराठी - Western Mesh)</option>
                </select>
                <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-[#849495] pointer-events-none text-[18px]">
                  expand_more
                </span>
              </div>
            </div>

            {/* Auto Switch Toggle from Stitch */}
            <div className="flex items-center justify-between bg-[#080e1d]/60 rounded-lg p-4 border border-white/5">
              <div className="flex-1 mr-4">
                <h3 className="flex items-center gap-2 text-xs font-semibold font-mono text-[#00f0ff] mb-0.5">
                  <span className="material-symbols-outlined text-[18px]">swap_horiz</span> 
                  Automatic Language Switching
                </h3>
                <p className="font-mono text-[11px] text-[#b9cacb]">
                  Agent will dynamically detect language shifts in real-time with hysteresis confidence &gt; 0.70
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={autoSwitch} 
                  onChange={(e) => setAutoSwitch(e.target.checked)}
                  className="sr-only peer" 
                />
                <div className="w-11 h-6 bg-[#2f3445] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00f0ff]"></div>
              </label>
            </div>
          </div>

          {/* Synthetic Persona & Speaking Style Module */}
          <div className="glass-panel rounded-xl p-5 gradient-border-top">
            <div className="flex items-center justify-between mb-4">
              <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] uppercase">
                <span className="material-symbols-outlined text-[#d0bcff] text-[18px]">psychology_alt</span>
                Speaking Style & Prosody
              </label>
              <span className="text-[10px] font-mono text-[#00f0ff] bg-[#00f0ff]/10 border border-[#00f0ff]/20 px-2 py-0.5 rounded">
                Neural SSML Active
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Style 1: Friendly */}
              <div
                onClick={() => setPersona('friendly')}
                className={`rounded-lg p-4 cursor-pointer flex flex-col items-center text-center transition-all border ${
                  selectedPersona === 'friendly'
                    ? 'bg-[#080e1d] border-[#00f0ff]/80 shadow-[0_0_15px_rgba(0,240,255,0.2)]'
                    : 'bg-[#080e1d]/40 border-white/5 opacity-70 hover:opacity-100'
                }`}
              >
                <span className={`material-symbols-outlined mb-2 text-[24px] ${selectedPersona === 'friendly' ? 'text-[#00f0ff]' : 'text-[#849495]'}`}>
                  sentiment_satisfied
                </span>
                <h4 className="font-semibold text-xs text-[#dde2f8] mb-1 font-mono">Friendly</h4>
                <p className="font-mono text-[10px] text-[#b9cacb] leading-relaxed">
                  Warm, conversational, slightly upbeat (+3% rate, +1% pitch). Ideal for hospitality and general customer service.
                </p>
              </div>

              {/* Style 2: Professional */}
              <div
                onClick={() => setPersona('professional')}
                className={`rounded-lg p-4 cursor-pointer flex flex-col items-center text-center transition-all border ${
                  selectedPersona === 'professional'
                    ? 'bg-[#080e1d] border-[#00f0ff]/80 shadow-[0_0_15px_rgba(0,240,255,0.2)]'
                    : 'bg-[#080e1d]/40 border-white/5 opacity-70 hover:opacity-100'
                }`}
              >
                <span className={`material-symbols-outlined mb-2 text-[24px] ${selectedPersona === 'professional' ? 'text-[#00f0ff]' : 'text-[#849495]'}`}>
                  work
                </span>
                <h4 className="font-semibold text-xs text-[#dde2f8] mb-1 font-mono">Professional</h4>
                <p className="font-mono text-[10px] text-[#b9cacb] leading-relaxed">
                  Concise, polished, and structured (+0% rate, 0% pitch). Ideal for B2B sales and technical consultations.
                </p>
              </div>

              {/* Style 3: Empathetic */}
              <div
                onClick={() => setPersona('energetic')}
                className={`rounded-lg p-4 cursor-pointer flex flex-col items-center text-center transition-all border ${
                  selectedPersona === 'energetic'
                    ? 'bg-[#080e1d] border-[#00f0ff]/80 shadow-[0_0_15px_rgba(0,240,255,0.2)]'
                    : 'bg-[#080e1d]/40 border-white/5 opacity-70 hover:opacity-100'
                }`}
              >
                <span className={`material-symbols-outlined mb-2 text-[24px] ${selectedPersona === 'energetic' ? 'text-[#00f0ff]' : 'text-[#849495]'}`}>
                  favorite
                </span>
                <h4 className="font-semibold text-xs text-[#dde2f8] mb-1 font-mono">Empathetic</h4>
                <p className="font-mono text-[10px] text-[#b9cacb] leading-relaxed">
                  Calm, unhurried, reassuring (-4% rate, -1% pitch). Ideal for clinics, healthcare triage, and sensitive inquiries.
                </p>
              </div>
            </div>
          </div>

          {/* Escalation & Emergency Policy Module */}
          <div className="glass-panel rounded-xl p-5 gradient-border-top">
            <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] mb-4 uppercase">
              <span className="material-symbols-outlined text-[#ffb4ab] text-[18px]">emergency</span>
              Escalation & Safety Policies
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1">Human Supervisor Phone</label>
                <input
                  type="text"
                  placeholder="+1-555-019-2832"
                  defaultValue="+1-555-019-2832"
                  className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
                />
              </div>
              <div>
                <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1">Emergency Triage Phone</label>
                <input
                  type="text"
                  placeholder="+1-555-019-9999"
                  defaultValue="+1-555-019-9999"
                  className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1">Notification Email</label>
                <input
                  type="email"
                  placeholder="escalations@yourdomain.com"
                  defaultValue="triage@apexhealthclinic.com"
                  className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff]"
                />
              </div>
            </div>
          </div>

          {/* System Prompt Directive from Stitch */}
          <div className="glass-panel rounded-xl p-5 gradient-border-top flex flex-col flex-1">
            <div className="flex justify-between items-center mb-3">
              <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] uppercase">
                <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">terminal</span>
                System Prompt Directive
              </label>
              <button 
                onClick={handleAutoOptimizePrompt}
                className="text-[#00f0ff] text-xs font-mono flex items-center gap-1 hover:text-[#7df4ff] cursor-pointer"
              >
                <span className="material-symbols-outlined text-[14px]">magic_button</span> 
                Auto-Optimize
              </button>
            </div>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="w-full h-36 bg-[#080e1d] border border-white/10 rounded-lg p-3 font-mono text-xs text-[#b9cacb] focus:outline-none focus:border-[#00f0ff] transition-all resize-none leading-relaxed"
            />
          </div>
        </div>

        {/* Right Column (Deployment & Voice Preview from Stitch) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          {/* Deployment Module from Stitch */}
          <div className="glass-panel rounded-xl p-5 gradient-border-top">
            <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] mb-4 uppercase">
              <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">rocket_launch</span>
              Deployment Actions
            </label>
            <div className="flex flex-col gap-3">
              <button 
                onClick={handleSave}
                disabled={isSaving || isLoading}
                className="w-full bg-[#00f0ff] hover:bg-[#7df4ff] text-[#00363a] py-2.5 px-4 rounded-lg font-bold text-xs shadow-[0_0_15px_rgba(0,240,255,0.4)] transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98 disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
                    Saving Configuration...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">save</span>
                    Save Configuration
                  </>
                )}
              </button>
              <button 
                onClick={() => {
                  setNotification({
                    type: 'success',
                    message: 'Voice channel initialized. Ready for calls on Dashboard.',
                  });
                  setTimeout(() => setNotification(null), 3500);
                }}
                className="w-full bg-transparent border border-[#00f0ff]/50 text-[#00f0ff] hover:bg-[#00f0ff]/10 py-2.5 px-4 rounded-lg font-semibold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">call</span>
                Initialize Voice Test
              </button>
            </div>
          </div>

          {/* Voice Preview Widget from Stitch */}
          <div className="glass-panel rounded-xl p-5 gradient-border-top flex-1 flex flex-col">
            <label className="flex items-center gap-2 text-xs font-semibold font-mono text-[#dde2f8] mb-6 uppercase">
              <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">volume_up</span>
              Phonetic Voice Preview
            </label>
            <div className="flex-1 flex flex-col items-center justify-center relative">
              {/* Concentric rings voice visualizer from Stitch */}
              <div className="w-36 h-36 rounded-full border border-[#00f0ff]/30 flex items-center justify-center relative mb-6">
                <div className={`absolute inset-0 rounded-full border border-[#00f0ff]/40 ${isPlayingVoice ? 'animate-ping' : ''}`}></div>
                <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-[#00f0ff]/20 to-[#571bc1]/30 flex items-center justify-center border border-[#00f0ff]/30 shadow-[0_0_20px_rgba(0,240,255,0.2)]">
                  <span className="material-symbols-outlined text-[#00f0ff] text-[32px]">
                    {isPlayingVoice ? 'graphic_eq' : 'mic'}
                  </span>
                </div>
              </div>

              {/* Audio Controls from Stitch */}
              <div className="w-full flex items-center justify-between font-mono text-xs text-[#b9cacb] px-4">
                <span>0:00</span>
                <button
                  onClick={handleVoicePreview}
                  className="w-10 h-10 rounded-full bg-[#00f0ff] text-[#00363a] flex items-center justify-center hover:scale-105 transition-transform shadow-[0_0_15px_rgba(0,240,255,0.4)] cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {isPlayingVoice ? 'pause' : 'play_arrow'}
                  </span>
                </button>
                <span>0:12</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
