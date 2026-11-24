export type OrbState = 
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'interrupted'
  | 'language_switch'
  | 'tool_action'
  | 'success'
  | 'error'
  | 'human_transfer';

export type CoreLanguage = 'en' | 'hi' | 'mr' | 'hinglish';
export type SupportedLanguage = CoreLanguage | string;

export interface BusinessConfig {
  name: string;
  industry: string;
  description?: string;
}

export interface AgentIdentity {
  name: string;
  role: string;
  personality: string;
}

export interface PolicyConfig {
  require_confirmation_for: string[];
  healthcare_safety: boolean;
  escalation_rules: string[];
}

export interface AgentConfig {
  business: BusinessConfig;
  agent: AgentIdentity;
  capabilities: string[];
  knowledge_base: string[];
  tools: string[];
  workflows: string[];
  permissions: Record<string, boolean>;
  policies: PolicyConfig;
  primary_language: string;
  auto_language_switch: boolean;
  persona: string;
  system_prompt: string;
  supported_languages: string[];
  tts_voice_map?: Record<string, string>;
  confidence_threshold?: number;
  stability_count?: number;
}

export interface BusinessProfileRecord {
  id: string;
  name: string;
  industry: string;
  description: string;
  offerings: Array<{ name: string; price?: string | number; details?: string; [key: string]: any }>;
  capabilities: string[];
  knowledge_base: string[];
  tools: string[];
  workflows: string[];
  permissions: Record<string, boolean>;
  policies: Record<string, any>;
  booking_unit_label: string;
  persona: string;
  speaking_style?: 'friendly' | 'professional' | 'empathetic';
  category?: string;
  address?: string;
  city?: string;
  contact_email?: string;
  contact_phone?: string;
  operating_hours?: Record<string, string>;
  specialties?: string[];
  practitioners?: Array<{ name: string; specialty: string; days?: string[] }>;
  faqs?: Array<{ question: string; answer: string }>;
  escalation?: Record<string, any>;
  created_at: string;
}

export interface EscalationRecord {
  id: string;
  call_id?: string;
  business_profile_id?: string;
  caller_name: string;
  caller_phone: string;
  caller_email?: string;
  language: string;
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  caller_intent: string;
  agent_attempts: string;
  summary: string;
  requested_action: string;
  issues?: Array<{ time: string; type: string; detail: string }>;
  user_confirmation?: 'pending' | 'accurate' | 'inaccurate';
  user_note?: string;
  email_status?: string;
  status: 'new' | 'sent' | 'acknowledged' | 'resolved' | 'failed' | 'pending';
  created_at: string;
  updated_at: string;
}

export type Escalation = EscalationRecord;

export interface AgentProfile {
  business: {
    name: string;
    industry: string;
    description?: string;
  };
  agent: {
    name: string;
    role: string;
    personality: string;
  };
  capabilities: string[];
  tools: string[];
  workflows: string[];
  knowledge_base?: string[];
  permissions?: Record<string, boolean>;
  policies?: PolicyConfig;
  primary_language?: string;
  auto_language_switch?: boolean;
  persona?: string;
  speaking_style?: 'friendly' | 'professional' | 'empathetic';
  system_prompt?: string;
  supported_languages?: string[];
}

export const ACTIVE_AGENT_PROFILE: AgentProfile = {
  business: { name: 'Aura AI', industry: 'Universal Voice AI' },
  agent: { name: 'Aura AI', role: 'Voice AI Agent', personality: 'Adaptive (Friendly / Professional / Empathetic)' },
  capabilities: ['Sales', 'Customer Support', 'Appointments', 'FAQ + RAG', 'Escalations'],
  tools: ['check_availability', 'book_appointment', 'create_ticket', 'create_lead', 'escalate_to_human'],
  workflows: ['General inquiry', 'Booking', 'Support', 'Human handoff'],
};

export interface LanguageCapabilityInfo {
  code: string;
  name: string;
  nativeName: string;
  region: string;
  stt: boolean;
  tts: boolean;
  llm: boolean;
  status: 'supported' | 'partially_supported' | 'experimental' | 'unavailable';
  defaultVoice?: string;
  flag: string;
  type?: string;
}

export interface LanguageInfo {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
  color: string;
}

export interface TranscriptMessage {
  id: string;
  speaker: 'user' | 'agent' | 'system';
  text: string;
  language: SupportedLanguage;
  confidence: number;
  timestamp: string;
  isCodeSwitch?: boolean;
  isInterrupted?: boolean;
}

export interface LanguageSwitchEvent {
  id: string;
  from: SupportedLanguage;
  to: SupportedLanguage;
  confidence: number;
  reason: string;
  timestamp: string;
}

export interface ToolAction {
  id: string;
  tool: string;
  parameters: Record<string, any>;
  result?: Record<string, any>;
  status: 'running' | 'success' | 'confirmation_required' | 'error';
  timestamp: string;
}

export interface CallMetrics {
  latencyMs: number;
  tokensPerSec: number;
  activeStreams: number;
  durationSeconds: number;
  leadScore: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentimentScore: number;
  intent: string;
}
