from __future__ import annotations

from math import exp

from sqlalchemy.orm import Session

from app.models.intelligence_feature_snapshot import (
    IntelligenceFeatureSnapshot,
)
from app.models.league_reliability import (
    LeagueReliability,
)
from app.models.match import Match
from app.models.signal import Signal
from app.models.team_power_rating import (
    TeamPowerRating,
)

from app.services.calibration_service import (
    provisional_calibration,
)

from app.services.signal_anomaly_service import (
    evaluate_signal_anomaly,
)

def clamp(
    value: float,
    low: float,
    high: float,
):

    return max(
        low,
        min(
            high,
            value,
        ),
    )


def latest_feature_snapshot(
    db: Session,
    match_id: int,
):

    return (
        db.query(
            IntelligenceFeatureSnapshot
        )
        .filter(
            IntelligenceFeatureSnapshot.match_id
            == match_id
        )
        .order_by(
            IntelligenceFeatureSnapshot
            .snapshot_at
            .desc(),

            IntelligenceFeatureSnapshot
            .id
            .desc(),
        )
        .first()
    )


def get_league_reliability(
    db: Session,
    match: Match,
):

    row = (
        db.query(
            LeagueReliability
        )
        .filter(
            LeagueReliability.league_id
            == match.league_id
        )
        .first()
    )

    if row is None:
        return 0.70

    return clamp(
        float(
            row.reliability_score
        ),
        0.40,
        1.00,
    )


def team_elo_experience(
    db: Session,
    team_id: int,
):

    return (
        db.query(
            TeamPowerRating
        )
        .filter(
            TeamPowerRating.team_id
            == team_id
        )
        .count()
    )


def calculate_elo_confidence(
    db: Session,
    match: Match,
):

    home_count = (
        team_elo_experience(
            db,
            match.home_team_id,
        )
    )

    away_count = (
        team_elo_experience(
            db,
            match.away_team_id,
        )
    )

    minimum = min(
        home_count,
        away_count,
    )

    # Saturates gradually.
    confidence = (
        1.0
        - exp(
            -minimum
            / 12.0
        )
    )

    return clamp(
        confidence,
        0.0,
        1.0,
    )


def calculate_data_quality(
    feature,
):

    if feature is None:
        return 0.25

    home_history = min(
        feature.home_history_count
        / 10.0,
        1.0,
    )

    away_history = min(
        feature.away_history_count
        / 10.0,
        1.0,
    )

    history_score = (
        home_history
        + away_history
    ) / 2.0

    has_market = all(
        value is not None
        for value in [
            feature.home_market_probability,
            feature.draw_market_probability,
            feature.away_market_probability,
        ]
    )

    market_score = (
        1.0
        if has_market
        else 0.55
    )

    score = (
        history_score
        * 0.70
        +
        market_score
        * 0.30
    )

    return clamp(
        score,
        0.0,
        1.0,
    )


def calculate_market_agreement(
    signal: Signal,
):

    if (
        signal.market_probability
        is None
    ):
        return 0.50

    difference = abs(
        float(
            signal.model_probability
        )
        -
        float(
            signal.market_probability
        )
    )

    # We do NOT want perfect agreement,
    # because VALUE requires disagreement.
    #
    # Moderate disagreement is healthy.
    # Extremely large disagreement is risky.

    if difference <= 5:
        score = 0.78

    elif difference <= 10:
        score = 1.00

    elif difference <= 15:
        score = 0.90

    elif difference <= 20:
        score = 0.75

    elif difference <= 30:
        score = 0.55

    else:
        score = 0.35

    return score


def calculate_uncertainty(
    *,
    raw_probability: float,
    calibrated_probability: float,
    data_quality: float,
    league_reliability: float,
    elo_confidence: float,
    market_agreement: float,
):

    calibration_gap = abs(
        raw_probability
        - calibrated_probability
    )

    probability_uncertainty = (
        max(
            0.0,
            1.0
            - abs(
                calibrated_probability
                - 50.0
            )
            / 50.0,
        )
    )

    uncertainty = (
        probability_uncertainty
        * 25.0
        +
        (
            1.0
            - data_quality
        )
        * 25.0
        +
        (
            1.0
            - league_reliability
        )
        * 20.0
        +
        (
            1.0
            - elo_confidence
        )
        * 15.0
        +
        (
            1.0
            - market_agreement
        )
        * 10.0
        +
        min(
            calibration_gap,
            10.0,
        )
        * 0.5
    )

    return clamp(
        uncertainty,
        0.0,
        100.0,
    )


def quality_tier(
    score: float,
):

    if score >= 85:
        return "A+"

    if score >= 78:
        return "A"

    if score >= 70:
        return "B"

    if score >= 60:
        return "C"

    return "D"


def build_signal_quality(
    db: Session,
    *,
    signal: Signal,
):

    match = (
        db.query(Match)
        .filter(
            Match.id
            == signal.match_id
        )
        .first()
    )

    if match is None:
        return None

    feature = (
        latest_feature_snapshot(
            db,
            signal.match_id,
        )
    )

    league_reliability = (
        get_league_reliability(
            db,
            match,
        )
    )

    data_quality = (
        calculate_data_quality(
            feature
        )
    )

    elo_confidence = (
        calculate_elo_confidence(
            db,
            match,
        )
    )

    market_agreement = (
        calculate_market_agreement(
            signal
        )
    )

    calibration = (
        provisional_calibration(
            raw_probability=(
                signal.model_probability
            ),

            league_reliability=(
                league_reliability
            ),

            data_quality=(
                data_quality
            ),
        )
    )

    calibrated_probability = (
        calibration[
            "probability"
        ]
    )

    uncertainty = (
        calculate_uncertainty(
            raw_probability=float(
                signal.model_probability
            ),

            calibrated_probability=(
                calibrated_probability
            ),

            data_quality=(
                data_quality
            ),

            league_reliability=(
                league_reliability
            ),

            elo_confidence=(
                elo_confidence
            ),

            market_agreement=(
                market_agreement
            ),
        )
    )

    edge_score = clamp(
        float(
            signal.edge
            or 0.0
        )
        / 15.0,
        0.0,
        1.0,
    )

    ev_score = clamp(
        float(
            signal.expected_value
            or 0.0
        )
        / 20.0,
        0.0,
        1.0,
    )

    probability_score = clamp(
        (
            calibrated_probability
            - 50.0
        )
        / 40.0,
        0.0,
        1.0,
    )

    uncertainty_score = (
        1.0
        - uncertainty
        / 100.0
    )

    quality = (
        probability_score
        * 22.0
        +
        edge_score
        * 18.0
        +
        ev_score
        * 12.0
        +
        data_quality
        * 15.0
        +
        league_reliability
        * 12.0
        +
        elo_confidence
        * 8.0
        +
        market_agreement
        * 5.0
        +
        uncertainty_score
        * 8.0
    )

    quality = clamp(
        quality,
        0.0,
        100.0,
    )

    tier = (
        quality_tier(
            quality
        )
    )

    anomaly = (
        evaluate_signal_anomaly(
            raw_probability=float(
                signal.model_probability
            ),

            calibrated_probability=(
                calibrated_probability
            ),

            market_probability=(
                signal.market_probability
            ),

            edge=(
                signal.edge
            ),

            odds=(
                signal.odds
            ),

            expected_value=(
                signal.expected_value
            ),

            bookmaker=(
                signal.bookmaker
            ),
        )
    )
    anomaly_penalty = (
            anomaly["score"]
            * 0.20
    )

    quality = clamp(
        quality
        - anomaly_penalty,
        0.0,
        100.0,
    )

    tier = (
        quality_tier(
            quality
        )
    )

    # ========================================================
    # PRODUCTION ELIGIBILITY
    #
    # HIGH / CRITICAL anomalies that require manual review
    # must never enter production tickets automatically.
    # ========================================================

    production_eligible = (
        bool(
            signal.active
        )
        and
        bool(
            signal.is_value
        )
        and
        signal.odds is not None
        and
        float(
            signal.edge
            or 0.0
        ) >= 5.0
        and
        float(
            signal.expected_value
            or 0.0
        ) > 0.0
        and
        data_quality >= 0.65
        and
        league_reliability >= 0.55
        and
        uncertainty <= 45.0
        and
        quality >= 60.0
        and
        anomaly[
            "level"
        ] != "CRITICAL"
        and
        not anomaly[
            "requires_review"
        ]
    )

    return {
        "match":
            match,

        "raw_probability":
            float(
                signal.model_probability
            ),

        "calibrated_probability":
            calibrated_probability,

        "calibration_status":
            calibration[
                "status"
            ],

        "uncertainty":
            round(
                uncertainty,
                4,
            ),

        "data_quality_score":
            round(
                data_quality,
                6,
            ),

        "market_agreement_score":
            round(
                market_agreement,
                6,
            ),

        "league_reliability":
            round(
                league_reliability,
                6,
            ),

        "elo_confidence":
            round(
                elo_confidence,
                6,
            ),

        "quality_score":
            round(
                quality,
                4,
            ),

        "quality_tier":
            tier,

        "production_eligible":
            production_eligible,

        "anomaly_score":
            anomaly[
                "score"
            ],

        "anomaly_level":
            anomaly[
                "level"
            ],

        "requires_review":
            anomaly[
                "requires_review"
            ],

        "anomaly_reasons":
            anomaly[
                "reasons"
            ],
    }