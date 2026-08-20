export interface TeamFormData {
  id: number;
  name: string;

  matches: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;

  form_score: number;

  goals_for_avg: number;
  goals_against_avg: number;

  sequence: string[];
}

export interface MatchFormResponse {
  match_id: number;

  home_team: TeamFormData;
  away_team: TeamFormData;
}