export interface H2HMatchItem {
  date: string;

  home_team: string;
  away_team: string;

  home_goals: number;
  away_goals: number;
}

export interface H2HSummary {
  matches: number;

  home_wins: number;
  draws: number;
  away_wins: number;

  home_goals_avg: number;
  away_goals_avg: number;
}

export interface H2HResponse {
  match_id: number;

  home_team: string;
  away_team: string;

  summary: H2HSummary;

  matches: H2HMatchItem[];
}