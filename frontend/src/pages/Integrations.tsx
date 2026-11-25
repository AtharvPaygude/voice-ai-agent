import React, { useState, useEffect } from 'react';
import { API_BASE_URL as API_BASE } from '../utils/api';

interface ServiceStatus {
  name: string;
  status: 'connected' | 'not_configured' | 'error' | 'configured';
  detail?: string;
  [key: string]: any;
}

export const Integrations: React.FC = () => {
  const [statuses, setStatuses] = useState<Record<string, ServiceStatus>>({});
  const [testingService, setTestingService] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { status: string; detail: string; at: string }>>({});
  const [, setIsLoading] = useState(true);

  const fetchStatuses = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/config/integrations/status`);
      if (res.ok) {
        const data = await res.json();
        setStatuses(data);
      }
    } catch (err) {
      console.error('Failed to load integration statuses:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatuses();
  }, []);

  const handleTest = async (service: string) => {
    setTestingService(service);
    try {
      const res = await fetch(`${API_BASE}/api/config/integrations/test/${service}`, {
        method: 'POST',
      });
      const data = await res.json();
      setTestResults((prev) => ({
        ...prev,
        [service]: {
          status: data.status,
          detail: data.detail || data.message || 'Check complete',
          at: new Date().toLocaleTimeString(),
        },
      }));
    } catch (err: any) {
      setTestResults((prev) => ({
        ...prev,
        [service]: {
          status: 'error',
          detail: err.message || 'Connection test failed',
          at: new Date().toLocaleTimeString(),
        },
      }));
    } finally {
      setTestingService(null);
    }
  };

  const integrationCards = [
    {
      id: 'email',
      title: 'Email Delivery (SMTP)',
      icon: 'mail',
      desc: 'Transmits appointment confirmations, cancellations, and urgent human escalation notices.',
      status: statuses.email?.status || 'not_configured',
      envVars: ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_FROM'],
      info: statuses.email?.host ? `Host: ${statuses.email.host} | From: ${statuses.email.from_address}` : 'No SMTP server set.',
    },
    {
      id: 'crm',
      title: 'CRM & Webhook Dispatch',
      icon: 'webhook',
      desc: 'Dispatches real-time booking, lead qualification, and ticket payloads to your external CRM or automation webhook.',
      status: statuses.crm?.status || 'not_configured',
      envVars: ['CRM_WEBHOOK_URL', 'CRM_WEBHOOK_SECRET'],
      info: statuses.crm?.url ? `Target: ${statuses.crm.url}` : 'No Webhook endpoint set.',
    },
    {
      id: 'telephony',
      title: 'Telephony & SIP Gateway',
      icon: 'phone_in_talk',
      desc: 'Connects inbound/outbound voice calls via Twilio or Exotel telephony trunks.',
      status: statuses.telephony?.status || 'not_configured',
      envVars: ['TELEPHONY_PROVIDER', 'TELEPHONY_ACCOUNT_SID', 'TELEPHONY_AUTH_TOKEN', 'TELEPHONY_PHONE_NUMBER'],
      info: statuses.telephony?.provider ? `Provider: ${statuses.telephony.provider} | Number: ${statuses.telephony.phone_number}` : 'Credentials not configured.',
    },
    {
      id: 'calendar',
      title: 'Scheduling Engine',
      icon: 'calendar_month',
      desc: 'Native PostgreSQL database scheduling engine with double-booking prevention and practitioner allocation.',
      status: 'connected',
      envVars: ['DATABASE_URL'],
      info: 'Supabase PostgreSQL transactional calendar active.',
    },
    {
      id: 'llm',
      title: 'AI LLM Providers',
      icon: 'psychology',
      desc: 'Streaming sentence pipeline with fallback cascading between Ollama and Google Gemini.',
      status: statuses.llm?.gemini_status === 'configured' || statuses.llm?.ollama_status === 'configured' ? 'connected' : 'not_configured',
      envVars: ['LLM_PRIMARY', 'GEMINI_API_KEY', 'GEMINI_MODEL', 'OLLAMA_BASE_URL', 'OLLAMA_MODEL'],
      info: `Primary: ${statuses.llm?.primary || 'ollama'} | Gemini: ${statuses.llm?.gemini_status || 'missing key'}`,
    },
  ];

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="font-['Sora'] font-bold text-2xl text-[#dde2f8] tracking-tight mb-1">
            External Integrations & Services
          </h2>
          <p className="text-sm text-[#b9cacb]">
            Truthful configuration state and live connectivity testing for SMTP, CRM, Telephony, and LLM backends.
          </p>
        </div>
        <button
          onClick={fetchStatuses}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#191f2f] hover:bg-white/5 border border-white/10 text-xs font-mono text-[#00f0ff] cursor-pointer"
        >
          <span className="material-symbols-outlined text-[16px]">refresh</span>
          Refresh Status
        </button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {integrationCards.map((card) => {
          const test = testResults[card.id];
          const isConnected = card.status === 'connected';

          return (
            <div
              key={card.id}
              className="glass-panel rounded-xl p-5 gradient-border-top flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-[#191f2f] border border-white/5 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">{card.icon}</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold border ${
                      isConnected
                        ? 'text-[#65f2b5] bg-[#65f2b5]/10 border-[#65f2b5]/30'
                        : 'text-[#ffb4ab] bg-[#93000a]/20 border-[#ffb4ab]/30'
                    }`}
                  >
                    {isConnected ? 'Configured' : 'Unconfigured'}
                  </span>
                </div>

                <h3 className="font-['Sora'] font-semibold text-base text-[#dde2f8] mb-1">
                  {card.title}
                </h3>
                <p className="text-xs text-[#b9cacb] leading-relaxed mb-3">
                  {card.desc}
                </p>

                <div className="p-2.5 rounded-lg bg-[#080e1d] border border-white/5 text-[11px] font-mono text-[#dde2f8] mb-3">
                  {card.info}
                </div>

                {!isConnected && (
                  <div className="mb-3">
                    <span className="text-[10px] font-mono text-[#849495] uppercase block mb-1">Required Environment Variables:</span>
                    <div className="flex flex-wrap gap-1">
                      {card.envVars.map((v) => (
                        <span key={v} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[#ffb4ab]">
                          {v}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {test && (
                  <div
                    className={`p-2 rounded-lg text-[10px] font-mono mb-3 border ${
                      test.status === 'connected' || test.status === 'ok'
                        ? 'bg-[#65f2b5]/10 border-[#65f2b5]/30 text-[#65f2b5]'
                        : test.status === 'not_configured'
                        ? 'bg-[#f59e0b]/10 border-[#f59e0b]/30 text-[#f59e0b]'
                        : 'bg-red-500/10 border-red-500/30 text-red-300'
                    }`}
                  >
                    <div className="flex justify-between items-center font-bold">
                      <span>Test Result: {test.status.toUpperCase()}</span>
                      <span className="text-[9px] opacity-75">{test.at}</span>
                    </div>
                    <div className="mt-0.5">{test.detail}</div>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                <button
                  onClick={() => handleTest(card.id)}
                  disabled={testingService === card.id}
                  className="px-3 py-1.5 bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] rounded-lg border border-[#00f0ff]/30 text-xs font-mono transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {testingService === card.id ? (
                    <>
                      <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
                      Testing...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[14px]">send</span>
                      Test Connection
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
