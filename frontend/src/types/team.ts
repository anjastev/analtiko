export interface TeamForm {
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


// ============================================================
// TEAM LIST
// ============================================================

export interface TeamListItem {
  id: number;

  external_id?: number | null;

  name: string;

  country?: string | null;

  logo?: string | null;

  form: TeamForm;
}


// ============================================================
// TEAM HISTORY
// ============================================================

export interface TeamHistoryItem {
  fixture_external_id: number;

  match_date: string;

  league_name?: string | null;

  opponent_name: string;

  venue: string;

  goals_for: number;
  goals_against: number;

  result: string;
}


// ============================================================
// UPCOMING TEAM MATCH
// ============================================================

export interface TeamUpcomingMatch {
  id: number;

  league: string;

  home_team: string;
  away_team: string;

  match_date: string;
}


// ============================================================
// TEAM DETAILS RESPONSE
// ============================================================

export interface TeamDetailsResponse {
  id: number;

  external_id?: number | null;

  name: string;

  country?: string | null;

  logo?: string | null;

  form: TeamForm;

  history: TeamHistoryItem[];

  upcoming_matches: TeamUpcomingMatch[];
}