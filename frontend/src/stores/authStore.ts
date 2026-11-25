/**
 * authStore.ts — Zustand store for authentication state.
 *
 * Handles login, register, logout, token persistence (localStorage),
 * and auto-restoring session on app boot via /api/auth/me.
 */
import { create } from 'zustand';
import { API_BASE_URL as API } from '../utils/api';

export type UserRole = 'admin' | 'customer';

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  business_profile_id: string | null;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: UserRole, businessProfileId?: string) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
  clearError: () => void;
}

const TOKEN_KEY = 'aura_session_token';

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem(TOKEN_KEY),
  loading: false,
  error: null,

  clearError: () => set({ error: null }),

  restoreSession: async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;
    try {
      set({ loading: true });
      const res = await fetch(`${API}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const user: AuthUser = await res.json();
        set({ user, token, loading: false });
      } else {
        // Token invalid/expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        set({ user: null, token: null, loading: false });
      }
    } catch {
      set({ loading: false });
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(err.detail || 'Login failed');
      }
      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.token);
      set({ user: data.user, token: data.token, loading: false, error: null });
    } catch (e: any) {
      set({ loading: false, error: e.message || 'Login failed' });
      throw e;
    }
  },

  register: async (email, password, fullName, role, businessProfileId) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          role,
          business_profile_id: businessProfileId || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
        throw new Error(err.detail || 'Registration failed');
      }
      // Auto-login after successful registration
      await get().login(email, password);
    } catch (e: any) {
      set({ loading: false, error: e.message || 'Registration failed' });
      throw e;
    }
  },

  logout: async () => {
    const token = get().token;
    if (token) {
      try {
        await fetch(`${API}/api/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // Ignore network errors on logout
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    set({ user: null, token: null, error: null });
  },
}));
