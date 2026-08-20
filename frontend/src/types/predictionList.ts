export interface PredictionListItem {
  match_id: number;
  league: string;
  home_team: string;
  away_team: string;
  match_date: string;

  prediction: {
    home_win: number;
    draw: number;
    away_win: number;
    over_25: number;
    btts_yes: number;
    confidence: number;
    main_pick: "HOME" | "DRAW" | "AWAY";
  };
}