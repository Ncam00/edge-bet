import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

// Attach JWT to every request
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ──────────────────────────────────────────────────────
export const register = (email: string, password: string) =>
  api.post('/auth/register', { email, password });

export const login = async (email: string, password: string) => {
  const form = new FormData();
  form.append('username', email);
  form.append('password', password);
  const { data } = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  await SecureStore.setItemAsync('access_token', data.access_token);
  return data;
};

export const logout = async () => {
  await SecureStore.deleteItemAsync('access_token');
};

// ── Picks ─────────────────────────────────────────────────────
export const getTodaysPicks = () =>
  api.get('/picks/today').then((r) => r.data);

export const getPickDetail = (id: number) =>
  api.get(`/picks/${id}`).then((r) => r.data);

// ── Bets ──────────────────────────────────────────────────────
export const placeBet = (body: {
  game_id: number;
  prediction_id?: number;
  stake: number;
  decimal_odds: number;
  market: string;
  selection: string;
}) => api.post('/bets', body).then((r) => r.data);

export const getBets = () => api.get('/bets').then((r) => r.data);

export const getBankroll = () => api.get('/bankroll').then((r) => r.data);
