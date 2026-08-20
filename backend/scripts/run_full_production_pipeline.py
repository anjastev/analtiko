import subprocess
import sys


STEPS = [
    (
        "SYNC FIXTURES",
        "scripts.sync_live_fixtures",
    ),

    (
        "SYNC HISTORY",
        "scripts.sync_live_history",
    ),

    (
        "DATA QUALITY AUDIT",
        "scripts.audit_production_readiness",
    ),

    (
        "EVALUATE OLD VALUE SIGNALS",
        "scripts.evaluate_production_signals",
    ),

    (
        "EVALUATE OLD COMBINATIONS",
        "scripts.evaluate_combinations",
    ),

    (
        "ML PREDICTIONS",
        "scripts.snapshot_ml_predictions",
    ),

    (
        "MARKET PREDICTIONS",
        "scripts.snapshot_market_predictions",
    ),

    (
        "RESEARCH MARKET PREDICTIONS",
        "scripts.snapshot_extra_market_predictions",
    ),

    (
        "MARKET POLICY",
        "scripts.apply_market_policy",
    ),

    (
        "DIRECT ODDS",
        "scripts.sync_direct_market_odds",
    ),

    (
        "DIRECT DC ODDS",
        "scripts.sync_direct_dc_odds",
    ),

    (
        "ODDS COVERAGE",
        "scripts.audit_direct_odds_coverage",
    ),

(
    "MARKET CONSENSUS",
    "scripts.snapshot_market_consensus",
),

(
    "INTELLIGENCE FEATURES",
    "scripts.build_intelligence_features",
),



    (
        "PRODUCTION SIGNALS",
        "scripts.generate_multi_market_signals",
    ),

    (
        "VALUE ENRICHMENT",
        "scripts.enrich_production_signals_with_value",
    ),

    (
        "PROSPECTIVE EVALUATION SNAPSHOTS",
        "scripts.snapshot_market_evaluation",
    ),


(
    "LEAGUE RELIABILITY",
    "scripts.calculate_league_reliability",
),

(
    "SIGNAL INTELLIGENCE",
    "scripts.build_signal_intelligence",
),

(
    "TICKET OPTIMIZER AUDIT",
    "scripts.audit_ticket_optimizer",
),

    (
        "BUILD COMBINATIONS",
        "scripts.build_multi_market_combinations",
    ),

    (
        "PERFORMANCE REPORT",
        "scripts.report_production_performance",
    ),

    (
        "BACKEND ACCEPTANCE",
        "scripts.run_backend_acceptance",
    ),
]


def run():

    failed = []

    print()
    print("=" * 100)
    print(
        "ANALITIKO FULL PRODUCTION PIPELINE"
    )
    print("=" * 100)

    for index, (
        title,
        module,
    ) in enumerate(
        STEPS,
        start=1,
    ):

        print()
        print("=" * 100)

        print(
            f"STEP {index}/"
            f"{len(STEPS)} | "
            f"{title}"
        )

        print("=" * 100)

        result = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                module,
            ],
            check=False,
        )

        if result.returncode != 0:

            failed.append(
                title
            )

            print(
                f"[FAILED] "
                f"{title}"
            )

            # Production correctness:
            # stop after a critical failure.
            break

        print(
            f"[OK] "
            f"{title}"
        )

    print()
    print("=" * 100)

    if not failed:

        print(
            "ANALITIKO PRODUCTION PIPELINE: OK"
        )

    else:

        print(
            "ANALITIKO PRODUCTION PIPELINE: FAILED"
        )

        for title in failed:

            print(
                f"  - {title}"
            )

    print("=" * 100)

    if failed:

        raise SystemExit(1)


if __name__ == "__main__":
    run()