import { create } from 'zustand';
import { Platform } from 'react-native';
import { login as apiLogin, logout as apiLogout } from '../services/api';

// Web-safe storage helper
const storage = {
  getItem: async (key: string): Promise<string | null> => {
    if (Platform.OS === 'web') {
      return localStorage.getItem(key);
    }
    const SecureStore = await import('expo-secure-store');
    return SecureStore.getItemAsync(key);
  },
  setItem: async (key: string, value: string): Promise<void> => {
    if (Platform.OS === 'web') {
      localStorage.setItem(key, value);
      return;
    }
    const SecureStore = await import('expo-secure-store');
    await SecureStore.setItemAsync(key, value);
  },
  removeItem: async (key: string): Promise<void> => {
    if (Platform.OS === 'web') {
      localStorage.removeItem(key);
      return;
    }
    const SecureStore = await import('expo-secure-store');
    await SecureStore.deleteItemAsync(key);
  },
};

interface AuthState {
  token: string | null;
  plan: 'free' | 'premium';
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  plan: 'free',
  isLoading: true,

  hydrate: async () => {
    try {
      const token = await storage.getItem('access_token');
      set({ token, isLoading: false });
    } catch (e) {
      console.warn('Hydration error:', e);
      set({ isLoading: false });
    }
  },

  login: async (email, password) => {
    const data = await apiLogin(email, password);
    await storage.setItem('access_token', data.access_token);
    set({ token: data.access_token, plan: data.plan });
  },

  logout: async () => {
    await apiLogout();
    await storage.removeItem('access_token');
    set({ token: null, plan: 'free' });
  },
}));
