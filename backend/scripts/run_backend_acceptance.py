import subprocess
import sys


STEPS = [
    (
        "PRODUCTION READINESS",
        "scripts.audit_production_readiness",
    ),

    (
        "ODDS QUALITY",
        "scripts.audit_direct_odds_coverage",
    ),

    (
        "VALUE PIPELINE",
        "scripts.test_value_pipeline",
    ),

    (
        "PRODUCTION PIPELINE",
        "scripts.test_production_pipeline",
    ),

    (
        "DATABASE INTEGRITY",
        "scripts.audit_database_integrity",
    ),

    (
        "PRODUCTION SAFETY",
        "scripts.audit_production_safety",
    ),

    (
        "API CONTRACT",
        "scripts.test_api_contract",
    ),

    (
        "PERFORMANCE REPORT",
        "scripts.report_production_performance",
    ),
]


def run():

    failures = []

    print()
    print("=" * 100)
    print(
        "ANALITIKO BACKEND ACCEPTANCE"
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

        result = (
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    module,
                ],
                check=False,
            )
        )

        if result.returncode != 0:

            failures.append(
                title
            )

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
    print(
        "BACKEND ACCEPTANCE RESULT"
    )
    print("=" * 100)

    if not failures:

        print()
        print(
            "ANALITIKO BACKEND: "
            "PRODUCTION READY"
        )

        print()

        print(
            "All acceptance scripts "
            "completed successfully."
        )

    else:

        print()
        print(
            "ANALITIKO BACKEND: "
            "NOT READY"
        )

        print()

        print(
            "Failed steps:"
        )

        for failure in failures:

            print(
                f"  - {failure}"
            )

    print()
    print("=" * 100)

    if failures:

        raise SystemExit(1)


if __name__ == "__main__":
    run()