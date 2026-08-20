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


export interface TeamListItem {
  id: number;

  external_id?: number | null;

  name: string;

  country?: string | null;

  logo?: string | null;

  form: TeamForm;
}