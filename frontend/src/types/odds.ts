export interface Odds {
  id: number;
  match_id: number;

  bookmaker?: string | null;

  home_win: number;
  draw: number;
  away_win: number;

  over_25?: number | null;
  under_25?: number | null;

  btts_yes?: number | null;
  btts_no?: number | null;

  recorded_at: string;
}