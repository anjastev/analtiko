import subprocess
import sys
import time
import os
from datetime import datetime

from scripts.pipeline_logging import (
    write_log,
)


try:
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )

    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace",
    )

except Exception:
    pass

STEPS = [
    {
        "name": "Sync Results",
        "module": "scripts.sync_results",
        "retry": True,
    },
    {
        "name": "Evaluate Rule Predictions",
        "module": "scripts.evaluate_predictions",
        "retry": False,
    },
    {
        "name": "Evaluate ML Predictions",
        "module": "scripts.evaluate_ml_predictions",
        "retry": False,
    },
    {
        "name": "Sync Selected Fixtures",
        "module": "scripts.sync_selected_fixtures",
        "retry": True,
    },
    {
        "name": "Snapshot ML Predictions",
        "module": "scripts.snapshot_ml_predictions",
        "retry": False,
    },
    {
        "name": "Sync Odds",
        "module": "scripts.sync_odds",
        "retry": True,
    },
    {
        "name": "Snapshot Rule Predictions",
        "module": "scripts.snapshot_predictions",
        "retry": False,
    },
]


LOG_FILE = "hourly_pipeline.log"

RETRY_WAIT_SECONDS = 10


def log_child_output(
    name: str,
    output: str,
):

    if not output:
        return

    write_log(
        LOG_FILE,
        f"OUTPUT START | {name}",
    )

    for line in output.splitlines():

        if not line.strip():
            continue

        write_log(
            LOG_FILE,
            f"{name} | {line}",
        )

    write_log(
        LOG_FILE,
        f"OUTPUT END | {name}",
    )


def execute_module(
    name: str,
    module: str,
):

    started_at = datetime.now()

    try:

        env = os.environ.copy()

        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        result = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                module,
            ],
            check=False,

            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

            text=True,
            encoding="utf-8",
            errors="replace",

            env=env,
        )

        output = (
            result.stdout
            or ""
        )

        exit_code = (
            result.returncode
        )

        success = (
            exit_code == 0
        )

    except Exception as error:

        output = (
            f"Could not start process: "
            f"{error}"
        )

        exit_code = -1

        success = False


    duration = (
        datetime.now()
        - started_at
    ).total_seconds()


    # Still show child output
    # in PowerShell.

    if output:

        print(
            output,
            end=""
            if output.endswith("\n")
            else "\n",
        )


    # And save it in the log.

    log_child_output(
        name=name,
        output=output,
    )


    return {
        "success":
            success,

        "exit_code":
            exit_code,

        "duration":
            duration,

        "output":
            output,
    }


def run_step(
    *,
    name: str,
    module: str,
    allow_retry: bool,
):

    print()
    print("=" * 72)
    print(name.upper())
    print("=" * 72)


    write_log(
        LOG_FILE,
        f"STEP STARTED | {name}",
    )


    # ========================================================
    # FIRST ATTEMPT
    # ========================================================

    result = execute_module(
        name=name,
        module=module,
    )


    attempts = 1


    # ========================================================
    # ONE RETRY
    # ========================================================

    if (
        not result["success"]
        and allow_retry
    ):

        print()
        print(
            f"{name} failed."
        )

        print(
            f"Retrying once in "
            f"{RETRY_WAIT_SECONDS} seconds..."
        )


        write_log(
            LOG_FILE,
            (
                f"STEP RETRY SCHEDULED | "
                f"{name} | "
                f"wait={RETRY_WAIT_SECONDS}s"
            ),
        )


        time.sleep(
            RETRY_WAIT_SECONDS
        )


        attempts += 1


        print()
        print(
            f"Retry attempt for "
            f"{name}"
        )


        write_log(
            LOG_FILE,
            (
                f"STEP RETRY STARTED | "
                f"{name}"
            ),
        )


        retry_result = (
            execute_module(
                name=
                    f"{name} RETRY",

                module=
                    module,
            )
        )


        # Total duration includes both attempts.

        result = {
            "success":
                retry_result[
                    "success"
                ],

            "exit_code":
                retry_result[
                    "exit_code"
                ],

            "duration":
                (
                    result[
                        "duration"
                    ]
                    +
                    retry_result[
                        "duration"
                    ]
                    +
                    RETRY_WAIT_SECONDS
                ),

            "output":
                retry_result[
                    "output"
                ],
        }


    # ========================================================
    # RESULT
    # ========================================================

    print()

    print(
        f"{name}: "
        f"{'OK' if result['success'] else 'FAILED'}"
    )


    if attempts > 1:

        print(
            f"Attempts: "
            f"{attempts}"
        )


    print(
        f"Duration: "
        f"{result['duration']:.1f}s"
    )


    write_log(
        LOG_FILE,
        (
            f"STEP FINISHED | "
            f"{name} | "
            f"{'OK' if result['success'] else 'FAILED'} | "
            f"attempts={attempts} | "
            f"duration={result['duration']:.1f}s | "
            f"exit={result['exit_code']}"
        ),
    )


    return {
        "name":
            name,

        "success":
            result[
                "success"
            ],

        "duration":
            result[
                "duration"
            ],

        "exit_code":
            result[
                "exit_code"
            ],

        "attempts":
            attempts,
    }


def run():

    started_at = (
        datetime.now()
    )


    write_log(
        LOG_FILE,
        (
            "HOURLY PIPELINE STARTED | "
            f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        ),
    )


    print()
    print("=" * 72)
    print(
        "ANALITIKO HOURLY PIPELINE"
    )
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


        result = run_step(
            name=
                step[
                    "name"
                ],

            module=
                step[
                    "module"
                ],

            allow_retry=
                step[
                    "retry"
                ],
        )


        results.append(
            result
        )


    # ========================================================
    # SUMMARY
    # ========================================================

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
    print(
        "HOURLY PIPELINE SUMMARY"
    )
    print("=" * 72)

    print()


    for result in results:

        status = (
            "OK"
            if result[
                "success"
            ]
            else "FAILED"
        )


        retry_text = (
            "retry"
            if result[
                "attempts"
            ] > 1
            else ""
        )


        print(
            f"{result['name']:<32}"
            f"{status:<10}"
            f"{result['duration']:>7.1f}s "
            f"{retry_text}"
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
            "HOURLY PIPELINE FINISHED | "
            f"successful={successful} | "
            f"failed={failed} | "
            f"duration={total_duration:.1f}s | "
            f"status={status}"
        ),
    )


if __name__ == "__main__":
    run()