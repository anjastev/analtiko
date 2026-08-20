from __future__ import annotations


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


def evaluate_signal_anomaly(
    *,
    raw_probability: float,
    calibrated_probability: float,
    market_probability: float | None,
    edge: float | None,
    odds: float | None,
    expected_value: float | None,
    bookmaker: str | None,
):

    score = 0.0

    reasons = []

    raw_probability = float(
        raw_probability
    )

    calibrated_probability = float(
        calibrated_probability
    )

    edge_value = float(
        edge or 0.0
    )

    ev_value = float(
        expected_value or 0.0
    )

    # ========================================================
    # EXTREME MODEL CONFIDENCE
    # ========================================================

    if calibrated_probability >= 97.0:

        score += 30.0

        reasons.append(
            "EXTREME_PROBABILITY"
        )

    elif calibrated_probability >= 94.0:

        score += 15.0

        reasons.append(
            "VERY_HIGH_PROBABILITY"
        )

    # ========================================================
    # EXTREME EDGE
    # ========================================================

    if edge_value >= 60.0:

        score += 40.0

        reasons.append(
            "EXTREME_EDGE"
        )

    elif edge_value >= 45.0:

        score += 25.0

        reasons.append(
            "VERY_HIGH_EDGE"
        )

    elif edge_value >= 30.0:

        score += 10.0

        reasons.append(
            "HIGH_EDGE"
        )

    # ========================================================
    # EXTREME EV
    # ========================================================

    if ev_value >= 50.0:

        score += 25.0

        reasons.append(
            "EXTREME_EV"
        )

    elif ev_value >= 30.0:

        score += 12.0

        reasons.append(
            "HIGH_EV"
        )

    # ========================================================
    # MODEL / MARKET DISAGREEMENT
    # ========================================================

    if market_probability is None:

        score += 15.0

        reasons.append(
            "NO_MARKET_PROBABILITY"
        )

    else:

        disagreement = abs(
            calibrated_probability
            - float(
                market_probability
            )
        )

        if disagreement >= 45.0:

            score += 30.0

            reasons.append(
                "EXTREME_MARKET_DISAGREEMENT"
            )

        elif disagreement >= 30.0:

            score += 18.0

            reasons.append(
                "HIGH_MARKET_DISAGREEMENT"
            )

    # ========================================================
    # PRICE SANITY
    # ========================================================

    if (
        odds is None
        or float(odds) <= 1.0
    ):

        score += 50.0

        reasons.append(
            "INVALID_ODDS"
        )

    if not bookmaker:

        score += 10.0

        reasons.append(
            "NO_BOOKMAKER"
        )

    # ========================================================
    # PROBABILITY / PRICE CONSISTENCY
    # ========================================================

    if (
        odds is not None
        and float(odds) > 1.0
    ):

        raw_implied = (
            100.0
            / float(
                odds
            )
        )

        price_gap = abs(
            calibrated_probability
            - raw_implied
        )

        if price_gap >= 45.0:

            score += 20.0

            reasons.append(
                "EXTREME_PRICE_GAP"
            )

        elif price_gap >= 30.0:

            score += 10.0

            reasons.append(
                "HIGH_PRICE_GAP"
            )

    score = clamp(
        score,
        0.0,
        100.0,
    )

    if score >= 60:

        level = "CRITICAL"

    elif score >= 35:

        level = "HIGH"

    elif score >= 15:

        level = "WATCH"

    else:

        level = "NORMAL"

    return {
        "score":
            round(
                score,
                2,
            ),

        "level":
            level,

        "requires_review":
            score >= 35.0,

        "reasons":
            reasons,
    }