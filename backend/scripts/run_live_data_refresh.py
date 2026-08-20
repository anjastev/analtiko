import subprocess
import sys


STEPS = [
    (
        "SYNC LIVE FIXTURES",
        "scripts.sync_live_fixtures",
    ),

    (
        "SYNC LIVE HISTORY",
        "scripts.sync_live_history",
    ),

    (
        "POST HISTORY AUDIT",
        "scripts.post_history_sync_audit",
    ),

    (
        "PRODUCTION READINESS",
        "scripts.audit_production_readiness",
    ),

    (
        "PRODUCTION INTELLIGENCE",
        "scripts.run_production_intelligence",
    ),
]


def run():

    failures = 0

    print()
    print("=" * 100)
    print(
        "ANALITIKO FULL LIVE DATA REFRESH"
    )
    print("=" * 100)

    for index, (
        name,
        module,
    ) in enumerate(
        STEPS,
        start=1,
    ):

        print()
        print("=" * 100)

        print(
            f"STEP {index}/"
            f"{len(STEPS)}: "
            f"{name}"
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
                f"{name}"
            )

        else:

            print(
                f"[OK] "
                f"{name}"
            )

    print()
    print("=" * 100)

    if failures == 0:

        print(
            "FULL LIVE DATA REFRESH: OK"
        )

    else:

        print(
            f"FULL LIVE DATA REFRESH: "
            f"PARTIAL "
            f"({failures} failures)"
        )

    print("=" * 100)


if __name__ == "__main__":
    run()