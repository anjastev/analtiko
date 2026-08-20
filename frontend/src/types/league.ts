export interface LeagueListItem {
  id: number;
  external_id?: number | null;

  name: string;
  country?: string | null;
  logo?: string | null;

  matches_count: number;
}

export interface LeagueMatch {
  id: number;

  home_team: {
    id: number;
    name: string;
    logo?: string | null;
  };

  away_team: {
    id: number;
    name: string;
    logo?: string | null;
  };

  match_date: string;
  status: string;

  home_score?: number | null;
  away_score?: number | null;
}

export interface LeagueDetailsResponse {
  id: number;
  external_id?: number | null;

  name: string;
  country?: string | null;
  logo?: string | null;

  matches_count: number;

  matches: LeagueMatch[];
}