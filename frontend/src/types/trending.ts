export interface TrendingMatch {
  match_id: number;

  league: string;

  home_team: string;
  away_team: string;

  match_date: string;

  score: number;

  confidence: number;

  main_pick: "HOME" | "DRAW" | "AWAY";

  market_signal:
    | "HOME_DROP"
    | "AWAY_DROP"
    | "STABLE";

  h2h: {
    matches: number;
    home_score: number;
    away_score: number;
  };

  form: {
    home: number;
    away: number;
  };

  odds: {
    home: number;
    draw: number;
    away: number;
  };

  breakdown: {
    odds_movement: number;
    favorite_drop: number;
    form: number;
    goals: number;
    h2h: number;
    league: number;
  };
}