export type Horizon = 'intraday' | 'daily' | 'weekly';

export const HORIZONS: Horizon[] = ['intraday', 'daily', 'weekly'];

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface SearchResult {
  symbol: string;
  description: string;
  type: string;
  displaySymbol: string;
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface Snapshot {
  ticker: string;
  price: number;
  volume: number;
  timestamp: string;
  source: string;
  market_open: boolean;
}

export interface AccuracyResponse {
  ticker: string;
  horizon: Horizon;
  count: number;
  model: {
    rolling_mae: number | null;
    mae: number | null;
    directional_accuracy: number | null;
    mean_error: number | null;
    update_count: number;
  };
  naive: {
    mae: number | null;
    directional_accuracy: number | null;
  };
  random_walk: {
    mae: number | null;
  };
  mae_trend: { t: string; abs_error: number }[];
  beats_naive: boolean;
}

export interface HistoryPoint {
  predicted_at: string;
  target_at: string;
  base_price: number;
  predicted_price: number;
  actual_price: number | null;
  error: number | null;
  resolved: boolean;
  source: string;
}

export interface HistoryResponse {
  points: HistoryPoint[];
}

export interface LastPrediction {
  predicted_price: number;
  actual_price: number;
  error: number;
  abs_error: number;
  hit: boolean;
  naive_abs_error: number;
  target_at: string;
}

export interface Tick {
  type: 'tick';
  ticker: string;
  horizon: Horizon;
  timestamp: string;
  price: number;
  predicted_price: number;
  predicted_return: number;
  predicted_at: string;
  target_at: string;
  last_prediction: LastPrediction | null;
  rolling_mae: number | null;
  source: 'live' | 'replay';
}
