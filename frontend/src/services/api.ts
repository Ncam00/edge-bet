import axios from 'axios';
import { Platform } from 'react-native';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

// Attach JWT to every request
api.interceptors.request.use(async (config) => {
  const token = await storage.getItem('access_token');
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
  await storage.setItem('access_token', data.access_token);
  return data;
};

export const logout = async () => {
  await storage.removeItem('access_token');
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

// ── Player Props ──────────────────────────────────────────────
export const getTopProps = () => 
  api.get('/props/top-props').then((r) => r.data);

export const analyzeProps = (props: PropRequest[]) =>
  api.post('/props/scan', { props }).then((r) => r.data);

export const getSupportedPlayers = () =>
  api.get('/props/players').then((r) => r.data);

// ── Live Betting ──────────────────────────────────────────────
export const analyzeLiveGame = (game: LiveGameRequest) =>
  api.post('/live/analyze', game).then((r) => r.data);

export const getSharpSignals = () =>
  api.get('/live/signals/today').then((r) => r.data);

export const analyzeSharpMoney = (game: SharpAnalysisRequest) =>
  api.post('/live/sharp/analyze', game).then((r) => r.data);

// ── Multi-Sport ───────────────────────────────────────────────
export const getSportCategories = () =>
  api.get('/sports/categories').then((r) => r.data);

export const getAvailableSports = () =>
  api.get('/sports/available').then((r) => r.data);

export const getAllSportPicks = () =>
  api.get('/sports/all').then((r) => r.data);

export const getSportPicks = (sportKey: string) =>
  api.get(`/sports/${sportKey}/picks`).then((r) => r.data);

export const getCategoryPicks = (category: string) =>
  api.get(`/sports/category/${category}/picks`).then((r) => r.data);

// ── Horse & Greyhound Racing ──────────────────────────────────
export const getTodaysRaces = (raceType?: string) =>
  api.get('/racing/today', { params: { race_type: raceType } }).then((r) => r.data);

export const getRacingValueBets = () =>
  api.get('/racing/value-bets').then((r) => r.data);

export const getRaceDetails = (raceId: string) =>
  api.get(`/racing/race/${raceId}`).then((r) => r.data);

export const getRunnerAnalysis = (raceId: string, runnerNumber: number) =>
  api.get(`/racing/runner/${raceId}/${runnerNumber}`).then((r) => r.data);

export const getRacingTips = (limit: number = 10, raceType?: string) =>
  api.get('/racing/tips', { params: { limit, race_type: raceType } }).then((r) => r.data);

export const getHorseTracks = () =>
  api.get('/racing/horses/tracks').then((r) => r.data);

export const getGreyhoundTracks = () =>
  api.get('/racing/greyhounds/tracks').then((r) => r.data);

export const getRacingSummary = () =>
  api.get('/racing/summary').then((r) => r.data);

// ── Racing Video Streams ──────────────────────────────────────
export const getLiveVideoStreams = (region?: string) =>
  api.get('/racing/video/streams', { params: { region } }).then((r) => r.data);

export const getRaceVideo = (raceId: string) =>
  api.get(`/racing/video/race/${raceId}`).then((r) => r.data);

export const getYouTubeRacingStreams = () =>
  api.get('/racing/video/youtube').then((r) => r.data);

export const getRegionalStreams = (region: string) =>
  api.get(`/racing/video/regional/${region}`).then((r) => r.data);

// ── Types ─────────────────────────────────────────────────────
export interface PropRequest {
  player: string;
  opponent: string;
  prop_type: 'points' | 'rebounds' | 'assists' | 'threes' | 'pra';
  line: number;
  odds_over?: number;
  odds_under?: number;
  expected_minutes?: number;
}

export interface PropPrediction {
  player: string;
  team: string;
  opponent: string;
  prop_type: string;
  projection: number;
  line: number;
  best_bet: 'OVER' | 'UNDER' | null;
  value: number;
  probability: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface LiveGameRequest {
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  quarter: number;
  minutes_remaining: number;
  pre_game_prob: number;
  live_odds_home?: number;
  live_odds_away?: number;
  home_last_3min_points?: number;
  away_last_3min_points?: number;
}

export interface SharpAnalysisRequest {
  game_id: string;
  home_team: string;
  away_team: string;
  opening_home_odds: number;
  current_home_odds: number;
  opening_away_odds: number;
  current_away_odds: number;
  bet_percent_home?: number;
  money_percent_home?: number;
}

export interface ValueBet {
  id: number;
  home_team: string;
  away_team: string;
  commence_time: string;
  market: string;
  selection: string;
  model_probability: number;
  implied_probability: number;
  decimal_odds: number;
  expected_value: number;
  confidence_label: 'high' | 'medium' | 'low';
  reasoning: string;
}
