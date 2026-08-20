export interface PopularityResponse {
  match_id: number;
  popularity_score: number;
  level: "low" | "medium" | "high" | "very_high";

  breakdown: {
    odds_movement: number;
    form: number;
    goals: number;
    xg: number;
    league: number;
  };
}