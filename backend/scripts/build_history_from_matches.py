from app.database.database import SessionLocal

from app.models.match import Match
from app.models.team_match_history import TeamMatchHistory


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def get_result(
    goals_for: int,
    goals_against: int,
) -> str:

    if goals_for > goals_against:
        return "W"

    if goals_for < goals_against:
        return "L"

    return "D"


def history_exists(
    db,
    team_id: int,
    fixture_external_id: int,
) -> bool:

    existing = (
        db.query(TeamMatchHistory)
        .filter(
            TeamMatchHistory.team_id == team_id,
            TeamMatchHistory.fixture_external_id
            == fixture_external_id,
        )
        .first()
    )

    return existing is not None


def run():
    db = SessionLocal()

    created = 0
    skipped = 0
    failed = 0

    try:

        matches = (
            db.query(Match)
            .filter(
                Match.status.in_(
                    FINISHED_STATUSES
                )
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        print()
        print("=" * 70)
        print("ANALITIKO LOCAL HISTORY BUILDER")
        print("=" * 70)

        print(
            f"Finished matches: "
            f"{len(matches)}"
        )

        for match in matches:

            if (
                match.external_id is None
                or match.home_score is None
                or match.away_score is None
            ):
                skipped += 1
                continue

            try:

                # =================================================
                # HOME TEAM HISTORY
                # =================================================

                if not history_exists(
                    db=db,
                    team_id=match.home_team_id,
                    fixture_external_id=
                        match.external_id,
                ):

                    home_history = (
                        TeamMatchHistory(
                            team_id=
                                match.home_team_id,

                            fixture_external_id=
                                match.external_id,

                            match_date=
                                match.match_date,

                            league_name=
                                match.league.name,

                            opponent_name=
                                match.away_team.name,

                            venue="home",

                            goals_for=
                                match.home_score,

                            goals_against=
                                match.away_score,

                            result=
                                get_result(
                                    match.home_score,
                                    match.away_score,
                                ),
                        )
                    )

                    db.add(
                        home_history
                    )

                    created += 1

                else:
                    skipped += 1


                # =================================================
                # AWAY TEAM HISTORY
                # =================================================

                if not history_exists(
                    db=db,
                    team_id=match.away_team_id,
                    fixture_external_id=
                        match.external_id,
                ):

                    away_history = (
                        TeamMatchHistory(
                            team_id=
                                match.away_team_id,

                            fixture_external_id=
                                match.external_id,

                            match_date=
                                match.match_date,

                            league_name=
                                match.league.name,

                            opponent_name=
                                match.home_team.name,

                            venue="away",

                            goals_for=
                                match.away_score,

                            goals_against=
                                match.home_score,

                            result=
                                get_result(
                                    match.away_score,
                                    match.home_score,
                                ),
                        )
                    )

                    db.add(
                        away_history
                    )

                    created += 1

                else:
                    skipped += 1


                db.commit()


                print(
                    f"{match.home_team.name} "
                    f"{match.home_score}-"
                    f"{match.away_score} "
                    f"{match.away_team.name}"
                )


            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"FAILED match "
                    f"{match.id}: "
                    f"{error}"
                )


        print()
        print("=" * 70)
        print("LOCAL HISTORY COMPLETE")
        print("=" * 70)

        print(
            f"Created rows: "
            f"{created}"
        )

        print(
            f"Skipped existing: "
            f"{skipped}"
        )

        print(
            f"Failed: "
            f"{failed}"
        )


    finally:
        db.close()


if __name__ == "__main__":
    run()