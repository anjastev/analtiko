export type MatchPick =
  | "HOME"
  | "DRAW"
  | "AWAY";


export type MlConfidenceLevel =
  | "LOW"
  | "MEDIUM"
  | "STRONG"
  | "ELITE";


export interface MlPredictionDetails {
  pick: MatchPick;

  probabilities: {
    HOME: number;
    DRAW: number;
    AWAY: number;
  };

  confidence: number;
  margin: number;

  analitiko_score: number;

  league_threshold: number;
  elite_threshold: number;

  is_strong_pick: boolean;
  is_elite_pick: boolean;

  confidence_level: MlConfidenceLevel;

  trained_classes: string[];

  experimental: boolean;
}


export interface MlPredictionItem {
  match_id: number;

  league: string;

  home_team: string;
  away_team: string;

  match_date: string;

  status: string;

  prediction: MlPredictionDetails;
}