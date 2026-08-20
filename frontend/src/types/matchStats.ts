export interface MatchStats {
  match_id: number;

  home_form: number;
  away_form: number;

  home_goals_avg: number;
  away_goals_avg: number;

  home_shots_avg: number;
  away_shots_avg: number;

  home_corners_avg: number;
  away_corners_avg: number;

  home_possession_avg: number;
  away_possession_avg: number;

  home_xg_avg: number;
  away_xg_avg: number;
}