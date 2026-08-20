from datetime import (
    datetime,
    timezone,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match
from app.models.signal import Signal
from app.models.signal_intelligence import (
    SignalIntelligence,
)

from app.services.signal_quality_service import (
    build_signal_quality,
)


def run():

    db = SessionLocal()

    now = datetime.now(
        timezone.utc
    )

    # SQLite stores our timestamps as naive UTC.
    db_now = now.replace(
        tzinfo=None
    )

    created = 0
    unchanged = 0
    skipped = 0
    failed = 0

    try:

        # ====================================================
        # UPCOMING ACTIVE SIGNALS
        # ====================================================

        signals = (
            db.query(Signal)
            .join(
                Match,
                Match.id
                == Signal.match_id,
            )
            .filter(
                Signal.active.is_(True),

                Match.match_date
                > db_now,
            )
            .all()
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO SIGNAL INTELLIGENCE"
        )
        print("=" * 100)

        print(
            f"Signals: {len(signals)}"
        )

        # ====================================================
        # PROCESS SIGNALS
        # ====================================================

        for signal in signals:

            try:

                result = (
                    build_signal_quality(
                        db,
                        signal=signal,
                    )
                )

                if result is None:

                    skipped += 1

                    print()
                    print(
                        f"[SKIPPED] "
                        f"Signal {signal.id}"
                    )

                    continue

                # ============================================
                # LATEST SNAPSHOT
                # ============================================

                latest = (
                    db.query(
                        SignalIntelligence
                    )
                    .filter(
                        SignalIntelligence.signal_id
                        == signal.id
                    )
                    .order_by(
                        SignalIntelligence
                        .calculated_at
                        .desc(),

                        SignalIntelligence
                        .id
                        .desc(),
                    )
                    .first()
                )

                # ============================================
                # DUPLICATE STATE CHECK
                # ============================================

                same_state = False

                if latest is not None:

                    latest_anomaly_score = float(
                        latest.anomaly_score
                        or 0.0
                    )

                    result_anomaly_score = float(
                        result.get(
                            "anomaly_score",
                            0.0,
                        )
                    )

                    same_state = (
                        abs(
                            float(
                                latest.quality_score
                            )
                            -
                            float(
                                result[
                                    "quality_score"
                                ]
                            )
                        )
                        < 0.0001

                        and

                        abs(
                            float(
                                latest.uncertainty
                            )
                            -
                            float(
                                result[
                                    "uncertainty"
                                ]
                            )
                        )
                        < 0.0001

                        and

                        int(
                            latest.production_eligible
                        )
                        ==
                        int(
                            result[
                                "production_eligible"
                            ]
                        )

                        and

                        abs(
                            latest_anomaly_score
                            -
                            result_anomaly_score
                        )
                        < 0.0001

                        and

                        (
                            latest.anomaly_level
                            or "NORMAL"
                        )
                        ==
                        result.get(
                            "anomaly_level",
                            "NORMAL",
                        )

                        and

                        int(
                            latest.requires_review
                            or 0
                        )
                        ==
                        int(
                            result.get(
                                "requires_review",
                                False,
                            )
                        )
                    )

                if same_state:

                    unchanged += 1

                    continue

                # ============================================
                # CREATE SNAPSHOT
                # ============================================

                row = SignalIntelligence(

                    signal_id=(
                        signal.id
                    ),

                    match_id=(
                        signal.match_id
                    ),

                    raw_probability=(
                        result[
                            "raw_probability"
                        ]
                    ),

                    calibrated_probability=(
                        result[
                            "calibrated_probability"
                        ]
                    ),

                    calibration_status=(
                        result[
                            "calibration_status"
                        ]
                    ),

                    uncertainty=(
                        result[
                            "uncertainty"
                        ]
                    ),

                    data_quality_score=(
                        result[
                            "data_quality_score"
                        ]
                    ),

                    market_agreement_score=(
                        result[
                            "market_agreement_score"
                        ]
                    ),

                    league_reliability=(
                        result[
                            "league_reliability"
                        ]
                    ),

                    elo_confidence=(
                        result[
                            "elo_confidence"
                        ]
                    ),

                    quality_score=(
                        result[
                            "quality_score"
                        ]
                    ),

                    quality_tier=(
                        result[
                            "quality_tier"
                        ]
                    ),

                    production_eligible=int(
                        result[
                            "production_eligible"
                        ]
                    ),

                    # ========================================
                    # ANOMALY
                    # ========================================

                    anomaly_score=float(
                        result.get(
                            "anomaly_score",
                            0.0,
                        )
                    ),

                    anomaly_level=(
                        result.get(
                            "anomaly_level",
                            "NORMAL",
                        )
                    ),

                    requires_review=int(
                        result.get(
                            "requires_review",
                            False,
                        )
                    ),

                    calculated_at=(
                        db_now
                    ),
                )

                db.add(
                    row
                )

                created += 1

                # ============================================
                # OUTPUT
                # ============================================

                match = (
                    result[
                        "match"
                    ]
                )

                print()
                print("-" * 100)

                print(
                    f"{match.home_team.name} "
                    f"vs "
                    f"{match.away_team.name}"
                )

                print(
                    f"Signal ID: "
                    f"{signal.id}"
                )

                print(
                    f"Raw probability: "
                    f"{result['raw_probability']:.1f}%"
                )

                print(
                    f"Calibrated: "
                    f"{result['calibrated_probability']:.1f}%"
                )

                print(
                    f"Quality: "
                    f"{result['quality_score']:.1f} "
                    f"({result['quality_tier']})"
                )

                print(
                    f"Uncertainty: "
                    f"{result['uncertainty']:.1f}%"
                )

                print(
                    f"Data quality: "
                    f"{result['data_quality_score']:.2f}"
                )

                print(
                    f"Market agreement: "
                    f"{result['market_agreement_score']:.2f}"
                )

                print(
                    f"League reliability: "
                    f"{result['league_reliability']:.2f}"
                )

                print(
                    f"Elo confidence: "
                    f"{result['elo_confidence']:.2f}"
                )

                print(
                    f"Anomaly: "
                    f"{result.get('anomaly_score', 0.0):.1f} "
                    f"("
                    f"{result.get('anomaly_level', 'NORMAL')}"
                    f")"
                )

                print(
                    f"Requires review: "
                    f"{result.get('requires_review', False)}"
                )

                reasons = result.get(
                    "anomaly_reasons",
                    [],
                )

                if reasons:

                    print(
                        "Anomaly reasons: "
                        + ", ".join(
                            reasons
                        )
                    )

                print(
                    f"Production eligible: "
                    f"{result['production_eligible']}"
                )

            except Exception as error:

                failed += 1

                db.rollback()

                print()
                print("-" * 100)

                print(
                    f"[FAILED] "
                    f"Signal {signal.id}"
                )

                print(
                    f"{type(error).__name__}: "
                    f"{error}"
                )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # SUMMARY
        # ====================================================

        print()
        print("=" * 100)
        print(
            "SIGNAL INTELLIGENCE SUMMARY"
        )
        print("=" * 100)

        print(
            f"Signals checked: "
            f"{len(signals)}"
        )

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

        if failed == 0:

            print(
                "STATUS: OK"
            )

        elif created > 0:

            print(
                "STATUS: PARTIAL"
            )

        else:

            print(
                "STATUS: FAILED"
            )

        print("=" * 100)

        if (
            failed > 0
            and
            created == 0
        ):

            raise SystemExit(1)

    finally:

        db.close()


if __name__ == "__main__":
    run()