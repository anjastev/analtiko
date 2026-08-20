export interface ValueAnalyticsGroup {
  total: number;
  pending: number;
  evaluated: number;
  correct: number;
  accuracy: number | null;
  profit: number;
  roi: number | null;
  average_edge: number | null;
  average_odds: number | null;
}

export interface ValueAnalyticsThresholds {
  value_edge: number;
  elite_value_edge: number;
}

export interface ValueAnalyticsRecentItem {
  id: number;
  match_id: number;

  league: string;
  home_team: string;
  away_team: string;

  match_date: string;

  value_pick: "HOME" | "DRAW" | "AWAY";
  model_pick: "HOME" | "DRAW" | "AWAY";

  model_probability: number;
  market_probability: number;

  edge: number;

  market_odds: number;
  fair_odds: number | null;

  expected_value: number | null;

  analitiko_score: number;

  is_strong_pick: boolean;
  is_elite_pick: boolean;
  is_elite_value: boolean;

  same_as_model_pick: boolean;

  bookmaker: string | null;

  created_at: string;

  actual_result:
    | "HOME"
    | "DRAW"
    | "AWAY"
    | null;

  correct: boolean | null;

  profit: number | null;
  roi: number | null;
}

export interface ValueAnalyticsResponse {
  model: string;

  status: string;

  thresholds: ValueAnalyticsThresholds;

  summary: ValueAnalyticsGroup;

  value: ValueAnalyticsGroup;

  elite_value: ValueAnalyticsGroup;

  model_consensus: ValueAnalyticsGroup;

  recent: ValueAnalyticsRecentItem[];

  note: string;
}