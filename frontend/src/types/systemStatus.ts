export interface SystemStatus {
  freshness: {
    fixtures: string | null;
    odds: string | null;
    history: string | null;
    predictions: string | null;
    official_predictions: string | null;
  };

  coverage: {
    total_matches: number;
    finished_matches: number;
    matches_with_odds: number;
    teams_with_history: number;
    prediction_snapshots: number;
    official_predictions: number;
  };
}