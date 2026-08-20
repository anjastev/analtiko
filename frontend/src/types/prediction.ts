export interface PredictionResponse {
  match_id: number;

  prediction: {
    home_win: number;
    draw: number;
    away_win: number;
    over_25: number;
    btts_yes: number;
    confidence: number;
    main_pick: "HOME" | "DRAW" | "AWAY";
  };

  reasons: string[];
}