export type CardStatus =
  | "ACTIVE"
  | "TARGET_HIT"
  | "STOP_HIT"
  | "EXPIRED"
  | "NO_FILL"
  | "CANCELLED";

export type Horizon = "30m" | "2h" | "1d" | "2d" | "3d";

export interface NewsItem {
  headline: string;
  summary: string;
  source: string;
  datetime: number;
}

export interface TradeCard {
  id: number;
  symbol: string;
  company_name: string | null;
  direction: "long";
  status: CardStatus;
  entry_zone_low: number;
  entry_zone_high: number;
  stop: number;
  target_1: number;
  target_2: number;
  t1_hit: boolean;
  horizon: Horizon;
  expires_at: string;
  confidence: number;
  position_size: number;
  risk_amount: number;
  reasoning: string | null;
  invalidation: string | null;
  catalyst: string | null;
  news_context: NewsItem[] | null;
  snapshot: Record<string, unknown> | null;
  price_at_creation: number;
  resolved_price: number | null;
  realized_r: number | null;
  created_at: string;
  resolved_at: string | null;
  current_price?: number;
  pct_to_target?: number;
  pct_to_stop?: number;
}

export interface HorizonStats {
  count: number;
  wins: number;
  total_r: number;
}

export interface Stats {
  total: number;
  wins: number;
  losses: number;
  expired: number;
  no_fill: number;
  win_rate: number;
  avg_r: number;
  total_r: number;
  by_horizon: Record<string, HorizonStats>;
  last_30d: Omit<Stats, "last_30d">;
}

export interface Settings {
  account_size: number;
  risk_percent: number;
  max_active_cards: number;
  paper_mode: boolean;
  min_confidence: number;
  scan_enabled: boolean;
  [key: string]: unknown;
}

export interface ScanRun {
  id: number;
  universe_size: number;
  prefiltered_count: number;
  gemini_calls: number;
  cards_created: number;
  cards_rejected: number;
  duration_ms: number;
  ran_at: string;
}

export interface Health {
  status: string;
  market_open: boolean;
  scanner_running: boolean;
  last_scan: string | null;
  active_cards: number;
}

export interface WSMessage {
  type: "card_created" | "card_updated" | "price_tick" | "scan_completed";
  data: unknown;
}

export interface PriceTick {
  id: number;
  symbol: string;
  price: number;
  pct_to_target: number;
  pct_to_stop: number;
}
