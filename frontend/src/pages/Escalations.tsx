import React, { useEffect, useState } from 'react';
import type { EscalationRecord } from '../types';
import { fetchEscalations, updateEscalationStatus, resendEscalation } from '../utils/api';

export const Escalations: React.FC = () => {
  const [escalations, setEscalations] = useState<EscalationRecord[]>([]);
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [resendingId, setResendingId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const data = await fetchEscalations();
      setEscalations(data);
      if (selectedEscalation) {
        const updated = data.find((e) => e.id === selectedEscalation.id);
        if (updated) setSelectedEscalation(updated);
      }
    } catch (err) {
      console.error('Failed to load escalations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      const updated = await updateEscalationStatus(id, newStatus);
      setEscalations((prev) => prev.map((e) => (e.id === id ? updated : e)));
      if (selectedEscalation?.id === id) {
        setSelectedEscalation(updated);
      }
      setActionMessage(`Status updated to ${newStatus}`);
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleResend = async (id: string) => {
    setResendingId(id);
    try {
      const res = await resendEscalation(id);
      setActionMessage(`Email resent: ${res.email_status}`);
      await loadData();
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err) {
      console.error('Failed to resend escalation email:', err);
      setActionMessage('Failed to resend email');
    } finally {
      setResendingId(null);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold bg-[#93000a]/40 text-[#ffb4ab] border border-[#ffb4ab]/30">Urgent</span>;
      case 'high':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold bg-[#ffb4ab]/20 text-[#ffb4ab] border border-[#ffb4ab]/30">High</span>;
      case 'medium':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30">Medium</span>;
      default:
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase bg-white/10 text-[#b9cacb]">Low</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'resolved':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20">Resolved</span>;
      case 'acknowledged':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase text-[#00f0ff] bg-[#00f0ff]/10 border border-[#00f0ff]/20">Acknowledged</span>;
      case 'sent':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase text-[#d0bcff] bg-[#d0bcff]/10 border border-[#d0bcff]/20">Sent</span>;
      default:
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase text-[#ffb4ab] bg-[#ffb4ab]/10 border border-[#ffb4ab]/20">New</span>;
    }
  };

  const getConfirmationBadge = (conf?: string) => {
    switch (conf) {
      case 'accurate':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20">✓ Verified</span>;
      case 'inaccurate':
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded text-[#ffb4ab] bg-[#ffb4ab]/10 border border-[#ffb4ab]/20">✗ Disputed</span>;
      default:
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded text-[#849495] bg-white/5 border border-white/10">Pending</span>;
    }
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-['Sora'] text-2xl font-bold text-[#dde2f8]">Escalation & Issue Reports</h1>
          <p className="text-xs font-mono text-[#849495] mt-1">
            Real-time supervisor triage, customer validation status, and audit trail
          </p>
        </div>
        <div className="flex items-center gap-3">
          {actionMessage && (
            <span className="text-xs font-mono text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-3 py-1.5 rounded-lg animate-fade-in">
              {actionMessage}
            </span>
          )}
          <button
            onClick={loadData}
            className="px-3 py-1.5 bg-[#191f2f] hover:bg-[#2f3445] text-[#00f0ff] font-mono text-xs rounded-lg border border-white/10 flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Table of Escalations (8 cols) */}
        <div className={`glass-panel rounded-xl overflow-hidden flex flex-col ${selectedEscalation ? 'lg:col-span-7' : 'lg:col-span-12'}`}>
          <div className="p-4 border-b border-white/10 flex items-center justify-between bg-[#080e1d]/50">
            <span className="font-mono text-xs uppercase tracking-wider text-[#b9cacb]">
              Logged Escalations ({escalations.length})
            </span>
            <span className="text-[10px] font-mono text-[#849495]">Auto-refreshes every 15s</span>
          </div>

          <div className="overflow-auto flex-1">
            {loading ? (
              <div className="p-8 text-center font-mono text-xs text-[#849495]">Loading escalation records...</div>
            ) : escalations.length === 0 ? (
              <div className="p-12 text-center">
                <span className="material-symbols-outlined text-[#65f2b5] text-[36px] mb-2">check_circle</span>
                <p className="font-['Sora'] text-sm text-[#dde2f8]">No active escalations</p>
                <p className="font-mono text-xs text-[#849495] mt-1">All caller requests handled automatically without incident.</p>
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10 bg-[#080e1d]/30 text-[10px] font-mono uppercase text-[#849495]">
                    <th className="p-3">Ref ID</th>
                    <th className="p-3">Caller</th>
                    <th className="p-3">Reason</th>
                    <th className="p-3">Priority</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Email</th>
                    <th className="p-3">Caller Confirm</th>
                    <th className="p-3">Logged</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono text-xs">
                  {escalations.map((esc) => (
                    <tr
                      key={esc.id}
                      onClick={() => setSelectedEscalation(esc)}
                      className={`hover:bg-[#00f0ff]/5 cursor-pointer transition-all ${
                        selectedEscalation?.id === esc.id ? 'bg-[#00f0ff]/10 border-l-2 border-[#00f0ff]' : ''
                      }`}
                    >
                      <td className="p-3 text-[#00f0ff] font-semibold">{esc.id.slice(0, 12)}</td>
                      <td className="p-3 text-[#dde2f8]">
                        <div>{esc.caller_name || 'Caller'}</div>
                        <div className="text-[10px] text-[#849495]">{esc.caller_phone || esc.caller_email || 'No contact'}</div>
                      </td>
                      <td className="p-3 text-[#b9cacb] capitalize">{esc.reason.replace(/_/g, ' ')}</td>
                      <td className="p-3">{getPriorityBadge(esc.priority)}</td>
                      <td className="p-3">{getStatusBadge(esc.status)}</td>
                      <td className="p-3 text-[10px] text-[#849495]">{esc.email_status || 'not_configured'}</td>
                      <td className="p-3">{getConfirmationBadge(esc.user_confirmation)}</td>
                      <td className="p-3 text-[10px] text-[#849495]">
                        {esc.created_at ? new Date(esc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Detail Side Panel (5 cols) */}
        {selectedEscalation && (
          <div className="lg:col-span-5 glass-panel rounded-xl p-5 flex flex-col gap-4 overflow-auto border border-[#00f0ff]/20">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-[#00f0ff]">Escalation Detail</p>
                <h3 className="font-['Sora'] font-semibold text-lg text-[#dde2f8] mt-1">{selectedEscalation.id}</h3>
              </div>
              <button
                onClick={() => setSelectedEscalation(null)}
                className="p-1 text-[#849495] hover:text-[#dde2f8]"
                title="Close Panel"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            {/* Status & Priority */}
            <div className="flex flex-wrap gap-2 items-center">
              {getPriorityBadge(selectedEscalation.priority)}
              {getStatusBadge(selectedEscalation.status)}
              {getConfirmationBadge(selectedEscalation.user_confirmation)}
            </div>

            {/* Caller Info */}
            <div className="bg-[#080e1d] rounded-lg p-3 border border-white/5 font-mono text-xs space-y-1">
              <div className="text-[#849495] uppercase text-[10px]">Caller Information</div>
              <div className="text-[#dde2f8] font-bold">{selectedEscalation.caller_name}</div>
              <div className="text-[#b9cacb]">Phone: {selectedEscalation.caller_phone || 'None provided'}</div>
              <div className="text-[#b9cacb]">Email: {selectedEscalation.caller_email || 'None provided'}</div>
              <div className="text-[#849495] text-[10px]">Language: {selectedEscalation.language}</div>
            </div>

            {/* Summary */}
            <div className="bg-[#080e1d] rounded-lg p-3 border border-white/5 text-xs space-y-1">
              <div className="font-mono text-[#849495] uppercase text-[10px]">Summary & Root Cause</div>
              <p className="text-[#dde2f8] leading-relaxed">{selectedEscalation.summary}</p>
            </div>

            {/* Caller Intent & Agent Attempts */}
            <div className="grid grid-cols-1 gap-2 text-xs">
              <div className="bg-[#080e1d] rounded-lg p-3 border border-white/5">
                <span className="font-mono text-[#849495] uppercase text-[10px] block mb-1">Caller Intent</span>
                <span className="text-[#dde2f8]">{selectedEscalation.caller_intent || 'General inquiry'}</span>
              </div>
              <div className="bg-[#080e1d] rounded-lg p-3 border border-white/5">
                <span className="font-mono text-[#849495] uppercase text-[10px] block mb-1">Agent Actions Taken</span>
                <span className="text-[#b9cacb] font-mono text-[11px]">{selectedEscalation.agent_attempts || 'Conversation automated'}</span>
              </div>
            </div>

            {/* Operational Issues Log */}
            {selectedEscalation.issues && selectedEscalation.issues.length > 0 && (
              <div className="bg-[#080e1d] rounded-lg p-3 border border-white/5 text-xs">
                <span className="font-mono text-[#849495] uppercase text-[10px] block mb-2">Tracked Turn Incidents</span>
                <div className="space-y-1 font-mono text-[11px]">
                  {selectedEscalation.issues.map((iss, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-[#ffb4ab]">
                      <span className="material-symbols-outlined text-[14px]">report_problem</span>
                      <span className="font-bold uppercase text-[10px]">{iss.type}:</span>
                      <span className="text-[#b9cacb]">{iss.detail || 'Triggered'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Caller Note if any */}
            {selectedEscalation.user_note && (
              <div className="bg-[#080e1d] rounded-lg p-3 border border-[#65f2b5]/20 text-xs">
                <span className="font-mono text-[#65f2b5] uppercase text-[10px] block mb-1">Caller Feedback Note</span>
                <p className="text-[#dde2f8] italic">"{selectedEscalation.user_note}"</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-auto pt-4 border-t border-white/10 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-[#849495] uppercase">Set Status:</span>
                {(['acknowledged', 'resolved'] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => handleStatusChange(selectedEscalation.id, st)}
                    className="px-2.5 py-1 bg-[#191f2f] hover:bg-[#2f3445] text-[#dde2f8] font-mono text-[10px] rounded uppercase border border-white/10 transition-all cursor-pointer"
                  >
                    {st}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleResend(selectedEscalation.id)}
                  disabled={resendingId === selectedEscalation.id}
                  className="w-full px-3 py-2 bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] font-mono text-xs rounded-lg border border-[#00f0ff]/30 flex items-center justify-center gap-2 transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[16px]">send</span>
                  {resendingId === selectedEscalation.id ? 'Resending Email...' : 'Resend Issue Email to Caller'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Escalations;
