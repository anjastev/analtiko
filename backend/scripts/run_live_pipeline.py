import subprocess
import sys
from datetime import datetime


STEPS = [
    {
        "name": "Sync Results",
        "module": "scripts.sync_results",
        "required": False,
    },
    {
        "name": "Snapshot ML Predictions",
        "module": "scripts.snapshot_ml_predictions",
        "required": False,
    },
    {
        "name": "Evaluate ML Predictions",
        "module": "scripts.evaluate_ml_predictions",
        "required": False,
    },
    {
        "name": "Pipeline Health",
        "module": "scripts.check_pipeline_health",
        "required": False,
    },
]


def run_step(
    name: str,
    module: str,
):
    print()
    print("=" * 72)
    print(name.upper())
    print("=" * 72)

    command = [
        sys.executable,
        "-m",
        module,
    ]

    result = subprocess.run(
        command,
        check=False,
    )

    success = (
        result.returncode == 0
    )

    print()

    if success:
        print(
            f"{name}: OK"
        )
    else:
        print(
            f"{name}: FAILED "
            f"(exit code "
            f"{result.returncode})"
        )

    return success


def run():

    started_at = datetime.now()

    print()
    print("=" * 72)
    print("ANALITIKO LIVE PIPELINE")
    print("=" * 72)

    print(
        f"Started: "
        f"{started_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    results = []

    for step in STEPS:

        success = run_step(
            name=step["name"],
            module=step["module"],
        )

        results.append(
            {
                "name":
                    step["name"],

                "success":
                    success,

                "required":
                    step["required"],
            }
        )

        if (
            not success
            and
            step["required"]
        ):
            print()
            print(
                "Required step failed. "
                "Stopping pipeline."
            )

            break


    finished_at = datetime.now()

    duration = (
        finished_at
        - started_at
    ).total_seconds()


    print()
    print("=" * 72)
    print("PIPELINE SUMMARY")
    print("=" * 72)


    for item in results:

        status = (
            "OK"
            if item["success"]
            else "FAILED"
        )

        print(
            f"{item['name']:<30}"
            f"{status}"
        )


    successful = sum(
        1
        for item in results
        if item["success"]
    )


    failed = sum(
        1
        for item in results
        if not item["success"]
    )


    print()
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
        f"{duration:.1f}s"
    )

    print(
        f"Finished: "
        f"{finished_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print("=" * 72)


if __name__ == "__main__":
    run()