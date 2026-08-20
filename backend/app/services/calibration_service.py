from __future__ import annotations


BASE_RATE = 50.0

MAX_SHRINKAGE = 0.18


def provisional_calibration(
    *,
    raw_probability: float,
    league_reliability: float,
    data_quality: float,
) -> dict:

    raw_probability = max(
        0.0,
        min(
            100.0,
            float(raw_probability),
        ),
    )

    reliability = max(
        0.0,
        min(
            1.0,
            float(league_reliability),
        ),
    )

    quality = max(
        0.0,
        min(
            1.0,
            float(data_quality),
        ),
    )

    weakness = (
        1.0
        - (
            reliability
            * quality
        )
    )

    shrinkage = min(
        MAX_SHRINKAGE,
        weakness
        * MAX_SHRINKAGE,
    )

    calibrated = (
        raw_probability
        * (
            1.0
            - shrinkage
        )
        +
        BASE_RATE
        * shrinkage
    )

    return {
        "probability":
            round(
                calibrated,
                4,
            ),

        "shrinkage":
            round(
                shrinkage,
                6,
            ),

        "status":
            "PROVISIONAL",
    }