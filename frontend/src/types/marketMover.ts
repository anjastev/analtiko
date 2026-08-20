export interface MarketMover {
  match_id: number;

  league: string;

  home_team: string;
  away_team: string;

  match_date: string;

  market: "HOME" | "DRAW" | "AWAY";

  opening_odd: number;
  current_odd: number;

  change: number;
  change_percentage: number;

  direction: "DROP" | "RISE";
}