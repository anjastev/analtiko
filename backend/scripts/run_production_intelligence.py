import subprocess
import sys


STEPS = [
    (
        "EVALUATE VALUE SIGNALS",
        "scripts.evaluate_production_signals",
    ),

    (
        "EVALUATE COMBINATIONS",
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
        "APPLY MARKET POLICY",
        "scripts.apply_market_policy",
    ),

    (
        "DIRECT MARKET ODDS",
        "scripts.sync_direct_market_odds",
    ),

    (
        "DIRECT DC ODDS",
        "scripts.sync_direct_dc_odds",
    ),

    (
        "DIRECT ODDS COVERAGE",
        "scripts.audit_direct_odds_coverage",
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
        "PROSPECTIVE SNAPSHOTS",
        "scripts.snapshot_market_evaluation",
    ),

    (
        "VALUE TEST",
        "scripts.test_value_pipeline",
    ),

    (
        "PRODUCTION COMBINATIONS",
        "scripts.build_multi_market_combinations",
    ),

    (
        "PERFORMANCE REPORT",
        "scripts.report_production_performance",
    ),

    (
        "PRODUCTION TEST",
        "scripts.test_production_pipeline",
    ),
]

def run():

    failures = 0

    print()
    print("=" * 100)
    print(
        "ANALITIKO PRODUCTION INTELLIGENCE PIPELINE"
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

        if (
            result.returncode
            != 0
        ):

            failures += 1

            print(
                f"[FAILED] "
                f"{title}"
            )

        else:

            print(
                f"[OK] "
                f"{title}"
            )

    print()
    print("=" * 100)

    if failures == 0:

        print(
            "PRODUCTION INTELLIGENCE: OK"
        )

    else:

        print(
            f"PRODUCTION INTELLIGENCE: "
            f"PARTIAL "
            f"({failures} failures)"
        )

    print("=" * 100)


if __name__ == "__main__":
    run()