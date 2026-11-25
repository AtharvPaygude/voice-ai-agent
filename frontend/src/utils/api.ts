import type { AgentConfig } from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://aura-voice-backend-6tkj.onrender.com';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || API_BASE_URL.replace(/^http/, 'ws');

export async function fetchCurrentConfig(): Promise<AgentConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config/current`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch current config: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function updateConfigApi(config: AgentConfig): Promise<AgentConfig> {
  const response = await fetch(`${API_BASE_URL}/api/config/update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => '');
    throw new Error(`Failed to update config: ${response.status} ${response.statusText} ${errorBody}`);
  }

  return response.json();
}

export async function fetchPersonas() {
  const response = await fetch(`${API_BASE_URL}/api/config/personas`);
  if (!response.ok) throw new Error('Failed to fetch personas');
  return response.json();
}

export async function fetchSupportedLanguages() {
  const response = await fetch(`${API_BASE_URL}/api/config/languages`);
  if (!response.ok) throw new Error('Failed to fetch languages');
  return response.json();
}

export async function fetchBusinessProfiles(): Promise<import('../types').BusinessProfileRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/business`);
  if (!response.ok) throw new Error('Failed to fetch business profiles');
  return response.json();
}

export async function activateBusinessProfile(profileId: string) {
  const response = await fetch(`${API_BASE_URL}/api/business/${profileId}/activate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new Error(`Failed to activate business profile: ${response.status} ${errorText}`);
  }
  return response.json();
}

export async function createBusinessProfile(data: Partial<import('../types').BusinessProfileRecord>) {
  const response = await fetch(`${API_BASE_URL}/api/business`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new Error(`Failed to create business profile: ${response.status} ${errorText}`);
  }
  return response.json();
}

export async function fetchEscalations(): Promise<import('../types').EscalationRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/escalations/`);
  if (!response.ok) throw new Error('Failed to fetch escalations');
  return response.json();
}

export async function fetchEscalation(id: string): Promise<import('../types').EscalationRecord> {
  const response = await fetch(`${API_BASE_URL}/api/escalations/${id}`);
  if (!response.ok) throw new Error(`Failed to fetch escalation ${id}`);
  return response.json();
}

export async function updateEscalationStatus(id: string, status: string): Promise<import('../types').EscalationRecord> {
  const response = await fetch(`${API_BASE_URL}/api/escalations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) throw new Error(`Failed to update escalation status: ${response.status}`);
  return response.json();
}

export async function resendEscalation(id: string): Promise<{ status: string; email_status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/escalations/${id}/resend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error(`Failed to resend escalation: ${response.status}`);
  return response.json();
}
