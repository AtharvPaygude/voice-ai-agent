/**
 * OnboardingPage.tsx — Business Owner Onboarding Wizard
 *
 * Multi-step guided setup for new business owners.
 * Fetches real onboarding session state from the backend, posts answers per step,
 * supports skip (optional fields), back-navigation, and final publish action.
 *
 * Preserves the AURA dark-futuristic Stitch design language.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const API = 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

interface StepInfo {
  step_id: string;
  title: string;
  voice_prompt: string;
  field_name: string;
  input_type: 'text' | 'select' | 'number' | 'confirm' | 'time_range' | 'tags';
  options?: string[];
  is_optional: boolean;
  current_value: any;
  help_text?: string;
}

interface OnboardingSession {
  business_id: string;
  business_name: string | null;
  category: string;
  current_step: string;
  current_step_info: StepInfo;
  progress_percentage: number;
  answers: Record<string, any>;
  status: string;
  steps_completed: string[];
  steps_pending: string[];
}

// ─── Category icon map ─────────────────────────────────────────────────────────

const CATEGORY_ICONS: Record<string, string> = {
  'Doctor / Clinic': 'local_hospital',
  'Hotel': 'hotel',
  'Restaurant': 'restaurant',
  'Service Business': 'handyman',
  'Real Estate': 'real_estate_agent',
  'Education': 'school',
  'Other': 'business',
};

// ─── Component ────────────────────────────────────────────────────────────────

export const OnboardingPage: React.FC = () => {
  const { token, user } = useAuthStore();
  const navigate = useNavigate();

  const [session, setSession] = useState<OnboardingSession | null>(null);
  const [inputValue, setInputValue] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Redirect non-admin users
  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/');
    }
  }, [user, navigate]);

  const authHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  // Load onboarding session
  const loadSession = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/onboarding/session`, {
        headers: authHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to load session' }));
        throw new Error(err.detail || 'Failed to load session');
      }
      const data: OnboardingSession = await res.json();
      setSession(data);
      setInputValue(data.current_step_info.current_value ?? '');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Submit answer for current step
  const submitAnswer = useCallback(async (skip = false) => {
    if (!session || !token) return;
    setLoading(true);
    setError(null);
    try {
      const step = session.current_step_info;
      const res = await fetch(`${API}/api/onboarding/answer`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          step: step.step_id,
          field: step.field_name,
          value: skip ? null : inputValue,
          skip,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to submit answer' }));
        throw new Error(err.detail || 'Failed to submit answer');
      }
      const data: OnboardingSession = await res.json();
      setSession(data);
      setInputValue(data.current_step_info.current_value ?? '');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [session, token, inputValue, authHeaders]);

  // Go back — reload session (backend holds state)
  const goBack = useCallback(async () => {
    await loadSession();
  }, [loadSession]);

  // Publish profile
  const publishProfile = useCallback(async () => {
    if (!token) return;
    setPublishing(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/onboarding/publish`, {
        method: 'POST',
        headers: authHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to publish' }));
        throw new Error(err.detail || 'Failed to publish');
      }
      const data = await res.json();
      setSuccessMsg(`🎉 "${data.business_name}" is now live on AURA!`);
      setTimeout(() => navigate('/'), 3000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setPublishing(false);
    }
  }, [token, authHeaders, navigate]);

  // ─── Render Helpers ──────────────────────────────────────────────────────────

  const renderInput = (step: StepInfo) => {
    if (step.input_type === 'confirm') {
      return (
        <div className="flex flex-col gap-3 mt-4">
          <div className="glass-panel rounded-xl p-4 border border-white/10">
            <p className="text-xs font-mono text-[#b9cacb] mb-3 uppercase tracking-widest">Review Your Configuration</p>
            <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto">
              {Object.entries(session?.answers || {}).map(([key, val]) => (
                <div key={key} className="flex items-start gap-2 text-xs">
                  <span className="font-mono text-[#00f0ff] min-w-[140px] shrink-0">{key.replace(/_/g, ' ')}:</span>
                  <span className="text-[#dde2f8]">{String(val).substring(0, 120)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (step.input_type === 'select' && step.options) {
      return (
        <div className="grid grid-cols-2 gap-3 mt-4">
          {step.options.map((opt) => {
            const icon = CATEGORY_ICONS[opt] || 'category';
            const isSelected = inputValue === opt;
            return (
              <button
                key={opt}
                onClick={() => setInputValue(opt)}
                className={`flex items-center gap-3 p-4 rounded-xl border transition-all cursor-pointer text-left ${
                  isSelected
                    ? 'bg-[#00f0ff]/15 border-[#00f0ff] text-[#00f0ff] shadow-[0_0_20px_rgba(0,240,255,0.25)]'
                    : 'bg-[#191f2f]/60 border-white/10 text-[#b9cacb] hover:border-white/30 hover:text-[#dde2f8]'
                }`}
              >
                <span className="material-symbols-outlined text-[22px]">{icon}</span>
                <span className="text-sm font-medium">{opt}</span>
              </button>
            );
          })}
        </div>
      );
    }

    if (step.input_type === 'number' && step.options) {
      return (
        <div className="flex flex-wrap gap-3 mt-4">
          {step.options.map((opt) => {
            const isSelected = String(inputValue) === String(opt);
            return (
              <button
                key={opt}
                onClick={() => setInputValue(opt)}
                className={`px-5 py-3 rounded-xl border text-sm font-mono font-semibold transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#00f0ff]/15 border-[#00f0ff] text-[#00f0ff] shadow-[0_0_15px_rgba(0,240,255,0.2)]'
                    : 'bg-[#191f2f]/60 border-white/10 text-[#b9cacb] hover:border-white/30 hover:text-[#dde2f8]'
                }`}
              >
                {opt} min
              </button>
            );
          })}
          <input
            type="number"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Custom..."
            className="px-4 py-2 rounded-xl bg-[#080e1d] border border-white/15 text-[#dde2f8] text-sm font-mono placeholder-[#4a5568] focus:outline-none focus:border-[#00f0ff] w-32 transition-colors"
          />
        </div>
      );
    }

    // Default: text / textarea input
    return (
      <textarea
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder={step.help_text || `Enter ${step.title.toLowerCase()}...`}
        rows={step.field_name.includes('hours') || step.field_name.includes('offerings') ? 4 : 2}
        className="w-full mt-4 px-4 py-3 rounded-xl bg-[#080e1d] border border-white/15 text-[#dde2f8] text-sm font-mono placeholder-[#4a5568] focus:outline-none focus:border-[#00f0ff] transition-colors resize-none leading-relaxed"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.ctrlKey) submitAnswer();
        }}
      />
    );
  };

  // ─── Main Render ─────────────────────────────────────────────────────────────

  if (successMsg) {
    return (
      <div className="min-h-screen bg-[#080e1d] flex items-center justify-center p-6">
        <div className="glass-panel rounded-2xl p-10 max-w-md w-full text-center gradient-border-top">
          <span className="material-symbols-outlined text-[64px] text-[#65f2b5] mb-4 block">check_circle</span>
          <h2 className="font-['Sora'] text-2xl font-bold text-[#dde2f8] mb-3">Published!</h2>
          <p className="text-sm text-[#b9cacb] leading-relaxed">{successMsg}</p>
          <p className="text-xs font-mono text-[#00f0ff] mt-4 animate-pulse">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  if (!session && loading) {
    return (
      <div className="min-h-screen bg-[#080e1d] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-[#00f0ff] border-t-transparent animate-spin" />
          <p className="font-mono text-xs text-[#00f0ff] uppercase tracking-widest animate-pulse">Initializing Onboarding...</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-[#080e1d] flex items-center justify-center p-6">
        <div className="glass-panel rounded-2xl p-8 max-w-md w-full text-center">
          <span className="material-symbols-outlined text-[48px] text-[#f43f5e] mb-3 block">error</span>
          <p className="text-sm text-[#b9cacb]">{error || 'Failed to load onboarding session.'}</p>
          <button
            onClick={loadSession}
            className="mt-4 px-5 py-2 bg-[#00f0ff]/15 hover:bg-[#00f0ff]/25 border border-[#00f0ff]/40 text-[#00f0ff] font-mono text-xs rounded-lg transition-all cursor-pointer"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const step = session.current_step_info;
  const isConfirmStep = step.input_type === 'confirm';
  const isAlreadyDone = session.status === 'completed';
  const totalSteps = session.steps_completed.length + session.steps_pending.length;
  const currentIdx = session.steps_completed.length;

  return (
    <div className="min-h-screen bg-[#080e1d] flex items-center justify-center p-4 lg:p-8">
      {/* Background gradient blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-32 -left-32 w-[500px] h-[500px] rounded-full bg-[#571bc1]/8 blur-[100px]" />
        <div className="absolute -bottom-32 -right-32 w-[400px] h-[400px] rounded-full bg-[#00f0ff]/6 blur-[100px]" />
      </div>

      <div className="relative z-10 w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-8 h-8 rounded-full bg-[#00f0ff]/15 border border-[#00f0ff]/40 flex items-center justify-center">
            <span className="material-symbols-outlined text-[16px] text-[#00f0ff]">auto_awesome</span>
          </div>
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-[#00f0ff]">AURA Business Setup</p>
            <p className="text-xs text-[#b9cacb] font-mono">Configure your AI voice assistant</p>
          </div>
          <div className="ml-auto">
            <button
              onClick={() => navigate('/')}
              className="text-[10px] font-mono text-[#b9cacb] hover:text-[#dde2f8] flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[14px]">arrow_back</span>
              Dashboard
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#b9cacb]">
              Step {currentIdx + 1} of {totalSteps}
            </span>
            <span className="text-[10px] font-mono text-[#00f0ff]">{session.progress_percentage}%</span>
          </div>
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#571bc1] to-[#00f0ff] rounded-full transition-all duration-700"
              style={{ width: `${Math.max(4, session.progress_percentage)}%` }}
            />
          </div>
          {/* Step dots */}
          <div className="flex gap-1 mt-3">
            {Array.from({ length: totalSteps }).map((_, i) => {
              const isCompleted = i < currentIdx;
              const isCurrent = i === currentIdx;
              return (
                <div
                  key={i}
                  className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
                    isCompleted ? 'bg-[#65f2b5]' : isCurrent ? 'bg-[#00f0ff] animate-pulse' : 'bg-white/10'
                  }`}
                />
              );
            })}
          </div>
        </div>

        {/* Main Card */}
        <div className="glass-panel rounded-2xl p-8 gradient-border-top relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 rounded-full bg-[#571bc1]/5 blur-[60px] pointer-events-none" />

          {/* Step header */}
          <div className="flex items-start gap-4 mb-6">
            <div className="w-10 h-10 rounded-xl bg-[#00f0ff]/10 border border-[#00f0ff]/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="material-symbols-outlined text-[20px] text-[#00f0ff]">
                {isConfirmStep ? 'fact_check' : 'edit_note'}
              </span>
            </div>
            <div className="flex-1">
              <p className="text-[10px] font-mono uppercase tracking-widest text-[#571bc1] mb-1">
                {isConfirmStep ? 'Final Review' : `Step ${currentIdx + 1}`}
                {step.is_optional && (
                  <span className="ml-2 text-[#b9cacb] normal-case">· Optional</span>
                )}
              </p>
              <h2 className="font-['Sora'] text-xl font-bold text-[#dde2f8]">{step.title}</h2>
            </div>
          </div>

          {/* Voice prompt */}
          <div className="bg-[#191f2f]/60 rounded-xl px-5 py-4 border border-white/8 mb-5">
            <div className="flex items-start gap-2">
              <span className="material-symbols-outlined text-[16px] text-[#d0bcff] mt-0.5 shrink-0">record_voice_over</span>
              <p className="text-sm text-[#dde2f8] leading-relaxed font-light italic">"{step.voice_prompt}"</p>
            </div>
          </div>

          {/* Help text */}
          {step.help_text && (
            <p className="text-xs text-[#b9cacb] mb-1 flex items-start gap-1.5">
              <span className="material-symbols-outlined text-[14px] text-[#00f0ff] mt-0.5">info</span>
              {step.help_text}
            </p>
          )}

          {/* Input area */}
          {renderInput(step)}

          {/* Error */}
          {error && (
            <div className="mt-4 flex items-center gap-2 bg-[#93000a]/20 border border-[#ffb4ab]/30 rounded-lg px-4 py-3">
              <span className="material-symbols-outlined text-[16px] text-[#ffb4ab]">error</span>
              <p className="text-xs text-[#ffb4ab] font-mono">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-3 mt-7">
            {session.steps_completed.length > 0 && (
              <button
                onClick={goBack}
                disabled={loading}
                className="px-4 py-2.5 bg-[#191f2f]/80 border border-white/10 hover:border-white/25 text-[#b9cacb] hover:text-[#dde2f8] font-mono text-xs rounded-xl flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[16px]">arrow_back</span>
                Back
              </button>
            )}

            {step.is_optional && !isConfirmStep && (
              <button
                onClick={() => submitAnswer(true)}
                disabled={loading}
                className="px-4 py-2.5 bg-[#191f2f]/80 border border-white/10 hover:border-white/25 text-[#b9cacb] hover:text-[#dde2f8] font-mono text-xs rounded-xl flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[16px]">skip_next</span>
                Skip
              </button>
            )}

            <div className="flex-1" />

            {isConfirmStep ? (
              <button
                onClick={publishProfile}
                disabled={publishing || loading || isAlreadyDone}
                className="px-7 py-2.5 bg-gradient-to-r from-[#571bc1] to-[#00f0ff] hover:brightness-110 text-[#080e1d] font-bold text-sm rounded-xl flex items-center gap-2 transition-all cursor-pointer disabled:opacity-60 shadow-[0_0_25px_rgba(0,240,255,0.3)]"
              >
                {publishing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#080e1d]/50 border-t-[#080e1d] rounded-full animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
                    Publish &amp; Go Live
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={() => submitAnswer()}
                disabled={loading || (!inputValue && !step.is_optional)}
                className="px-7 py-2.5 bg-[#00f0ff] hover:bg-[#7df4ff] text-[#00363a] font-bold text-sm rounded-xl flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50 shadow-[0_0_20px_rgba(0,240,255,0.3)]"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-[#00363a]/50 border-t-[#00363a] rounded-full animate-spin" />
                ) : (
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                )}
                Next
              </button>
            )}
          </div>

          {!isConfirmStep && step.input_type === 'text' && (
            <p className="text-center text-[10px] font-mono text-[#4a5568] mt-3">
              Press <kbd className="px-1 py-0.5 bg-white/5 border border-white/10 rounded text-[9px]">Ctrl+Enter</kbd> to continue
            </p>
          )}
        </div>

        {session.business_name && session.business_name !== 'My New Business' && (
          <div className="mt-4 text-center">
            <p className="text-xs font-mono text-[#b9cacb]">
              Setting up: <span className="text-[#00f0ff] font-semibold">{session.business_name}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OnboardingPage;
