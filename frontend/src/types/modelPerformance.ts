export interface AccuracyMetric {
  predictions: number;
  accuracy: number | null;
}

export interface ModelPerformance {
  evaluated_predictions: number;

  result_accuracy: number | null;

  high_confidence: AccuracyMetric;

  over_25: AccuracyMetric;

  btts: AccuracyMetric;
}