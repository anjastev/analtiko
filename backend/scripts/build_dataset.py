import csv
from pathlib import Path

from app.database.database import SessionLocal

from app.models.match import Match
from app.models.odds import Odds
from app.models.match_stats import MatchStats
from app.models.team_match_history import TeamMatchHistory
from app.models.h2h import H2HMatch

from app.analytics.team_form import (
    calculate_form_from_history,
)

from app.analytics.h2h import (
    calculate_h2h_scores,
)


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


OUTPUT_DIR = Path("data")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "analitiko_dataset.csv"
)


def get_result(
    home_score: int,
    away_score: int,
) -> str:

    if home_score > away_score:
        return "HOME"

    if home_score < away_score:
        return "AWAY"

    return "DRAW"


def calculate_context_stats(
    history,
):
    if not history:
        return {
            "games": 0,
            "points_per_game": 0.0,
            "goals_for_avg": 0.0,
            "goals_against_avg": 0.0,
            "goal_difference_avg": 0.0,
            "clean_sheet_rate": 0.0,
            "failed_to_score_rate": 0.0,
            "win_rate": 0.0,
        }

    games = len(history)

    points = 0
    goals_for = 0
    goals_against = 0
    clean_sheets = 0
    failed_to_score = 0
    wins = 0

    for item in history:

        goals_for += (
            item.goals_for or 0
        )

        goals_against += (
            item.goals_against or 0
        )

        if item.result == "W":
            points += 3
            wins += 1

        elif item.result == "D":
            points += 1

        if (
            item.goals_against
            == 0
        ):
            clean_sheets += 1

        if (
            item.goals_for
            == 0
        ):
            failed_to_score += 1

    goals_for_avg = (
        goals_for
        / games
    )

    goals_against_avg = (
        goals_against
        / games
    )

    return {
        "games":
            games,

        "points_per_game":
            round(
                points / games,
                3,
            ),

        "goals_for_avg":
            round(
                goals_for_avg,
                3,
            ),

        "goals_against_avg":
            round(
                goals_against_avg,
                3,
            ),

        "goal_difference_avg":
            round(
                goals_for_avg
                - goals_against_avg,
                3,
            ),

        "clean_sheet_rate":
            round(
                clean_sheets
                / games,
                3,
            ),

        "failed_to_score_rate":
            round(
                failed_to_score
                / games,
                3,
            ),

        "win_rate":
            round(
                wins
                / games,
                3,
            ),
    }


def run():
    db = SessionLocal()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    skipped_no_score = 0
    skipped_no_history = 0

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
        print(
            "ANALITIKO ML DATASET BUILDER V3"
        )
        print("=" * 70)

        print(
            f"Finished matches found: "
            f"{len(matches)}"
        )


        for match in matches:

            print()
            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )


            # =================================================
            # FINAL SCORE
            # =================================================

            if (
                match.home_score
                is None
                or
                match.away_score
                is None
            ):

                skipped_no_score += 1

                print(
                    "Skipped: missing score"
                )

                continue


            # =================================================
            # GENERAL HISTORY
            # leakage-safe
            # =================================================

            home_history = (
                db.query(
                    TeamMatchHistory
                )
                .filter(
                    TeamMatchHistory.team_id
                    == match.home_team_id,

                    TeamMatchHistory.match_date
                    < match.match_date,
                )
                .order_by(
                    TeamMatchHistory
                    .match_date
                    .desc()
                )
                .limit(5)
                .all()
            )


            away_history = (
                db.query(
                    TeamMatchHistory
                )
                .filter(
                    TeamMatchHistory.team_id
                    == match.away_team_id,

                    TeamMatchHistory.match_date
                    < match.match_date,
                )
                .order_by(
                    TeamMatchHistory
                    .match_date
                    .desc()
                )
                .limit(5)
                .all()
            )


            if (
                not home_history
                or
                not away_history
            ):

                skipped_no_history += 1

                print(
                    "Skipped: no history"
                )

                continue


            home_form = (
                calculate_form_from_history(
                    home_history
                )
            )


            away_form = (
                calculate_form_from_history(
                    away_history
                )
            )


            # =================================================
            # ROLLING 3 HISTORY
            # =================================================

            home_history_3 = (
                home_history[:3]
            )

            away_history_3 = (
                away_history[:3]
            )


            home_form_3 = (
                calculate_form_from_history(
                    home_history_3
                )
            )


            away_form_3 = (
                calculate_form_from_history(
                    away_history_3
                )
            )


            # =================================================
            # HOME-SPECIFIC HISTORY
            # =================================================

            home_venue_history = (
                db.query(
                    TeamMatchHistory
                )
                .filter(
                    TeamMatchHistory.team_id
                    == match.home_team_id,

                    TeamMatchHistory.match_date
                    < match.match_date,

                    TeamMatchHistory.venue
                    == "home",
                )
                .order_by(
                    TeamMatchHistory
                    .match_date
                    .desc()
                )
                .limit(5)
                .all()
            )


            # =================================================
            # AWAY-SPECIFIC HISTORY
            # =================================================

            away_venue_history = (
                db.query(
                    TeamMatchHistory
                )
                .filter(
                    TeamMatchHistory.team_id
                    == match.away_team_id,

                    TeamMatchHistory.match_date
                    < match.match_date,

                    TeamMatchHistory.venue
                    == "away",
                )
                .order_by(
                    TeamMatchHistory
                    .match_date
                    .desc()
                )
                .limit(5)
                .all()
            )


            home_context = (
                calculate_context_stats(
                    home_venue_history
                )
            )


            away_context = (
                calculate_context_stats(
                    away_venue_history
                )
            )


            # =================================================
            # XG
            # =================================================

            stats = (
                db.query(MatchStats)
                .filter(
                    MatchStats.match_id
                    == match.id
                )
                .first()
            )


            home_xg = 1.2
            away_xg = 1.2


            if stats:

                if (
                    stats.home_xg_avg
                    and
                    stats.home_xg_avg > 0
                ):
                    home_xg = (
                        stats.home_xg_avg
                    )

                if (
                    stats.away_xg_avg
                    and
                    stats.away_xg_avg > 0
                ):
                    away_xg = (
                        stats.away_xg_avg
                    )


            # =================================================
            # ODDS
            # optional
            # =================================================

            latest_odds = (
                db.query(Odds)
                .filter(
                    Odds.match_id
                    == match.id
                )
                .order_by(
                    Odds.recorded_at.desc()
                )
                .first()
            )


            if latest_odds:

                home_odds = (
                    latest_odds.home_win
                )

                draw_odds = (
                    latest_odds.draw
                )

                away_odds = (
                    latest_odds.away_win
                )

                has_odds = 1

            else:

                home_odds = None
                draw_odds = None
                away_odds = None

                has_odds = 0


            # =================================================
            # H2H
            # leakage-safe
            # =================================================

            home_external_id = (
                match.home_team.external_id
            )

            away_external_id = (
                match.away_team.external_id
            )


            h2h_home_score = 5.0
            h2h_away_score = 5.0
            h2h_matches_count = 0


            if (
                home_external_id
                and
                away_external_id
            ):

                h2h_matches = (
                    db.query(H2HMatch)
                    .filter(

                        H2HMatch.match_date
                        < match.match_date,

                        (
                            (
                                H2HMatch.home_team_external_id
                                == home_external_id
                            )
                            &
                            (
                                H2HMatch.away_team_external_id
                                == away_external_id
                            )
                        )
                        |
                        (
                            (
                                H2HMatch.home_team_external_id
                                == away_external_id
                            )
                            &
                            (
                                H2HMatch.away_team_external_id
                                == home_external_id
                            )
                        )
                    )
                    .order_by(
                        H2HMatch
                        .match_date
                        .desc()
                    )
                    .limit(5)
                    .all()
                )


                h2h_matches_count = (
                    len(
                        h2h_matches
                    )
                )


                if h2h_matches:

                    scores = (
                        calculate_h2h_scores(
                            matches=
                                h2h_matches,

                            home_team_external_id=
                                home_external_id,
                        )
                    )


                    h2h_home_score = (
                        scores[
                            "home_score"
                        ]
                    )


                    h2h_away_score = (
                        scores[
                            "away_score"
                        ]
                    )


            # =================================================
            # TARGET
            # =================================================

            result = get_result(
                match.home_score,
                match.away_score,
            )


            total_goals = (
                match.home_score
                +
                match.away_score
            )


            over_25 = (
                1
                if total_goals > 2.5
                else 0
            )


            btts = (
                1
                if (
                    match.home_score > 0
                    and
                    match.away_score > 0
                )
                else 0
            )


            # =================================================
            # ENGINEERED FEATURES
            # =================================================

            form_diff = (
                home_form[
                    "form_score"
                ]
                -
                away_form[
                    "form_score"
                ]
            )


            goals_diff = (
                home_form[
                    "goals_for_avg"
                ]
                -
                away_form[
                    "goals_for_avg"
                ]
            )


            defense_diff = (
                away_form[
                    "goals_against_avg"
                ]
                -
                home_form[
                    "goals_against_avg"
                ]
            )


            xg_diff = (
                home_xg
                -
                away_xg
            )


            h2h_diff = (
                h2h_home_score
                -
                h2h_away_score
            )


            home_strength = (
                home_form[
                    "goals_for_avg"
                ]
                +
                away_form[
                    "goals_against_avg"
                ]
            )


            away_strength = (
                away_form[
                    "goals_for_avg"
                ]
                +
                home_form[
                    "goals_against_avg"
                ]
            )


            home_away_context_diff = (
                home_context[
                    "points_per_game"
                ]
                -
                away_context[
                    "points_per_game"
                ]
            )


            recent_form_diff_3 = (
                home_form_3[
                    "form_score"
                ]
                -
                away_form_3[
                    "form_score"
                ]
            )


            # =================================================
            # DATASET ROW
            # =================================================

            rows.append(
                {
                    "match_id":
                        match.id,

                    "match_date":
                        match.match_date,

                    "league":
                        match.league.name,

                    "home_team":
                        match.home_team.name,

                    "away_team":
                        match.away_team.name,


                    # =========================================
                    # GENERAL FORM
                    # =========================================

                    "home_form":
                        home_form[
                            "form_score"
                        ],

                    "away_form":
                        away_form[
                            "form_score"
                        ],


                    "home_goals_avg":
                        home_form[
                            "goals_for_avg"
                        ],

                    "away_goals_avg":
                        away_form[
                            "goals_for_avg"
                        ],


                    "home_goals_against_avg":
                        home_form[
                            "goals_against_avg"
                        ],

                    "away_goals_against_avg":
                        away_form[
                            "goals_against_avg"
                        ],


                    # =========================================
                    # ROLLING 3
                    # =========================================

                    "home_form_3":
                        home_form_3[
                            "form_score"
                        ],

                    "away_form_3":
                        away_form_3[
                            "form_score"
                        ],

                    "recent_form_diff_3":
                        recent_form_diff_3,


                    # =========================================
                    # HOME/AWAY CONTEXT
                    # =========================================

                    "home_home_ppg":
                        home_context[
                            "points_per_game"
                        ],

                    "away_away_ppg":
                        away_context[
                            "points_per_game"
                        ],


                    "home_home_goals_avg":
                        home_context[
                            "goals_for_avg"
                        ],

                    "away_away_goals_avg":
                        away_context[
                            "goals_for_avg"
                        ],


                    "home_home_conceded_avg":
                        home_context[
                            "goals_against_avg"
                        ],

                    "away_away_conceded_avg":
                        away_context[
                            "goals_against_avg"
                        ],


                    "home_home_goal_diff_avg":
                        home_context[
                            "goal_difference_avg"
                        ],

                    "away_away_goal_diff_avg":
                        away_context[
                            "goal_difference_avg"
                        ],


                    "home_home_clean_sheet_rate":
                        home_context[
                            "clean_sheet_rate"
                        ],

                    "away_away_clean_sheet_rate":
                        away_context[
                            "clean_sheet_rate"
                        ],


                    "home_home_failed_score_rate":
                        home_context[
                            "failed_to_score_rate"
                        ],

                    "away_away_failed_score_rate":
                        away_context[
                            "failed_to_score_rate"
                        ],


                    "home_home_win_rate":
                        home_context[
                            "win_rate"
                        ],

                    "away_away_win_rate":
                        away_context[
                            "win_rate"
                        ],


                    "home_away_context_diff":
                        home_away_context_diff,


                    # =========================================
                    # XG
                    # =========================================

                    "home_xg":
                        home_xg,

                    "away_xg":
                        away_xg,


                    # =========================================
                    # OPTIONAL ODDS
                    # =========================================

                    "home_odds":
                        home_odds,

                    "draw_odds":
                        draw_odds,

                    "away_odds":
                        away_odds,

                    "has_odds":
                        has_odds,


                    # =========================================
                    # H2H
                    # =========================================

                    "h2h_home_score":
                        h2h_home_score,

                    "h2h_away_score":
                        h2h_away_score,

                    "h2h_matches":
                        h2h_matches_count,


                    # =========================================
                    # EXISTING ENGINEERED FEATURES
                    # =========================================

                    "form_diff":
                        form_diff,

                    "goals_diff":
                        goals_diff,

                    "defense_diff":
                        defense_diff,

                    "xg_diff":
                        xg_diff,

                    "h2h_diff":
                        h2h_diff,

                    "home_strength":
                        home_strength,

                    "away_strength":
                        away_strength,


                    # =========================================
                    # FINAL SCORE / TARGETS
                    # =========================================

                    "home_score":
                        match.home_score,

                    "away_score":
                        match.away_score,

                    "result":
                        result,

                    "over_25":
                        over_25,

                    "btts":
                        btts,
                }
            )


            print(
                f"Added: "
                f"{result}"
            )


        # =====================================================
        # SAVE CSV
        # =====================================================

        if rows:

            with OUTPUT_FILE.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = (
                    csv.DictWriter(
                        file,
                        fieldnames=
                            list(
                                rows[0]
                                .keys()
                            ),
                    )
                )


                writer.writeheader()


                writer.writerows(
                    rows
                )


        # =====================================================
        # SUMMARY
        # =====================================================

        print()
        print("=" * 70)
        print(
            "DATASET V3 COMPLETE"
        )
        print("=" * 70)


        print(
            f"Rows created: "
            f"{len(rows)}"
        )


        print(
            f"Missing score: "
            f"{skipped_no_score}"
        )


        print(
            f"Missing history: "
            f"{skipped_no_history}"
        )


        if rows:

            print()
            print(
                f"Saved to: "
                f"{OUTPUT_FILE.resolve()}"
            )


    finally:

        db.close()


if __name__ == "__main__":
    run()