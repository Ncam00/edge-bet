import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { login as apiLogin, logout as apiLogout } from '../services/api';

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
    const token = await SecureStore.getItemAsync('access_token');
    set({ token, isLoading: false });
  },

  login: async (email, password) => {
    const data = await apiLogin(email, password);
    set({ token: data.access_token, plan: data.plan });
  },

  logout: async () => {
    await apiLogout();
    set({ token: null, plan: 'free' });
  },
}));
