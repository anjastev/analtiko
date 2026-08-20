from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.h2h import H2HMatch
from app.models.market import Market
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.match import Match
from app.models.match_stats import MatchStats
from app.models.team_match_history import (
    TeamMatchHistory,
)

from app.analytics.h2h import (
    calculate_h2h_scores,
)
from app.analytics.team_form import (
    calculate_form_from_history,
)

from app.ml.football_market_predictor import (
    predict_btts,
    predict_over25,
)


UPCOMING_WINDOW_DAYS = 3

FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}

MODEL_VERSION_OVER25 = (
    "logistic_regression_over25_v1"
)

MODEL_VERSION_BTTS = (
    "logistic_regression_btts_v1"
)


def get_market(
    db,
    code: str,
):

    return (
        db.query(Market)
        .filter(
            Market.sport
            == "football",

            Market.code
            == code,
        )
        .first()
    )


def prediction_exists(
    db,
    match_id: int,
    market_id: int,
    selection: str,
    model_version: str,
):

    return (
        db.query(
            MarketPrediction
        )
        .filter(
            MarketPrediction.match_id
            == match_id,

            MarketPrediction.market_id
            == market_id,

            MarketPrediction.selection
            == selection,

            MarketPrediction.model_version
            == model_version,

            MarketPrediction.actual_result
            .is_(None),
        )
        .first()
        is not None
    )


def save_prediction(
    db,
    match_id: int,
    market_id: int,
    selection: str,
    probability: float,
    model_version: str,
):

    if prediction_exists(
        db=db,
        match_id=match_id,
        market_id=market_id,
        selection=selection,
        model_version=model_version,
    ):
        return False

    level = "LOW"

    if probability >= 85:
        level = "ULTRA"

    elif probability >= 80:
        level = "ELITE"

    elif probability >= 75:
        level = "STRONG"

    elif probability >= 60:
        level = "MEDIUM"

    row = MarketPrediction(
        match_id=match_id,
        market_id=market_id,
        model_version=model_version,
        selection=selection,
        probability=probability,
        confidence=probability,
        confidence_level=level,
        is_recommended=(
            probability >= 75
        ),
    )

    db.add(
        row
    )

    return True


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    end = (
        now
        + timedelta(
            days=UPCOMING_WINDOW_DAYS
        )
    )

    created = 0
    unchanged = 0
    skipped = 0
    failed = 0

    try:

        market_ou25 = (
            get_market(
                db,
                "OU_25",
            )
        )

        market_btts = (
            get_market(
                db,
                "BTTS",
            )
        )

        if (
            market_ou25 is None
            or market_btts is None
        ):

            raise RuntimeError(
                "OU_25 or BTTS market missing."
            )

        matches = (
            db.query(Match)
            .filter(
                Match.match_date
                >= now,

                Match.match_date
                <= end,

                ~Match.status.in_(
                    FINISHED_STATUSES
                ),
            )
            .order_by(
                Match.match_date.asc()
            )
            .all()
        )

        print()
        print("=" * 80)
        print(
            "ANALITIKO EXTRA MARKET SNAPSHOTS"
        )
        print("=" * 80)

        print(
            f"Matches: "
            f"{len(matches)}"
        )

        for match in matches:

            print()
            print("-" * 80)

            print(
                f"[{match.id}] "
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            try:

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
                        TeamMatchHistory.match_date
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
                        TeamMatchHistory.match_date
                        .desc()
                    )
                    .limit(5)
                    .all()
                )

                if (
                    not home_history
                    or not away_history
                ):

                    skipped += 1

                    print(
                        "Skipped: no_history"
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
                        is not None
                        and
                        stats.home_xg_avg > 0
                    ):

                        home_xg = float(
                            stats.home_xg_avg
                        )

                    if (
                        stats.away_xg_avg
                        is not None
                        and
                        stats.away_xg_avg > 0
                    ):

                        away_xg = float(
                            stats.away_xg_avg
                        )

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
                    and away_external_id
                ):

                    h2h_matches = (
                        db.query(H2HMatch)
                        .filter(
                            H2HMatch.match_date
                            < match.match_date,

                            (
                                (
                                    H2HMatch
                                    .home_team_external_id
                                    == home_external_id
                                )
                                &
                                (
                                    H2HMatch
                                    .away_team_external_id
                                    == away_external_id
                                )
                            )
                            |
                            (
                                (
                                    H2HMatch
                                    .home_team_external_id
                                    == away_external_id
                                )
                                &
                                (
                                    H2HMatch
                                    .away_team_external_id
                                    == home_external_id
                                )
                            )
                        )
                        .order_by(
                            H2HMatch.match_date
                            .desc()
                        )
                        .limit(5)
                        .all()
                    )

                    h2h_matches_count = (
                        len(h2h_matches)
                    )

                    if h2h_matches:

                        scores = (
                            calculate_h2h_scores(
                                matches=(
                                    h2h_matches
                                ),
                                home_team_external_id=(
                                    home_external_id
                                ),
                            )
                        )

                        h2h_home_score = float(
                            scores[
                                "home_score"
                            ]
                        )

                        h2h_away_score = float(
                            scores[
                                "away_score"
                            ]
                        )

                features = {
                    "league":
                        match.league.name,

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

                    "home_xg":
                        home_xg,

                    "away_xg":
                        away_xg,

                    "h2h_home_score":
                        h2h_home_score,

                    "h2h_away_score":
                        h2h_away_score,

                    "h2h_matches":
                        h2h_matches_count,
                }

                over25 = (
                    predict_over25(
                        **features
                    )
                )

                btts = (
                    predict_btts(
                        **features
                    )
                )

                print(
                    "OU_25: "
                    f"OVER="
                    f"{over25['probabilities']['OVER']}% "
                    f"UNDER="
                    f"{over25['probabilities']['UNDER']}%"
                )

                print(
                    "BTTS: "
                    f"YES="
                    f"{btts['probabilities']['YES']}% "
                    f"NO="
                    f"{btts['probabilities']['NO']}%"
                )

                rows = [
                    (
                        market_ou25,
                        "OVER",
                        over25[
                            "probabilities"
                        ][
                            "OVER"
                        ],
                        MODEL_VERSION_OVER25,
                    ),
                    (
                        market_ou25,
                        "UNDER",
                        over25[
                            "probabilities"
                        ][
                            "UNDER"
                        ],
                        MODEL_VERSION_OVER25,
                    ),
                    (
                        market_btts,
                        "YES",
                        btts[
                            "probabilities"
                        ][
                            "YES"
                        ],
                        MODEL_VERSION_BTTS,
                    ),
                    (
                        market_btts,
                        "NO",
                        btts[
                            "probabilities"
                        ][
                            "NO"
                        ],
                        MODEL_VERSION_BTTS,
                    ),
                ]

                for (
                    market,
                    selection,
                    probability,
                    model_version,
                ) in rows:

                    if save_prediction(
                        db=db,
                        match_id=match.id,
                        market_id=market.id,
                        selection=selection,
                        probability=probability,
                        model_version=model_version,
                    ):

                        created += 1

                    else:

                        unchanged += 1

                db.commit()

            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"FAILED: "
                    f"{error}"
                )

        print()
        print("=" * 80)
        print(
            "EXTRA MARKET SNAPSHOT SUMMARY"
        )
        print("=" * 80)

        print(
            f"Created: "
            f"{created}"
        )

        print(
            f"Unchanged: "
            f"{unchanged}"
        )

        print(
            f"Skipped: "
            f"{skipped}"
        )

        print(
            f"Failed: "
            f"{failed}"
        )

        print()

        print(
            "STATUS: "
            + (
                "OK"
                if failed == 0
                else "PARTIAL"
            )
        )

        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    run()