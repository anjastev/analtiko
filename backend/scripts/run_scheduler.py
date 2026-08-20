import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scripts.sync_selected_fixtures import run as sync_fixtures
from scripts.sync_odds import run as sync_odds
from scripts.sync_results import run as sync_results
from scripts.evaluate_predictions import run as evaluate_predictions
from scripts.snapshot_predictions import run as snapshot_predictions
from scripts.create_official_predictions import (
    run as create_official_predictions,
)

TIMEZONE = "Europe/Skopje"


def run_job(name, function):
    print()
    print("=" * 70)
    print(
        f"[{datetime.now()}] "
        f"Starting {name}..."
    )
    print("=" * 70)

    try:
        function()

        print(
            f"[{datetime.now()}] "
            f"{name} completed."
        )

    except Exception as error:
        print(
            f"[{datetime.now()}] "
            f"{name} failed: {error}"
        )


def run_official_prediction_job():
    run_job(
        "official prediction",
        create_official_predictions,
    )


def run_fixture_job():
    run_job(
        "fixture sync",
        sync_fixtures,
    )


def run_odds_job():
    run_job(
        "odds sync",
        sync_odds,
    )


def run_snapshot_job():
    run_job(
        "prediction snapshot",
        snapshot_predictions,
    )


def run_results_job():
    run_job(
        "results sync",
        sync_results,
    )


def run_evaluation_job():
    run_job(
        "prediction evaluation",
        evaluate_predictions,
    )


def main():
    scheduler = BackgroundScheduler(
        timezone=TIMEZONE
    )

    # =========================================================
    # FIXTURES
    # =========================================================
    # Morning + afternoon refresh
    scheduler.add_job(
        run_fixture_job,
        CronTrigger(
            hour="8,14",
            minute=0,
            timezone=TIMEZONE,
        ),
        id="fixture_sync",
        replace_existing=True,
    )

    scheduler.add_job(
        run_official_prediction_job,
        "interval",
        minutes=30,
        id="official_prediction",
        replace_existing=True,
    )

    # =========================================================
    # ODDS
    # =========================================================
    scheduler.add_job(
        run_odds_job,
        CronTrigger(
            hour="9,12,15,18,21",
            minute=0,
            timezone=TIMEZONE,
        ),
        id="odds_sync",
        replace_existing=True,
    )

    # =========================================================
    # PREDICTION SNAPSHOTS
    # =========================================================
    # Snapshot predictions after odds refresh.
    scheduler.add_job(
        run_snapshot_job,
        CronTrigger(
            hour="9,12,15,18,21",
            minute=10,
            timezone=TIMEZONE,
        ),
        id="prediction_snapshot",
        replace_existing=True,
    )

    # =========================================================
    # RESULTS
    # =========================================================
    # Check recently played matches.
    scheduler.add_job(
        run_results_job,
        CronTrigger(
            hour="12,18,23",
            minute=30,
            timezone=TIMEZONE,
        ),
        id="results_sync",
        replace_existing=True,
    )

    # =========================================================
    # EVALUATION
    # =========================================================
    # Run shortly after result sync.
    scheduler.add_job(
        run_evaluation_job,
        CronTrigger(
            hour="12,18,23",
            minute=40,
            timezone=TIMEZONE,
        ),
        id="prediction_evaluation",
        replace_existing=True,
    )

    scheduler.start()

    print()
    print("=" * 70)
    print("ANALITIKO SCHEDULER STARTED")
    print("=" * 70)

    print()
    print("Fixtures:")
    print("  08:00")
    print("  14:00")

    print()
    print("Odds:")
    print("  09:00")
    print("  12:00")
    print("  15:00")
    print("  18:00")
    print("  21:00")

    print()
    print("Prediction snapshots:")
    print("  09:10")
    print("  12:10")
    print("  15:10")
    print("  18:10")
    print("  21:10")

    print()
    print("Results:")
    print("  12:30")
    print("  18:30")
    print("  23:30")

    print()
    print("Prediction evaluation:")
    print("  12:40")
    print("  18:40")
    print("  23:40")

    print()
    print(
        f"Timezone: {TIMEZONE}"
    )

    print()
    print("Press CTRL+C to stop.")
    print()

    try:
        while True:
            time.sleep(60)

    except (
        KeyboardInterrupt,
        SystemExit,
    ):
        print()
        print(
            "Stopping Analitiko Scheduler..."
        )

        scheduler.shutdown()


if __name__ == "__main__":
    main()