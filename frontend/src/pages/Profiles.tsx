import React, { useEffect, useState, useCallback } from 'react';
import { useConfigStore } from '../stores/configStore';
import { createBusinessProfile } from '../utils/api';
import type { BusinessProfileRecord } from '../types';

/* ─────────────────────────────────────────────────────────
   Industry options shared with Studio
───────────────────────────────────────────────────────── */
const INDUSTRY_OPTIONS = [
  'Doctor / Clinic',
  'Hotel',
  'Restaurant',
  'E-commerce',
  'Real Estate',
  'Education',
  'Service Business',
  'Legal',
  'Finance',
  'Other',
];

const CAPABILITY_OPTIONS = [
  'Sales', 'Customer Support', 'Appointment Booking',
  'Reservations', 'Order Tracking', 'Lead Qualification',
  'CRM', 'Ticket Creation', 'FAQ', 'RAG', 'Human Handoff',
];

const TOOL_OPTIONS = [
  'get_offering_price', 'get_offering_details', 'check_availability',
  'book_slot', 'confirm_slot', 'reschedule_slot', 'cancel_slot',
  'check_order', 'create_lead', 'create_ticket', 'send_email',
  'send_sms', 'get_customer', 'transfer_to_human',
];

const WORKFLOW_OPTIONS = [
  'General inquiry', 'Booking', 'Support', 'Human handoff',
  'Lead qualification', 'Follow-up', 'Reservation', 'Scheduling',
];

/* ─────────────────────────────────────────────────────────
   Industry badge colour
───────────────────────────────────────────────────────── */
const industryColor = (industry: string) => {
  const map: Record<string, string> = {
    'Doctor / Clinic': 'text-[#65f2b5] bg-[#65f2b5]/15 border-[#65f2b5]/30',
    'Hotel':           'text-[#fbbf24] bg-[#fbbf24]/15 border-[#fbbf24]/30',
    'Restaurant':      'text-[#f87171] bg-[#f87171]/15 border-[#f87171]/30',
    'E-commerce':      'text-[#60a5fa] bg-[#60a5fa]/15 border-[#60a5fa]/30',
    'Real Estate':     'text-[#a78bfa] bg-[#a78bfa]/15 border-[#a78bfa]/30',
    'Education':       'text-[#34d399] bg-[#34d399]/15 border-[#34d399]/30',
    'Service Business':'text-[#00f0ff] bg-[#00f0ff]/15 border-[#00f0ff]/30',
    'Legal':           'text-[#d0bcff] bg-[#d0bcff]/15 border-[#d0bcff]/30',
    'Finance':         'text-[#fb923c] bg-[#fb923c]/15 border-[#fb923c]/30',
  };
  return map[industry] || 'text-[#b9cacb] bg-white/5 border-white/10';
};

/* ─────────────────────────────────────────────────────────
   Create Profile Modal
───────────────────────────────────────────────────────── */
interface CreateModalProps {
  onClose: () => void;
  onCreated: () => void;
}

const CreateProfileModal: React.FC<CreateModalProps> = ({ onClose, onCreated }) => {
  const [form, setForm] = useState({
    name: '',
    industry: 'Service Business',
    description: '',
    persona: 'professional',
    booking_unit_label: 'appointment',
  });
  const [selectedCaps, setSelectedCaps] = useState<string[]>(['Sales', 'Customer Support', 'Human Handoff']);
  const [selectedTools, setSelectedTools] = useState<string[]>(['check_availability', 'book_slot', 'transfer_to_human']);
  const [selectedWorkflows, setSelectedWorkflows] = useState<string[]>(['General inquiry', 'Booking', 'Support', 'Human handoff']);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (_list: string[], setList: React.Dispatch<React.SetStateAction<string[]>>, val: string) => {
    setList((prev) => prev.includes(val) ? prev.filter((v) => v !== val) : [...prev, val]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) { setError('Business name is required.'); return; }
    setSaving(true);
    setError(null);
    try {
      await createBusinessProfile({
        ...form,
        capabilities: selectedCaps,
        tools: selectedTools,
        workflows: selectedWorkflows,
        knowledge_base: ['business_info', 'offerings', 'policies'],
        permissions: { read_knowledge: true, execute_tools: true, transfer_to_human: true },
        policies: {
          require_confirmation_for: ['cancellation', 'refund'],
          healthcare_safety: form.industry === 'Doctor / Clinic',
          escalation_rules: ['high-risk request', 'caller asks for a human'],
        },
      } as any);
      onCreated();
    } catch (err: any) {
      setError(err?.message || 'Failed to create profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#0d1322] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/5">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-[#00f0ff]">New Business Profile</p>
            <h2 className="font-['Sora'] font-bold text-lg text-[#dde2f8] mt-0.5">Configure Agent Identity</h2>
          </div>
          <button onClick={onClose} className="text-[#849495] hover:text-white cursor-pointer transition-colors">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5">
          {error && (
            <div className="bg-red-500/15 border border-red-500/40 text-red-300 text-xs font-mono px-4 py-2 rounded-lg flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">error</span>
              {error}
            </div>
          )}

          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1.5">Business Name *</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. City Wellness Clinic"
                className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] placeholder:text-[#849495]"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1.5">Industry</label>
              <select
                value={form.industry}
                onChange={(e) => setForm({ ...form, industry: e.target.value })}
                className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] appearance-none cursor-pointer"
              >
                {INDUSTRY_OPTIONS.map((i) => <option key={i}>{i}</option>)}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1.5">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Brief description of the business and its main offerings..."
                rows={2}
                className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] resize-none placeholder:text-[#849495]"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1.5">Agent Persona</label>
              <select
                value={form.persona}
                onChange={(e) => setForm({ ...form, persona: e.target.value })}
                className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] appearance-none cursor-pointer"
              >
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="energetic">Energetic</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-1.5">Booking Unit Label</label>
              <input
                value={form.booking_unit_label}
                onChange={(e) => setForm({ ...form, booking_unit_label: e.target.value })}
                placeholder="e.g. appointment, slot, table"
                className="w-full bg-[#080e1d] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] placeholder:text-[#849495]"
              />
            </div>
          </div>

          {/* Capabilities */}
          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Capabilities</label>
            <div className="flex flex-wrap gap-2">
              {CAPABILITY_OPTIONS.map((cap) => {
                const active = selectedCaps.includes(cap);
                return (
                  <button
                    key={cap} type="button"
                    onClick={() => toggle(selectedCaps, setSelectedCaps, cap)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active ? 'bg-[#65f2b5]/15 border-[#65f2b5]/40 text-[#65f2b5]' : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >{cap}</button>
                );
              })}
            </div>
          </div>

          {/* Tools */}
          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Tools</label>
            <div className="flex flex-wrap gap-2">
              {TOOL_OPTIONS.map((tool) => {
                const active = selectedTools.includes(tool);
                return (
                  <button
                    key={tool} type="button"
                    onClick={() => toggle(selectedTools, setSelectedTools, tool)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active ? 'bg-[#f59e0b]/15 border-[#f59e0b]/40 text-[#fbbf24]' : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >{tool}</button>
                );
              })}
            </div>
          </div>

          {/* Workflows */}
          <div>
            <label className="block text-[10px] font-mono uppercase text-[#b9cacb] mb-2">Workflows</label>
            <div className="flex flex-wrap gap-2">
              {WORKFLOW_OPTIONS.map((wf) => {
                const active = selectedWorkflows.includes(wf);
                return (
                  <button
                    key={wf} type="button"
                    onClick={() => toggle(selectedWorkflows, setSelectedWorkflows, wf)}
                    className={`px-2.5 py-1.5 rounded-full border text-[10px] font-mono transition-all cursor-pointer ${
                      active ? 'bg-[#571bc1]/15 border-[#571bc1]/40 text-[#d0bcff]' : 'bg-[#080e1d] border-white/10 text-[#b9cacb]'
                    }`}
                  >{wf}</button>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2 border-t border-white/5">
            <button
              type="button" onClick={onClose}
              className="px-4 py-2 text-xs font-mono text-[#b9cacb] hover:text-[#dde2f8] border border-white/10 rounded-lg hover:bg-white/5 cursor-pointer transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 text-xs font-bold bg-[#00f0ff] text-[#00363a] rounded-lg hover:bg-[#7df4ff] shadow-[0_0_15px_rgba(0,240,255,0.3)] cursor-pointer disabled:opacity-50 transition-all flex items-center gap-2"
            >
              {saving ? (
                <><span className="material-symbols-outlined text-[14px] animate-spin">sync</span> Creating...</>
              ) : (
                <><span className="material-symbols-outlined text-[14px]">add_circle</span> Create Profile</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

/* ─────────────────────────────────────────────────────────
   Profile Card
───────────────────────────────────────────────────────── */
interface ProfileCardProps {
  profile: BusinessProfileRecord;
  isActive: boolean;
  isActivating: boolean;
  onActivate: (id: string) => void;
}

const ProfileCard: React.FC<ProfileCardProps> = ({ profile, isActive, isActivating, onActivate }) => {
  const createdDate = new Date(profile.created_at).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });

  return (
    <div
      className={`relative glass-panel rounded-xl p-5 transition-all duration-300 border-2 ${
        isActive
          ? 'border-[#00f0ff]/70 shadow-[0_0_25px_rgba(0,240,255,0.18)]'
          : 'border-transparent hover:border-white/15'
      }`}
    >
      {/* Active badge */}
      {isActive && (
        <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-[#00f0ff]/15 border border-[#00f0ff]/40 text-[#00f0ff] text-[10px] font-mono px-2 py-1 rounded-full">
          <div className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] animate-pulse" />
          ACTIVE
        </div>
      )}

      {/* Card header */}
      <div className="mb-3 pr-16">
        <p className="font-['Sora'] font-semibold text-sm text-[#dde2f8] leading-snug">{profile.name}</p>
        <p className="text-[10px] font-mono text-[#849495] mt-0.5">{createdDate}</p>
      </div>

      {/* Industry badge */}
      <span className={`inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded border mb-3 ${industryColor(profile.industry)}`}>
        {profile.industry}
      </span>

      {/* Description */}
      {profile.description && (
        <p className="text-[11px] text-[#b9cacb] leading-relaxed mb-3 line-clamp-2">{profile.description}</p>
      )}

      {/* Tags row */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {(profile.capabilities || []).slice(0, 4).map((cap) => (
          <span key={cap} className="text-[9px] font-mono text-[#65f2b5] bg-[#65f2b5]/10 border border-[#65f2b5]/20 px-1.5 py-0.5 rounded">
            {cap}
          </span>
        ))}
        {(profile.capabilities || []).length > 4 && (
          <span className="text-[9px] font-mono text-[#849495] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded">
            +{(profile.capabilities || []).length - 4} more
          </span>
        )}
      </div>

      {/* Tools count */}
      <div className="flex items-center gap-3 text-[10px] font-mono text-[#849495] mb-4">
        <div className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[13px] text-[#fbbf24]">build</span>
          {(profile.tools || []).length} tools
        </div>
        <div className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[13px] text-[#d0bcff]">account_tree</span>
          {(profile.workflows || []).length} workflows
        </div>
        <div className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[13px] text-[#60a5fa]">psychology</span>
          {profile.persona}
        </div>
      </div>

      {/* Activate button */}
      {isActive ? (
        <div className="w-full py-2 text-xs font-mono text-center text-[#00f0ff] border border-[#00f0ff]/30 rounded-lg bg-[#00f0ff]/5">
          <span className="material-symbols-outlined text-[14px] align-text-bottom mr-1">check_circle</span>
          Currently Active
        </div>
      ) : (
        <button
          onClick={() => onActivate(profile.id)}
          disabled={isActivating}
          className="w-full py-2 text-xs font-semibold border border-[#00f0ff]/40 text-[#00f0ff] rounded-lg hover:bg-[#00f0ff]/10 transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5"
        >
          {isActivating ? (
            <><span className="material-symbols-outlined text-[14px] animate-spin">sync</span> Activating...</>
          ) : (
            <><span className="material-symbols-outlined text-[14px]">rocket_launch</span> Activate Profile</>
          )}
        </button>
      )}
    </div>
  );
};

/* ─────────────────────────────────────────────────────────
   Main Profiles Page
───────────────────────────────────────────────────────── */
export const Profiles: React.FC = () => {
  const profiles       = useConfigStore((s) => s.profiles);
  const selectedId     = useConfigStore((s) => s.selectedProfileId);
  const isActivating   = useConfigStore((s) => s.isActivating);
  const loadProfiles   = useConfigStore((s) => s.loadProfiles);
  const loadConfig     = useConfigStore((s) => s.loadConfig);
  const selectAndActivateProfile = useConfigStore((s) => s.selectAndActivateProfile);

  const [showCreate, setShowCreate]   = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [search, setSearch] = useState('');
  const [activatingId, setActivatingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    await loadConfig();
    await loadProfiles();
  }, [loadConfig, loadProfiles]);

  useEffect(() => { refresh(); }, [refresh]);

  const handleActivate = async (id: string) => {
    setActivatingId(id);
    const ok = await selectAndActivateProfile(id);
    setActivatingId(null);
    if (ok) {
      setNotification({ type: 'success', message: 'Profile activated! All calls will now use this business context.' });
      setTimeout(() => setNotification(null), 4000);
    } else {
      setNotification({ type: 'error', message: 'Failed to activate profile. Please try again.' });
    }
  };

  const handleCreated = async () => {
    setShowCreate(false);
    await refresh();
    setNotification({ type: 'success', message: 'Business profile created successfully!' });
    setTimeout(() => setNotification(null), 3500);
  };

  const filtered = profiles.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.industry.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Notification */}
      {notification && (
        <div
          className={`flex items-center justify-between px-4 py-3 rounded-lg border text-xs font-mono animate-fadeIn ${
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
          <button onClick={() => setNotification(null)} className="text-white/60 hover:text-white cursor-pointer">✕</button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="font-['Sora'] font-bold text-2xl text-[#dde2f8] mb-1">Business Profiles</h1>
          <p className="text-sm text-[#b9cacb]">
            Each profile configures the agent's identity, capabilities and tools for a specific business context.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 bg-[#00f0ff] text-[#00363a] font-bold text-xs rounded-lg shadow-[0_0_15px_rgba(0,240,255,0.35)] hover:bg-[#7df4ff] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          New Profile
        </button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Profiles', value: profiles.length, icon: 'domain', color: 'text-[#00f0ff]' },
          { label: 'Active Profile', value: profiles.find(p => p.id === selectedId)?.name || '—', icon: 'bolt', color: 'text-[#65f2b5]', small: true },
          { label: 'Industries', value: new Set(profiles.map(p => p.industry)).size, icon: 'category', color: 'text-[#fbbf24]' },
          { label: 'Total Tools', value: profiles.reduce((s, p) => s + (p.tools?.length ?? 0), 0), icon: 'build', color: 'text-[#d0bcff]' },
        ].map(({ label, value, icon, color, small }) => (
          <div key={label} className="glass-panel rounded-xl p-4 border border-white/5">
            <div className="flex items-center gap-2 mb-1">
              <span className={`material-symbols-outlined text-[16px] ${color}`}>{icon}</span>
              <p className="text-[10px] font-mono uppercase text-[#849495]">{label}</p>
            </div>
            <p className={`font-['Sora'] font-bold ${small ? 'text-sm' : 'text-2xl'} ${color} truncate`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#849495] text-[18px]">search</span>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search profiles by name or industry…"
          className="w-full bg-[#080e1d] border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#dde2f8] focus:outline-none focus:border-[#00f0ff] placeholder:text-[#849495]"
        />
      </div>

      {/* Profile grid */}
      {filtered.length === 0 ? (
        <div className="glass-panel rounded-xl p-12 text-center border border-white/5">
          <span className="material-symbols-outlined text-[48px] text-[#849495] mb-3 block">domain_disabled</span>
          <p className="font-['Sora'] font-semibold text-[#dde2f8] mb-1">
            {profiles.length === 0 ? 'No profiles yet' : 'No profiles match your search'}
          </p>
          <p className="text-xs font-mono text-[#849495] mb-5">
            {profiles.length === 0
              ? 'Create your first business profile to configure the AI agent for a specific use case.'
              : 'Try a different search term.'}
          </p>
          {profiles.length === 0 && (
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#00f0ff]/10 border border-[#00f0ff]/40 text-[#00f0ff] text-xs font-mono rounded-lg hover:bg-[#00f0ff]/20 cursor-pointer transition-all"
            >
              <span className="material-symbols-outlined text-[16px]">add_circle</span>
              Create First Profile
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((profile) => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              isActive={profile.id === selectedId}
              isActivating={activatingId === profile.id && isActivating}
              onActivate={handleActivate}
            />
          ))}
        </div>
      )}

      {/* Active profile summary */}
      {selectedId && (
        <div className="glass-panel rounded-xl p-5 border border-[#00f0ff]/20 bg-[#00f0ff]/5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[#00f0ff]/15 border border-[#00f0ff]/30 flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">done_all</span>
            </div>
            <div>
              <p className="text-xs font-mono text-[#00f0ff] font-semibold">Active Profile Synced</p>
              <p className="text-[11px] text-[#b9cacb] font-mono mt-0.5">
                All new calls will load <strong className="text-[#dde2f8]">{profiles.find(p => p.id === selectedId)?.name}</strong>'s capabilities, tools, and workflows into the agent runtime.
                Go to <strong className="text-[#dde2f8]">Agent Studio</strong> to fine-tune the system prompt or language settings.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Create modal */}
      {showCreate && <CreateProfileModal onClose={() => setShowCreate(false)} onCreated={handleCreated} />}
    </div>
  );
};
