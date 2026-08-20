export interface PredictionProbabilities {
  HOME: number;
  DRAW: number;
  AWAY: number;
}

export interface RuleEnginePrediction {
  pick: "HOME" | "DRAW" | "AWAY";
  confidence: number;

  probabilities: PredictionProbabilities;

  over_25: number;
  btts_yes: number;
}

export interface MlModelPrediction {
  pick: "HOME" | "DRAW" | "AWAY";

  probabilities: PredictionProbabilities;

  confidence: number;
  margin: number;

  analitiko_score: number;
  league_threshold: number;

  is_strong_pick: boolean;

  elite_threshold: number;

  is_elite_pick: boolean;

  confidence_level:
  | "LOW"
  | "MEDIUM"
  | "STRONG"
  | "ELITE";

  trained_classes: string[];

  experimental: boolean;
}

export interface PredictionComparison {
  match_id: number;

  home_team: string;
  away_team: string;

  league: string;

  rule_engine: RuleEnginePrediction;

  ml_model: MlModelPrediction;

  comparison: {
    agreement: boolean;
    same_pick: boolean;

    rule_selected_probability: number;
    ml_selected_probability: number;

    probability_difference: number;
  };

  warning: string;
}