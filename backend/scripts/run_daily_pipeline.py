# backend/scripts/run_daily_pipeline.py

import subprocess
import sys

from datetime import datetime

from scripts.pipeline_logging import (
    write_log,
)


STEPS = [
    {
        "name": "Sync History",
        "module": "scripts.sync_history",
    },
    {
        "name": "Build Local History",
        "module": "scripts.build_history_from_matches",
    },
    {
        "name": "Pipeline Health",
        "module": "scripts.check_pipeline_health",
    },
]


LOG_FILE = (
    "daily_pipeline.log"
)


def run_step(
    name: str,
    module: str,
):

    print()
    print("=" * 72)
    print(name.upper())
    print("=" * 72)


    started_at = (
        datetime.now()
    )


    write_log(
        LOG_FILE,
        f"STEP STARTED | {name}",
    )


    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                module,
            ],
            check=False,
        )

        exit_code = (
            result.returncode
        )

        success = (
            exit_code == 0
        )


    except Exception as error:

        success = False
        exit_code = -1

        print(
            f"FAILED TO START: "
            f"{error}"
        )

        write_log(
            LOG_FILE,
            (
                f"STEP ERROR | "
                f"{name} | "
                f"{error}"
            ),
        )


    duration = (
        datetime.now()
        - started_at
    ).total_seconds()


    print()

    print(
        f"{name}: "
        f"{'OK' if success else 'FAILED'}"
    )

    print(
        f"Duration: "
        f"{duration:.1f}s"
    )


    write_log(
        LOG_FILE,
        (
            f"STEP FINISHED | "
            f"{name} | "
            f"{'OK' if success else 'FAILED'} | "
            f"duration={duration:.1f}s | "
            f"exit={exit_code}"
        ),
    )


    return {
        "name":
            name,

        "success":
            success,

        "duration":
            duration,

        "exit_code":
            exit_code,
    }


def run():

    started_at = (
        datetime.now()
    )


    write_log(
        LOG_FILE,
        (
            "DAILY PIPELINE STARTED | "
            f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        ),
    )


    print()
    print("=" * 72)
    print("ANALITIKO DAILY PIPELINE")
    print("=" * 72)

    print(
        f"Started: "
        f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )


    results = []


    for index, step in enumerate(
        STEPS,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(STEPS)}]"
        )


        result = (
            run_step(
                name=
                    step["name"],

                module=
                    step["module"],
            )
        )


        results.append(
            result
        )


    finished_at = (
        datetime.now()
    )


    total_duration = (
        finished_at
        - started_at
    ).total_seconds()


    failed = sum(
        1
        for item in results
        if not item[
            "success"
        ]
    )


    successful = (
        len(results)
        - failed
    )


    print()
    print("=" * 72)
    print("DAILY PIPELINE SUMMARY")
    print("=" * 72)

    print()


    for result in results:

        print(
            f"{result['name']:<32}"
            f"{'OK' if result['success'] else 'FAILED':<10}"
            f"{result['duration']:>7.1f}s"
        )


    print()
    print("-" * 72)

    print(
        f"Successful: "
        f"{successful}"
    )

    print(
        f"Failed: "
        f"{failed}"
    )

    print(
        f"Duration: "
        f"{total_duration:.1f}s"
    )

    print(
        f"Finished: "
        f"{finished_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )


    status = (
        "HEALTHY"
        if failed == 0
        else "COMPLETED WITH ERRORS"
    )


    print()

    print(
        f"PIPELINE STATUS: "
        f"{status}"
    )

    print("=" * 72)


    write_log(
        LOG_FILE,
        (
            "DAILY PIPELINE FINISHED | "
            f"successful={successful} | "
            f"failed={failed} | "
            f"duration={total_duration:.1f}s | "
            f"status={status}"
        ),
    )


if __name__ == "__main__":
    run()