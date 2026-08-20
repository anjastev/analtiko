export type MlConfidenceLevel =
  | "LOW"
  | "MEDIUM"
  | "STRONG"
  | "ELITE";


export interface MlAnalyticsSummary {
  total_snapshots: number;

  pending: number;

  evaluated: number;

  correct: number;

  accuracy: number | null;
}


export interface MlPickPerformance {
  total: number;

  evaluated: number;

  correct: number;

  accuracy: number | null;
}


export interface MlElitePerformance
  extends MlPickPerformance {

  threshold: number;
}


export interface MlValidation {
  strict_oos_matches: number;

  strict_oos_accuracy: number;

  strict_oos_strong_accuracy: number;

  strict_oos_strong_coverage: number;

  strict_oos_elite_accuracy: number;

  elite_threshold: number;

  note: string;
}


export interface MlConfidencePerformance {
  level: MlConfidenceLevel;

  total: number;

  evaluated: number;

  correct: number;

  accuracy: number | null;
}


export interface MlLeaguePerformance {
  league: string;

  snapshots: number;

  evaluated: number;

  correct: number;

  accuracy: number | null;

  strong_picks: number;

  strong_evaluated: number;

  strong_correct: number;

  strong_accuracy: number | null;

  elite_picks: number;

  elite_evaluated: number;

  elite_correct: number;

  elite_accuracy: number | null;
}


export interface MlRecentResult {
  snapshot_id: number;

  match_id: number;

  league: string;

  home_team: string;
  away_team: string;

  match_date: string;

  home_score: number | null;
  away_score: number | null;

  pick:
    | "HOME"
    | "DRAW"
    | "AWAY";

  actual_result:
    | "HOME"
    | "DRAW"
    | "AWAY"
    | null;

  correct: boolean;

  confidence: number;

  margin: number;

  analitiko_score: number;

  league_threshold: number;

  elite_threshold: number;

  is_strong_pick: boolean;

  is_elite_pick: boolean;

  confidence_level:
    MlConfidenceLevel;

  model_version: string;

  created_at: string;

  evaluated_at: string;
}


export interface MlPendingResult {
  snapshot_id: number;

  match_id: number;

  league: string;

  home_team: string;
  away_team: string;

  match_date: string;

  status: string;

  pick:
    | "HOME"
    | "DRAW"
    | "AWAY";

  confidence: number;

  margin: number;

  analitiko_score: number;

  league_threshold: number;

  elite_threshold: number;

  is_strong_pick: boolean;

  is_elite_pick: boolean;

  confidence_level:
    MlConfidenceLevel;

  model_version: string;

  created_at: string;
}


export interface MlAnalyticsResponse {
  model: string;

  experimental: boolean;

  validation: MlValidation;

  summary: MlAnalyticsSummary;

  strong_picks:
    MlPickPerformance;

  elite_picks:
    MlElitePerformance;

  confidence_levels:
    MlConfidencePerformance[];

  by_league:
    MlLeaguePerformance[];

  recent_results:
    MlRecentResult[];

  recent_pending:
    MlPendingResult[];

  note: string;
}