export type CombinationStrategy =
  | "SAFE"
  | "BALANCED"
  | "AGGRESSIVE";


export interface BackendHealth {
  status: string;
  timestamp: string;

  upcoming_matches: number;
  production_ready_matches: number;
  production_coverage: number;

  active_signals: number;
  value_signals: number;

  pending_combinations: number;
  fresh_odds_rows: number;
}


export interface TicketSelection {
  id: number;

  signal_id: number;
  match_id: number;

  match: string | null;

  selection: string;

  odds: number | null;
  probability: number | null;

  correct: boolean | null;

  signal_edge: number | null;
  signal_ev: number | null;
}


export interface Ticket {
  id: number;

  name: string;

  strategy:
    CombinationStrategy
    | string;

  sport: string;

  total_odds: number | null;

  estimated_probability:
    number | null;

  risk_score: number | null;

  status: string;

  profit: number | null;
  roi: number | null;

  created_at: string | null;
  evaluated_at: string | null;

  selections: TicketSelection[];
}


export interface Signal {
  id: number;

  match_id: number;

  market_id: number;

  market_code: string | null;

  selection: string;

  signal_type: string;

  model_probability: number;

  market_probability:
    number | null;

  edge:
    number | null;

  odds:
    number | null;

  bookmaker:
    string | null;

  expected_value:
    number | null;

  is_value: boolean;

  confidence_score:
    number | null;

  risk_level:
    string | null;

  active: boolean;

  odds_recorded_at:
    string | null;

  created_at:
    string | null;
}


export interface MatchSummary {
  id: number;

  external_id:
    number | null;

  match_date:
    string | null;

  status: string;

  home_team: {
    id: number;
    name: string | null;
  };

  away_team: {
    id: number;
    name: string | null;
  };

  home_score:
    number | null;

  away_score:
    number | null;

  data_quality:
    "READY"
    | "PARTIAL"
    | "BLOCKED"
    | string;

  production_ready:
    boolean;
}


export interface DashboardPayload {

  health:
    BackendHealth;

  upcoming_matches:
    MatchSummary[];

  value_signals:
    Signal[];

  combinations:
    Ticket[];
}


export interface PerformanceStats {

  value_signals: {
    evaluated: number;
    wins: number;
    losses: number;

    hit_rate: number;

    profit_units: number;

    roi: number;
  };

  combinations: {
    evaluated: number;
    wins: number;
    losses: number;

    hit_rate: number;

    profit_units: number;

    roi: number;
  };
}

export interface TicketBuilderRequest {
  message: string;

  sport?: "football";

  strategy?:
    | "SAFE"
    | "BALANCED"
    | "AGGRESSIVE";

  date?:
    | "today"
    | "tomorrow";

  leagues?: string[];

  selections?: number;

  min_probability?: number;

  target_odds?: number;
}


export interface BuiltTicketSelection {
  signal_id: number;

  match_id: number;

  match: string;

  league: string | null;

  kickoff: string | null;

  market: string;

  selection: string;

  probability: number;

  market_probability:
    number | null;

  edge:
    number | null;

  expected_value:
    number | null;

  odds: number;

  bookmaker:
    string | null;
}


export interface ParsedTicketRequest {
  sport: string;

  strategy: string;

  date: string;

  leagues: string[];

  selections: number;

  min_probability: number;

  target_odds:
    number | null;
}


export interface TicketBuilderResponse {
  success: boolean;

  message: string;

  parsed_request:
    ParsedTicketRequest;

  selections:
    BuiltTicketSelection[];

  total_odds:
    number | null;

  estimated_probability:
    number | null;

  strategy: string;

  risk_level: string;

  candidates_found: number;
}

export interface OptimizedTicketSelection {
  signal_id: number;
  match_id: number;

  match: string;
  league: string;

  kickoff: string | null;

  market: string;
  selection: string;

  odds: number;

  bookmaker:
    string | null;

  raw_probability: number;
  calibrated_probability: number;

  edge: number;
  expected_value: number;

  quality_score: number;
  quality_tier: string;

  uncertainty: number;
}


export interface OptimizedTicketMetrics {
  total_odds: number;

  estimated_probability: number;
  naive_probability: number;

  average_quality: number;
  average_uncertainty: number;

  average_edge: number;
  average_ev: number;

  correlation_penalty: number;

  optimizer_score: number;
}


export interface OptimizedTicket {
  success: boolean;

  strategy:
    | "SAFE"
    | "BALANCED"
    | "AGGRESSIVE"
    | string;

  candidates_found: number;

  requested_selections: number;

  target_odds: number;

  message: string;

  selections:
    OptimizedTicketSelection[];

  metrics:
    OptimizedTicketMetrics | null;
}


export interface OptimizedTicketsResponse {
  generated_at: string;

  days: number;

  tickets:
    OptimizedTicket[];
}
export interface OptimizedTicketSelection {
  signal_id: number;
  match_id: number;

  match: string;
  league: string;
  kickoff: string | null;

  market: string;
  selection: string;

  odds: number;
  bookmaker: string | null;

  raw_probability: number;
  calibrated_probability: number;

  edge: number;
  expected_value: number;

  quality_score: number;
  quality_tier: string;

  uncertainty: number;
}


export interface OptimizedTicketMetrics {
  total_odds: number;

  estimated_probability: number;
  naive_probability: number;

  average_quality: number;
  average_uncertainty: number;

  average_edge: number;
  average_ev: number;

  correlation_penalty: number;

  optimizer_score: number;
}


export interface OptimizedTicket {
  success: boolean;

  strategy:
    | "SAFE"
    | "BALANCED"
    | "AGGRESSIVE"
    | string;

  candidates_found: number;

  requested_selections: number;

  target_odds: number;

  message: string;

  selections: OptimizedTicketSelection[];

  metrics: OptimizedTicketMetrics | null;
}


export interface OptimizedTicketsResponse {
  generated_at: string;

  days: number;

  tickets: OptimizedTicket[];
}