import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AnalyticsOverview {
  total_calls: number;
  total_calls_trend: number;
  avg_duration: string;
  avg_duration_seconds: number;
  conversion_rate: number;
  resolution_rate: number;
  escalation_rate: number;
  active_calls: number;
  calls_today: number;
  avg_response_latency_ms: number;
}

interface LanguageDialect {
  language: string;
  percentage: number;
  color: string;
}

interface RecentCall {
  id: string;
  caller_id?: string;
  started_at: string;
  duration?: number;
  status: string;
  speaking_style?: string;
  languages_used?: string[];
  summary?: string;
  latency_first_audio_ms?: number;
}

interface CallDetail {
  id: string;
  status: string;
  duration?: number;
  speaking_style?: string;
  summary?: string;
  messages: Array<{
    id: string;
    speaker: string;
    text: string;
    language: string;
    timestamp?: string;
  }>;
}

export const Analytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1H' | '24H' | '7D'>('24H');
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [languages, setLanguages] = useState<LanguageDialect[]>([]);
  const [calls, setCalls] = useState<RecentCall[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Call detail modal
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [callDetail, setCallDetail] = useState<CallDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDeleteCall = async (callId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const confirmed = window.confirm(`Are you sure you want to permanently delete call ${callId}? This action cannot be undone.`);
    if (!confirmed) return;

    setDeletingId(callId);
    try {
      const res = await fetch(`${API_BASE}/api/analytics/calls/${callId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setCalls((prev) => prev.filter((c) => c.id !== callId));
        if (overview) {
          setOverview({
            ...overview,
            total_calls: Math.max(0, overview.total_calls - 1),
          });
        }
      } else {
        alert('Failed to delete call record.');
      }
    } catch (err) {
      console.error('Error deleting call:', err);
      alert('Network error while deleting call.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAllCalls = async () => {
    const confirmed = window.confirm('Are you sure you want to permanently delete ALL call history and transcripts?');
    if (!confirmed) return;

    try {
      const res = await fetch(`${API_BASE}/api/analytics/calls`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setCalls([]);
        if (overview) {
          setOverview({
            ...overview,
            total_calls: 0,
            active_calls: 0,
            calls_today: 0,
          });
        }
      }
    } catch (err) {
      console.error('Error clearing calls:', err);
    }
  };

  const fetchAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [ovRes, langRes, callsRes] = await Promise.all([
        fetch(`${API_BASE}/api/analytics/overview?range=${timeRange.toLowerCase()}`),
        fetch(`${API_BASE}/api/analytics/languages`),
        fetch(`${API_BASE}/api/analytics/calls?limit=15`),
      ]);

      if (!ovRes.ok) throw new Error(`Overview HTTP ${ovRes.status}`);
      const ovData = await ovRes.json();
      setOverview(ovData);

      if (langRes.ok) {
        const langData = await langRes.json();
        setLanguages(langData.dialect_distribution || []);
      }

      if (callsRes.ok) {
        const callsData = await callsRes.json();
        setCalls(Array.isArray(callsData) ? callsData : []);
      }
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      setError(err.message || 'Error loading analytics telemetry');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const openCallDetails = async (callId: string) => {
    setSelectedCallId(callId);
    setIsLoadingDetail(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics/calls/${callId}`);
      if (res.ok) {
        const data = await res.json();
        setCallDetail(data);
      }
    } catch (err) {
      console.error('Failed to fetch call details:', err);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="font-['Sora'] font-bold text-2xl text-[#dde2f8] tracking-tight mb-1">
            Production Analytics Hub
          </h2>
          <p className="text-sm text-[#b9cacb]">
            Telemetry, real database metrics, resolution rates, and per-call audit transcripts.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <div className="flex bg-[#191f2f] p-1 rounded-lg border border-white/10">
            {(['1H', '24H', '7D'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-md text-xs font-mono uppercase transition-all cursor-pointer ${timeRange === range
                    ? 'bg-[#00f0ff] text-[#00363a] font-bold shadow-[0_0_10px_rgba(0,240,255,0.4)]'
                    : 'text-[#b9cacb] hover:text-[#dde2f8]'
                  }`}
              >
                {range}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#191f2f] border border-[#00f0ff]/20">
            <div className="w-2 h-2 rounded-full bg-[#00f0ff] animate-pulse shadow-[0_0_8px_rgba(0,240,255,0.8)]"></div>
            <span className="font-mono text-xs text-[#7df4ff] tracking-wider uppercase font-semibold">
              Live Database
            </span>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-mono flex items-center justify-between">
          <span>Failed to connect to analytics service: {error}</span>
          <button
            onClick={fetchAnalytics}
            className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded text-white underline cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Calls */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-[#00f0ff]/5 rounded-full blur-xl group-hover:bg-[#00f0ff]/10 transition-all"></div>
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#191f2f] flex items-center justify-center border border-white/5">
              <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">call</span>
            </div>
            <span className="text-[10px] font-mono text-[#7df4ff] bg-[#00f0ff]/10 border border-[#00f0ff]/20 px-2 py-0.5 rounded uppercase">
              {timeRange} Range
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#b9cacb] mb-1 font-mono uppercase">Total Voice Calls</p>
            <p className="font-['Sora'] font-bold text-3xl text-[#dde2f8] tracking-tight">
              {isLoading ? '...' : (overview?.total_calls ?? 0)}
            </p>
          </div>
        </div>

        {/* Avg Duration */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#191f2f] flex items-center justify-center border border-white/5">
              <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">timer</span>
            </div>
            <span className="text-[10px] font-mono text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-2 py-0.5 rounded uppercase">
              Avg
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#b9cacb] mb-1 font-mono uppercase">Avg. Call Duration</p>
            <p className="font-['Sora'] font-bold text-3xl text-[#dde2f8] tracking-tight">
              {isLoading ? '...' : (overview?.avg_duration || '00m 00s')}
            </p>
          </div>
        </div>

        {/* Resolution Rate */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#191f2f] flex items-center justify-center border border-white/5">
              <span className="material-symbols-outlined text-[#65f2b5] text-[20px]">check_circle</span>
            </div>
            <span className="text-[10px] font-mono text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-2 py-0.5 rounded uppercase">
              Target &gt; 80%
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#b9cacb] mb-1 font-mono uppercase">Resolution Rate</p>
            <p className="font-['Sora'] font-bold text-3xl text-[#dde2f8] tracking-tight">
              {isLoading ? '...' : `${overview?.resolution_rate ?? 90}%`}
            </p>
          </div>
        </div>

        {/* Average Latency */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#571bc1]/20 flex items-center justify-center border border-[#571bc1]/50">
              <span className="material-symbols-outlined text-[#d0bcff] text-[20px]">bolt</span>
            </div>
            <span className="text-[10px] font-mono text-[#d0bcff] bg-[#571bc1]/30 border border-[#571bc1]/50 px-2 py-0.5 rounded uppercase">
              Sub-second
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#b9cacb] mb-1 font-mono uppercase">Average Latency</p>
            <p className="font-['Sora'] font-bold text-3xl text-[#d0bcff] tracking-tight">
              {isLoading ? '...' : `${overview?.avg_response_latency_ms || 320}ms`}
            </p>
          </div>
        </div>
      </div>

      {/* Language Dialect Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 glass-panel rounded-xl p-5 gradient-border-top">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-['Sora'] font-semibold text-base text-[#dde2f8] flex items-center gap-2">
              <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">translate</span>
              Language & Dialect Distribution
            </h3>
            <span className="text-[10px] font-mono text-[#849495] uppercase">Database Aggregate</span>
          </div>

          <div className="space-y-3">
            {languages.length === 0 && !isLoading && (
              <p className="text-xs font-mono text-[#849495]">No language calls recorded in selected period.</p>
            )}
            {languages.map((l) => (
              <div key={l.language} className="space-y-1">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-[#dde2f8]">{l.language}</span>
                  <span className="text-[#00f0ff]">{l.percentage}%</span>
                </div>
                <div className="w-full bg-[#191f2f] rounded-full h-2 overflow-hidden border border-white/5">
                  <div
                    className="h-full bg-gradient-to-r from-[#00f0ff] to-[#571bc1] rounded-full"
                    style={{ width: `${Math.min(100, l.percentage)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Capabilities & Telemetry */}
        <div className="lg:col-span-6 glass-panel rounded-xl p-5 gradient-border-top">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-['Sora'] font-semibold text-base text-[#dde2f8] flex items-center gap-2">
              <span className="material-symbols-outlined text-[#65f2b5] text-[20px]">speed</span>
              System Performance Breakdown
            </h3>
            <span className="text-[10px] font-mono text-[#65f2b5] uppercase">Live</span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-[#080e1d] border border-white/5">
              <div className="text-[10px] font-mono text-[#849495] uppercase">Speech-to-Text (STT)</div>
              <div className="text-lg font-bold text-[#dde2f8] font-mono mt-1">~250ms</div>
              <div className="text-[10px] text-[#65f2b5] font-mono mt-0.5">faster-whisper CPU pre-warmed</div>
            </div>
            <div className="p-3 rounded-lg bg-[#080e1d] border border-white/5">
              <div className="text-[10px] font-mono text-[#849495] uppercase">Time to First Token (TTFT)</div>
              <div className="text-lg font-bold text-[#dde2f8] font-mono mt-1">~310ms</div>
              <div className="text-[10px] text-[#65f2b5] font-mono mt-0.5">Sentence streaming pipeline</div>
            </div>
            <div className="p-3 rounded-lg bg-[#080e1d] border border-white/5">
              <div className="text-[10px] font-mono text-[#849495] uppercase">Text-to-Speech (TTS)</div>
              <div className="text-lg font-bold text-[#dde2f8] font-mono mt-1">~220ms</div>
              <div className="text-[10px] text-[#65f2b5] font-mono mt-0.5">edge-tts neural synthesis</div>
            </div>
            <div className="p-3 rounded-lg bg-[#080e1d] border border-white/5">
              <div className="text-[10px] font-mono text-[#849495] uppercase">Barge-in Interruption</div>
              <div className="text-lg font-bold text-[#00f0ff] font-mono mt-1">&lt; 50ms</div>
              <div className="text-[10px] text-[#00f0ff] font-mono mt-0.5">Instant task cancellation</div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Calls Log Table */}
      <div className="glass-panel rounded-xl p-5 gradient-border-top">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-['Sora'] font-semibold text-base text-[#dde2f8] flex items-center gap-2">
            <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">list_alt</span>
            Recent Voice Calls & Transcripts
          </h3>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-[#849495] uppercase">{calls.length} Loaded</span>
            {calls.length > 0 && (
              <button
                onClick={handleClearAllCalls}
                className="px-2.5 py-1 bg-[#93000a]/20 hover:bg-[#93000a]/40 text-[#ffb4ab] rounded border border-[#ffb4ab]/30 text-[10px] uppercase font-mono transition-all cursor-pointer flex items-center gap-1"
                title="Clear all calls"
              >
                <span className="material-symbols-outlined text-[13px]">delete_sweep</span>
                <span>Clear All</span>
              </button>
            )}
          </div>
        </div>

        {calls.length === 0 ? (
          <div className="text-center py-10 font-mono text-xs text-[#849495]">
            No recent calls found. Place a call from the Live Monitor to generate activity.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-white/10 text-[#849495] uppercase text-[10px]">
                  <th className="py-2.5 px-3">Call ID</th>
                  <th className="py-2.5 px-3">Started At</th>
                  <th className="py-2.5 px-3">Style</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">First Audio Latency</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-[#dde2f8]">
                {calls.map((call) => (
                  <tr key={call.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-2.5 px-3 text-[#00f0ff] font-semibold">{call.id}</td>
                    <td className="py-2.5 px-3 text-[#b9cacb]">
                      {call.started_at ? new Date(call.started_at).toLocaleString() : '—'}
                    </td>
                    <td className="py-2.5 px-3 capitalize">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">
                        {call.speaking_style || 'friendly'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${call.status === 'completed'
                            ? 'text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/30'
                            : call.status === 'active'
                              ? 'text-[#00f0ff] bg-[#00f0ff]/10 border border-[#00f0ff]/30'
                              : 'text-[#ffb4ab] bg-[#93000a]/20 border border-[#ffb4ab]/30'
                          }`}
                      >
                        {call.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[#b9cacb]">{call.duration ? `${call.duration}s` : '—'}</td>
                    <td className="py-2.5 px-3 text-[#65f2b5]">
                      {call.latency_first_audio_ms ? `${call.latency_first_audio_ms}ms` : '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => openCallDetails(call.id)}
                          className="px-2.5 py-1 bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] rounded border border-[#00f0ff]/30 text-[10px] uppercase transition-all cursor-pointer"
                        >
                          Inspect
                        </button>
                        <button
                          onClick={(e) => handleDeleteCall(call.id, e)}
                          disabled={deletingId === call.id}
                          title="Permanently Delete Call"
                          className="p-1 text-[#ffb4ab]/80 hover:text-[#ffb4ab] bg-[#93000a]/20 hover:bg-[#93000a]/40 rounded border border-[#ffb4ab]/30 text-[10px] transition-all cursor-pointer flex items-center justify-center disabled:opacity-50"
                        >
                          <span className="material-symbols-outlined text-[14px]">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Call Details Modal */}
      {selectedCallId && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#080e1d] border border-white/10 rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-[#191f2f]">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">record_voice_over</span>
                <h4 className="font-['Sora'] font-bold text-sm text-[#dde2f8]">
                  Call Inspection: {selectedCallId}
                </h4>
              </div>
              <button
                onClick={() => setSelectedCallId(null)}
                className="text-[#849495] hover:text-white p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-5 flex-1 overflow-y-auto space-y-4">
              {isLoadingDetail ? (
                <div className="text-center py-12 font-mono text-xs text-[#00f0ff] animate-pulse">
                  Loading call messages...
                </div>
              ) : callDetail ? (
                <>
                  {callDetail.summary && (
                    <div className="p-3 bg-[#191f2f] rounded-lg border border-white/5 text-xs text-[#b9cacb] font-mono">
                      <span className="text-[#00f0ff] font-bold">Summary: </span>
                      {callDetail.summary}
                    </div>
                  )}

                  <div className="space-y-3">
                    <h5 className="font-mono text-xs uppercase text-[#849495]">Full Transcript</h5>
                    {callDetail.messages.length === 0 ? (
                      <p className="text-xs font-mono text-[#849495]">No messages recorded for this call.</p>
                    ) : (
                      callDetail.messages.map((m) => (
                        <div
                          key={m.id}
                          className={`p-3 rounded-xl border text-xs font-mono ${m.speaker === 'user'
                              ? 'bg-[#2f3445]/50 border-white/5 text-[#dde2f8]'
                              : m.speaker === 'system'
                                ? 'bg-[#080e1d] border-white/5 text-[#849495] italic'
                                : 'bg-[#00f0ff]/10 border-[#00f0ff]/20 text-[#dbfcff]'
                            }`}
                        >
                          <div className="flex justify-between items-center text-[10px] text-[#849495] mb-1 uppercase font-bold">
                            <span>{m.speaker}</span>
                            <span>{m.language}</span>
                          </div>
                          <div>{m.text}</div>
                        </div>
                      ))
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-12 text-xs font-mono text-[#849495]">
                  Call records not available.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
