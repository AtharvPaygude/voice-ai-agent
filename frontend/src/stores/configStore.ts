import { create } from 'zustand';
import type { AgentConfig, BusinessProfileRecord } from '../types';
import { fetchCurrentConfig, updateConfigApi, fetchBusinessProfiles, activateBusinessProfile } from '../utils/api';
import { useCallStore } from './callStore';

interface ConfigStoreState {
  config: AgentConfig | null;
  profiles: BusinessProfileRecord[];
  selectedProfileId: string | null;
  isLoading: boolean;
  isSaving: boolean;
  isActivating: boolean;
  error: string | null;
  lastSavedAt: string | null;

  // Actions
  loadConfig: () => Promise<AgentConfig | null>;
  saveConfig: (newConfig: AgentConfig) => Promise<boolean>;
  loadProfiles: () => Promise<BusinessProfileRecord[]>;
  selectAndActivateProfile: (profileId: string) => Promise<boolean>;
  setLocalConfig: (config: AgentConfig) => void;
  clearError: () => void;
}

export const useConfigStore = create<ConfigStoreState>((set, get) => ({
  config: null,
  profiles: [],
  selectedProfileId: null,
  isLoading: false,
  isSaving: false,
  isActivating: false,
  error: null,
  lastSavedAt: null,

  loadConfig: async () => {
    set({ isLoading: true, error: null });
    try {
      const config = await fetchCurrentConfig();
      set({ config, isLoading: false, error: null });
      useCallStore.getState().configureLanguageSwitching(config.confidence_threshold, config.stability_count);
      return config;
    } catch (err: any) {
      console.error('Error loading configuration:', err);
      set({
        isLoading: false,
        error: err?.message || 'Failed to load configuration from backend',
      });
      return null;
    }
  },

  loadProfiles: async () => {
    try {
      const profiles = await fetchBusinessProfiles();
      const currentConfig = get().config;
      let matchedProfileId: string | null = get().selectedProfileId;

      if (!matchedProfileId && currentConfig && profiles.length > 0) {
        const found = profiles.find(
          (p) => p.name.toLowerCase() === currentConfig.business.name.toLowerCase()
        );
        if (found) {
          matchedProfileId = found.id;
        } else {
          matchedProfileId = profiles[0].id;
        }
      }

      set({ profiles, selectedProfileId: matchedProfileId });
      if (matchedProfileId) {
        useCallStore.getState().setSelectedProfileId(matchedProfileId);
      }
      return profiles;
    } catch (err: any) {
      console.error('Error loading business profiles:', err);
      return [];
    }
  },

  selectAndActivateProfile: async (profileId: string) => {
    set({ isActivating: true, error: null });
    try {
      const res = await activateBusinessProfile(profileId);
      if (res && res.config) {
        useCallStore.getState().configureLanguageSwitching(
          res.config.confidence_threshold,
          res.config.stability_count
        );
        set({
          config: res.config,
          selectedProfileId: profileId,
          isActivating: false,
          lastSavedAt: new Date().toLocaleTimeString(),
          error: null,
        });

        // Update call store with active profile ID
        useCallStore.getState().setSelectedProfileId(profileId);
        return true;
      }
      set({ isActivating: false });
      return false;
    } catch (err: any) {
      console.error('Failed to activate profile:', err);
      set({
        isActivating: false,
        error: err?.message || 'Failed to activate profile',
      });
      return false;
    }
  },

  saveConfig: async (newConfig: AgentConfig) => {
    set({ isSaving: true, error: null });
    try {
      const saved = await updateConfigApi(newConfig);
      useCallStore.getState().configureLanguageSwitching(saved.confidence_threshold, saved.stability_count);
      set({
        config: saved,
        isSaving: false,
        lastSavedAt: new Date().toLocaleTimeString(),
        error: null,
      });
      return true;
    } catch (err: any) {
      console.error('Error saving configuration:', err);
      set({
        isSaving: false,
        error: err?.message || 'Failed to save configuration to backend',
      });
      return false;
    }
  },

  setLocalConfig: (config: AgentConfig) => {
    set({ config });
  },

  clearError: () => {
    set({ error: null });
  },
}));
