import os
import subprocess
import sys
import time

from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[1]

LOG_DIR = (
    BASE_DIR
    / "logs"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# PIPELINE STEPS
#
# ORDER:
#
# 1. Sync finished results
# 2. Evaluate existing Rule snapshots
# 3. Evaluate existing ML snapshots
# 4. Evaluate existing VALUE snapshots
# 5. Refresh selected upcoming fixtures
# 6. Create/update ML snapshots
# 7. Refresh odds
# 8. Create/update Rule snapshots
# 9. Create/update VALUE snapshots
# 10. Pipeline health
#
# VALUE snapshots depend on:
# - ML snapshots
# - odds
#
# so Snapshot VALUE must run AFTER both.
# ============================================================

STEPS = [
    {
        "name":
            "Sync Results",

        "module":
            "scripts.sync_results",

        "api_heavy":
            True,
    },

    {
        "name":
            "Evaluate Rule Predictions",

        "module":
            "scripts.evaluate_predictions",

        "api_heavy":
            False,
    },

    {
        "name":
            "Evaluate ML Predictions",

        "module":
            "scripts.evaluate_ml_predictions",

        "api_heavy":
            False,
    },

    {
        "name":
            "Evaluate VALUE Predictions",

        "module":
            "scripts.evaluate_value_predictions",

        "api_heavy":
            False,
    },

    {
        "name":
            "Sync Selected Fixtures",

        "module":
            "scripts.sync_selected_fixtures",

        "api_heavy":
            True,
    },

    {
        "name":
            "Snapshot ML Predictions",

        "module":
            "scripts.snapshot_ml_predictions",

        "api_heavy":
            False,
    },

    {
        "name":
            "Sync Odds",

        "module":
            "scripts.sync_odds",

        "api_heavy":
            True,
    },

    {
        "name":
            "Snapshot Rule Predictions",

        "module":
            "scripts.snapshot_predictions",

        "api_heavy":
            False,
    },

    {
        "name":
            "Snapshot VALUE Predictions",

        "module":
            "scripts.snapshot_value_predictions",

        "api_heavy":
            False,
    },

    {
        "name":
            "Pipeline Health",

        "module":
            "scripts.pipeline_health",

        "api_heavy":
            False,
    },
]


# ============================================================
# ENVIRONMENT
# ============================================================

def build_environment():

    env = os.environ.copy()

    # Windows UTF-8 protection
    env[
        "PYTHONIOENCODING"
    ] = "utf-8"

    env[
        "PYTHONUTF8"
    ] = "1"

    return env


# ============================================================
# LOGGING
# ============================================================

def get_log_path():

    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    return (
        LOG_DIR
        / (
            f"full_pipeline_"
            f"{timestamp}.log"
        )
    )


def write_log(
    log_file,
    text,
):

    with open(
        log_file,
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            str(text)
        )

        if not str(
            text
        ).endswith(
            "\n"
        ):

            file.write(
                "\n"
            )


# ============================================================
# DISPLAY
# ============================================================

def print_section(
    title,
):

    print()

    print(
        "=" * 78
    )

    print(
        title.upper()
    )

    print(
        "=" * 78
    )


# ============================================================
# EXECUTE MODULE
# ============================================================

def execute_module(
    module,
    log_file,
):

    env = build_environment()

    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        module,
    ]

    process = subprocess.run(
        command,
        cwd=str(
            BASE_DIR
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    output = (
        process.stdout
        or ""
    )

    if output:

        print(
            output,
            end=""
            if output.endswith(
                "\n"
            )
            else "\n",
        )

        write_log(
            log_file,
            output,
        )

    return (
        process.returncode,
        output,
    )


# ============================================================
# DETECT STATUS
# ============================================================

def detect_step_status(
    return_code,
    output,
):
    """
    FAILED:
        Python process crashed / returned non-zero.

    PARTIAL:
        Process completed but data refresh was degraded,
        for example because an external API hit rate limit.

    OK:
        Process completed with no detected degradation.
    """

    if return_code != 0:

        return "FAILED"

    normalized = (
        output
        or ""
    ).lower()

    # --------------------------------------------------------
    # External API degradation signals
    # --------------------------------------------------------

    partial_signals = [
        "rate limit reached",
        "too many requests",
        "ratelimit",
        "rate_limit",
    ]

    if any(
        signal in normalized
        for signal
        in partial_signals
    ):

        return "PARTIAL"

    return "OK"


# ============================================================
# RUN ONE STEP
# ============================================================

def run_step(
    index,
    total,
    step,
    log_file,
):

    name = (
        step[
            "name"
        ]
    )

    module = (
        step[
            "module"
        ]
    )

    api_heavy = (
        step[
            "api_heavy"
        ]
    )

    print()
    print(
        f"[{index}/{total}]"
    )

    print_section(
        name
    )

    write_log(
        log_file,
        (
            "\n"
            + "=" * 78
            + "\n"
            + (
                f"[{index}/{total}] "
                f"{name.upper()}"
            )
            + "\n"
            + "=" * 78
            + "\n"
        ),
    )

    start_time = (
        time.time()
    )

    # ========================================================
    # FIRST ATTEMPT
    # ========================================================

    return_code, output = (
        execute_module(
            module,
            log_file,
        )
    )

    retried = False

    # ========================================================
    # RETRY ONLY ON REAL PROCESS FAILURE
    #
    # We do NOT retry just because the API said rate limited.
    # The subprocess itself succeeded in that case.
    # ========================================================

    if (
        return_code != 0
        and api_heavy
    ):

        retried = True

        print()

        print(
            f"{name}: FAILED"
        )

        print(
            "Retrying once "
            "in 10 seconds..."
        )

        write_log(
            log_file,
            (
                f"\n{name}: FAILED\n"
                "Retrying once "
                "in 10 seconds...\n"
            ),
        )

        time.sleep(
            10
        )

        retry_return_code, (
            retry_output
        ) = execute_module(
            module,
            log_file,
        )

        return_code = (
            retry_return_code
        )

        if retry_output:

            output = (
                output
                + "\n"
                + retry_output
            )

    # ========================================================
    # STATUS
    # ========================================================

    status = (
        detect_step_status(
            return_code,
            output,
        )
    )

    duration = (
        time.time()
        - start_time
    )

    print()

    print(
        f"{name}: "
        f"{status}"
    )

    print(
        f"Duration: "
        f"{duration:.1f}s"
    )

    if retried:

        print(
            "Retry attempted: YES"
        )

    write_log(
        log_file,
        (
            f"\n{name}: "
            f"{status}\n"
            f"Duration: "
            f"{duration:.1f}s\n"
        ),
    )

    return {
        "name":
            name,

        "module":
            module,

        "status":
            status,

        "duration":
            duration,

        "retried":
            retried,
    }


# ============================================================
# MAIN PIPELINE
# ============================================================

def run():

    started_at = (
        datetime.now()
    )

    log_file = (
        get_log_path()
    )

    print()
    print(
        "=" * 78
    )

    print(
        "ANALITIKO FULL PIPELINE"
    )

    print(
        "=" * 78
    )

    print(
        "Started: "
        f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"Steps: "
        f"{len(STEPS)}"
    )

    print(
        f"Log: "
        f"{log_file}"
    )

    print(
        "=" * 78
    )

    write_log(
        log_file,
        (
            "=" * 78
            + "\n"
            + "ANALITIKO FULL PIPELINE\n"
            + "=" * 78
            + "\n"
            + (
                "Started: "
                f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            + "\n"
            + (
                f"Steps: "
                f"{len(STEPS)}"
            )
            + "\n"
            + "=" * 78
            + "\n"
        ),
    )

    results = []

    total_steps = (
        len(
            STEPS
        )
    )

    # ========================================================
    # RUN ALL STEPS
    # ========================================================

    for index, step in enumerate(
        STEPS,
        start=1,
    ):

        result = run_step(
            index=index,
            total=total_steps,
            step=step,
            log_file=log_file,
        )

        results.append(
            result
        )

    # ========================================================
    # COUNTS
    # ========================================================

    ok_count = sum(
        1
        for result
        in results
        if result[
            "status"
        ]
        == "OK"
    )

    partial_count = sum(
        1
        for result
        in results
        if result[
            "status"
        ]
        == "PARTIAL"
    )

    failed_count = sum(
        1
        for result
        in results
        if result[
            "status"
        ]
        == "FAILED"
    )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    if failed_count > 0:

        pipeline_status = (
            "FAILED"
        )

    elif partial_count > 0:

        pipeline_status = (
            "PARTIAL"
        )

    else:

        pipeline_status = (
            "HEALTHY"
        )

    # ========================================================
    # TIMING
    # ========================================================

    finished_at = (
        datetime.now()
    )

    total_duration = sum(
        result[
            "duration"
        ]
        for result
        in results
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print(
        "=" * 78
    )

    print(
        "FULL PIPELINE SUMMARY"
    )

    print(
        "=" * 78
    )

    print()

    for result in results:

        retry_text = (
            " retry"
            if result[
                "retried"
            ]
            else ""
        )

        print(
            f"{result['name']:<34}"
            f"{result['status']:<12}"
            f"{result['duration']:>8.1f}s"
            f"{retry_text}"
        )

    print()
    print(
        "-" * 78
    )

    print(
        f"OK: "
        f"{ok_count}"
    )

    print(
        f"Partial: "
        f"{partial_count}"
    )

    print(
        f"Failed: "
        f"{failed_count}"
    )

    print(
        f"Total steps: "
        f"{len(results)}"
    )

    print()

    print(
        f"Total duration: "
        f"{total_duration:.1f}s"
    )

    print(
        "Finished: "
        f"{finished_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print()

    print(
        "PIPELINE STATUS: "
        f"{pipeline_status}"
    )

    print(
        "=" * 78
    )

    # ========================================================
    # LOG SUMMARY
    # ========================================================

    write_log(
        log_file,
        (
            "\n"
            + "=" * 78
            + "\n"
            + "FULL PIPELINE SUMMARY\n"
            + "=" * 78
            + "\n"
        ),
    )

    for result in results:

        retry_text = (
            " retry"
            if result[
                "retried"
            ]
            else ""
        )

        write_log(
            log_file,
            (
                f"{result['name']:<34}"
                f"{result['status']:<12}"
                f"{result['duration']:>8.1f}s"
                f"{retry_text}"
            ),
        )

    write_log(
        log_file,
        (
            "\n"
            + "-" * 78
            + "\n"
            + (
                f"OK: "
                f"{ok_count}\n"
            )
            + (
                f"Partial: "
                f"{partial_count}\n"
            )
            + (
                f"Failed: "
                f"{failed_count}\n"
            )
            + (
                f"Total steps: "
                f"{len(results)}\n"
            )
            + "\n"
            + (
                f"Total duration: "
                f"{total_duration:.1f}s\n"
            )
            + (
                "Finished: "
                f"{finished_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            + "\n"
            + (
                "PIPELINE STATUS: "
                f"{pipeline_status}\n"
            )
            + "=" * 78
            + "\n"
        ),
    )

    # ========================================================
    # EXIT CODE
    #
    # PARTIAL is not a crash.
    # Only FAILED returns exit code 1.
    # ========================================================

    if failed_count > 0:

        sys.exit(
            1
        )


if __name__ == "__main__":
    run()