import { Link } from "react-router-dom";
import type { Match } from "../types/match";

interface MatchCardProps {
  match: Match;
}

function MatchCard({ match }: MatchCardProps) {
  const matchDate = new Date(match.match_date);

  return (
    <Link
      to={`/matches/${match.id}`}
      className="match-card-link"
    >
      <div className="match-card">
        <div className="match-card__top">
          <span className="league-name">
            {match.league.name}
          </span>

          <span className="match-status">
            {match.status}
          </span>
        </div>

        <div className="match-card__teams">
          <div className="team-row">
            <span>{match.home_team.name}</span>
            <strong>
              {match.home_score ?? "-"}
            </strong>
          </div>

          <div className="team-row">
            <span>{match.away_team.name}</span>
            <strong>
              {match.away_score ?? "-"}
            </strong>
          </div>
        </div>

        <div className="match-card__footer">
          <span>
            {matchDate.toLocaleDateString()}
          </span>

          <span>
            {matchDate.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      </div>
    </Link>
  );
}

export default MatchCard;