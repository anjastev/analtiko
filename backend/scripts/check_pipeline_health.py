from datetime import datetime, timezone

from app.database.database import SessionLocal

from app.models.match import Match
from app.models.odds import Odds
from app.models.team_match_history import TeamMatchHistory
from app.models.prediction_snapshot import PredictionSnapshot


def run():
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        total_matches = (
            db.query(Match)
            .count()
        )

        upcoming_matches = (
            db.query(Match)
            .filter(
                Match.match_date >= now
            )
            .count()
        )

        finished_matches = (
            db.query(Match)
            .filter(
                Match.status.in_(
                    ["FT", "AET", "PEN"]
                )
            )
            .count()
        )

        odds_rows = (
            db.query(Odds)
            .count()
        )

        matches_with_odds = (
            db.query(Odds.match_id)
            .distinct()
            .count()
        )

        history_rows = (
            db.query(
                TeamMatchHistory
            )
            .count()
        )

        teams_with_history = (
            db.query(
                TeamMatchHistory.team_id
            )
            .distinct()
            .count()
        )

        snapshots = (
            db.query(
                PredictionSnapshot
            )
            .count()
        )

        official_snapshots = (
            db.query(
                PredictionSnapshot
            )
            .filter(
                PredictionSnapshot.is_official
                == 1
            )
            .count()
        )

        evaluated = (
            db.query(
                PredictionSnapshot
            )
            .filter(
                PredictionSnapshot.result_correct
                .isnot(None)
            )
            .count()
        )

        print()
        print("=" * 65)
        print("ANALITIKO PIPELINE HEALTH")
        print("=" * 65)

        print()
        print("MATCHES")
        print(f"Total:       {total_matches}")
        print(f"Upcoming:    {upcoming_matches}")
        print(f"Finished:    {finished_matches}")

        print()
        print("ODDS")
        print(f"Rows:        {odds_rows}")
        print(
            f"Matches:     {matches_with_odds}"
        )

        print()
        print("HISTORY")
        print(f"Rows:        {history_rows}")
        print(
            f"Teams:       {teams_with_history}"
        )

        print()
        print("PREDICTIONS")
        print(f"Snapshots:   {snapshots}")
        print(
            f"Official:    {official_snapshots}"
        )
        print(f"Evaluated:   {evaluated}")

        print()
        print("=" * 65)
        print("HEALTH")
        print("=" * 65)

        checks = {
            "Matches available":
                total_matches > 0,

            "Upcoming matches":
                upcoming_matches > 0,

            "Odds available":
                matches_with_odds > 0,

            "History available":
                history_rows > 0,

            "Prediction data":
                snapshots > 0,

            "Evaluation data":
                evaluated > 0,
        }

        for label, status in checks.items():
            symbol = (
                "OK"
                if status
                else "MISSING"
            )

            print(
                f"{label:<25} {symbol}"
            )

        print()

    finally:
        db.close()


if __name__ == "__main__":
    run()