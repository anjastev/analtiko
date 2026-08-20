from dataclasses import dataclass


# ============================================================
# RESEARCH THRESHOLDS
# ============================================================

STRONG_THRESHOLD = 75.0
ELITE_THRESHOLD = 80.0
ULTRA_THRESHOLD = 85.0


# ============================================================
# RESULT
# ============================================================

@dataclass
class SignalDecision:
    qualifies: bool
    signal_type: str | None
    confidence_score: float
    risk_level: str | None


# ============================================================
# ENGINE
# ============================================================

def evaluate_prediction_signal(
    probability: float,
) -> SignalDecision:
    """
    Evaluate a market probability and decide whether it
    qualifies as a recommendation signal.

    IMPORTANT:
    These are research/product thresholds only.
    They are NOT validated realized-accuracy thresholds yet.
    """

    probability = float(
        probability
    )

    # ========================================================
    # ULTRA
    # ========================================================

    if probability >= ULTRA_THRESHOLD:

        return SignalDecision(
            qualifies=True,
            signal_type="ULTRA",
            confidence_score=probability,
            risk_level="LOW",
        )

    # ========================================================
    # ELITE
    # ========================================================

    if probability >= ELITE_THRESHOLD:

        return SignalDecision(
            qualifies=True,
            signal_type="ELITE",
            confidence_score=probability,
            risk_level="LOW_MEDIUM",
        )

    # ========================================================
    # STRONG
    # ========================================================

    if probability >= STRONG_THRESHOLD:

        return SignalDecision(
            qualifies=True,
            signal_type="STRONG",
            confidence_score=probability,
            risk_level="MEDIUM",
        )

    # ========================================================
    # NO SIGNAL
    # ========================================================

    return SignalDecision(
        qualifies=False,
        signal_type=None,
        confidence_score=probability,
        risk_level=None,
    )