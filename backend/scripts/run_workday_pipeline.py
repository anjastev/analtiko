import os
import subprocess
import sys
import time

from datetime import (
    datetime,
    timedelta,
)
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


# Workday execution window.
#
# Pipeline runs once every hour:
#
# 08:00
# 09:00
# ...
# 16:00
#
# After the 16:00 run, the workday runner exits.

START_HOUR = 8
END_HOUR = 16

RUN_INTERVAL_HOURS = 1


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

    date_text = (
        datetime.now()
        .strftime(
            "%Y%m%d"
        )
    )

    return (
        LOG_DIR
        / (
            f"workday_pipeline_"
            f"{date_text}.log"
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
# TIME HELPERS
# ============================================================

def get_workday_start(
    now,
):

    return now.replace(
        hour=START_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )


def get_workday_end(
    now,
):

    return now.replace(
        hour=END_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )


def get_next_run_time(
    now,
):
    """
    Returns the next hourly execution time.

    Examples:

    07:30 -> 08:00
    08:15 -> 09:00
    12:02 -> 13:00
    15:45 -> 16:00
    after 16:00 -> None
    """

    workday_start = (
        get_workday_start(
            now
        )
    )

    workday_end = (
        get_workday_end(
            now
        )
    )

    # Before workday starts.
    if now < workday_start:

        return workday_start

    # After final execution time.
    if now >= workday_end:

        return None

    # Next full hour.
    next_run = (
        now.replace(
            minute=0,
            second=0,
            microsecond=0,
        )
        + timedelta(
            hours=RUN_INTERVAL_HOURS
        )
    )

    if next_run > workday_end:

        return None

    return next_run


# ============================================================
# PIPELINE EXECUTION
# ============================================================

def run_full_pipeline(
    log_file,
):

    env = build_environment()

    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "scripts.run_full_pipeline",
    ]

    started_at = (
        datetime.now()
    )

    print()
    print(
        "=" * 80
    )

    print(
        "WORKDAY PIPELINE RUN"
    )

    print(
        "=" * 80
    )

    print(
        "Started: "
        f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        "=" * 80
    )

    write_log(
        log_file,
        (
            "\n"
            + "=" * 80
            + "\n"
            + "WORKDAY PIPELINE RUN\n"
            + "=" * 80
            + "\n"
            + (
                "Started: "
                f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            + "=" * 80
            + "\n"
        ),
    )

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

    finished_at = (
        datetime.now()
    )

    duration = (
        finished_at
        - started_at
    ).total_seconds()

    # ========================================================
    # RESULT
    #
    # run_full_pipeline returns:
    #
    # 0 -> HEALTHY or PARTIAL
    # 1 -> at least one FAILED step
    # ========================================================

    if process.returncode == 0:

        status = (
            "COMPLETED"
        )

    else:

        status = (
            "FAILED"
        )

    print()
    print(
        "-" * 80
    )

    print(
        "Workday run status: "
        f"{status}"
    )

    print(
        f"Duration: "
        f"{duration:.1f}s"
    )

    print(
        "-" * 80
    )

    write_log(
        log_file,
        (
            "\n"
            + "-" * 80
            + "\n"
            + (
                "Workday run status: "
                f"{status}\n"
            )
            + (
                f"Duration: "
                f"{duration:.1f}s\n"
            )
            + "-" * 80
            + "\n"
        ),
    )

    return process.returncode


# ============================================================
# WAIT
# ============================================================

def wait_until(
    target_time,
):

    while True:

        now = (
            datetime.now()
        )

        remaining = (
            target_time
            - now
        ).total_seconds()

        if remaining <= 0:
            return

        # Sleep in smaller chunks so Ctrl+C stays responsive.
        sleep_seconds = min(
            remaining,
            30,
        )

        time.sleep(
            sleep_seconds
        )


# ============================================================
# MAIN
# ============================================================

def run():

    log_file = (
        get_log_path()
    )

    print()
    print(
        "=" * 80
    )

    print(
        "ANALITIKO WORKDAY PIPELINE"
    )

    print(
        "=" * 80
    )

    print(
        f"Workday: "
        f"{START_HOUR:02d}:00"
        f" - "
        f"{END_HOUR:02d}:00"
    )

    print(
        "Interval: "
        f"{RUN_INTERVAL_HOURS} hour"
    )

    print(
        "Runner: "
        "scripts.run_full_pipeline"
    )

    print(
        f"Log: "
        f"{log_file}"
    )

    print(
        "=" * 80
    )

    write_log(
        log_file,
        (
            "\n"
            + "=" * 80
            + "\n"
            + "ANALITIKO WORKDAY PIPELINE\n"
            + "=" * 80
            + "\n"
            + (
                f"Started runner: "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            + (
                f"Workday: "
                f"{START_HOUR:02d}:00"
                f" - "
                f"{END_HOUR:02d}:00\n"
            )
            + (
                f"Interval: "
                f"{RUN_INTERVAL_HOURS} hour\n"
            )
            + "=" * 80
            + "\n"
        ),
    )

    # ========================================================
    # CURRENT TIME
    # ========================================================

    now = (
        datetime.now()
    )

    workday_start = (
        get_workday_start(
            now
        )
    )

    workday_end = (
        get_workday_end(
            now
        )
    )

    # ========================================================
    # BEFORE 08:00
    # ========================================================

    if now < workday_start:

        print()
        print(
            "Workday has not started yet."
        )

        print(
            "First run scheduled for: "
            f"{workday_start.strftime('%H:%M:%S')}"
        )

        wait_until(
            workday_start
        )

        run_full_pipeline(
            log_file
        )

    # ========================================================
    # BETWEEN 08:00 AND 16:00
    #
    # When started manually during workday, run immediately.
    # This is useful if PowerShell is started at e.g. 14:32.
    # ========================================================

    elif now <= workday_end:

        print()
        print(
            "Inside workday window."
        )

        print(
            "Running pipeline immediately..."
        )

        run_full_pipeline(
            log_file
        )

    # ========================================================
    # AFTER 16:00
    # ========================================================

    else:

        print()
        print(
            "Workday execution window "
            "has already finished."
        )

        print(
            "No runs scheduled for today."
        )

        print(
            "=" * 80
        )

        return

    # ========================================================
    # HOURLY LOOP
    # ========================================================

    while True:

        now = (
            datetime.now()
        )

        next_run = (
            get_next_run_time(
                now
            )
        )

        if next_run is None:

            break

        print()
        print(
            "=" * 80
        )

        print(
            "WAITING FOR NEXT RUN"
        )

        print(
            "=" * 80
        )

        print(
            "Current time: "
            f"{now.strftime('%H:%M:%S')}"
        )

        print(
            "Next run: "
            f"{next_run.strftime('%H:%M:%S')}"
        )

        print(
            "Press Ctrl+C to stop."
        )

        print(
            "=" * 80
        )

        write_log(
            log_file,
            (
                "\n"
                + (
                    "Next run: "
                    f"{next_run.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
            ),
        )

        wait_until(
            next_run
        )

        run_full_pipeline(
            log_file
        )

    # ========================================================
    # END OF WORKDAY
    # ========================================================

    finished_at = (
        datetime.now()
    )

    print()
    print(
        "=" * 80
    )

    print(
        "WORKDAY PIPELINE COMPLETE"
    )

    print(
        "=" * 80
    )

    print(
        "Finished: "
        f"{finished_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        "No more automatic runs "
        "scheduled today."
    )

    print(
        "=" * 80
    )

    write_log(
        log_file,
        (
            "\n"
            + "=" * 80
            + "\n"
            + "WORKDAY PIPELINE COMPLETE\n"
            + (
                "Finished: "
                f"{finished_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            + "=" * 80
            + "\n"
        ),
    )


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    try:

        run()

    except KeyboardInterrupt:

        print()
        print()
        print(
            "=" * 80
        )

        print(
            "WORKDAY PIPELINE STOPPED BY USER"
        )

        print(
            "=" * 80
        )

        print(
            "The runner was stopped safely."
        )

        print(
            "Existing snapshots and database "
            "data remain unchanged."
        )

        print(
            "=" * 80
        )