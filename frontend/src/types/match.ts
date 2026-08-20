export interface Team {
  id: number;
  name: string;
  country?: string | null;
  logo?: string | null;
}

export interface League {
  id: number;
  name: string;
  country: string;
  logo?: string | null;
}

export interface Match {
  id: number;
  match_date: string;
  status: string;
  home_score?: number | null;
  away_score?: number | null;
  league: League;
  home_team: Team;
  away_team: Team;
}