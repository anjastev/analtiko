from collections import defaultdict
from datetime import date, timedelta

from app.collectors.api_football import (
    APIFootballClient,
)

from app.football_leagues import (
    get_enabled_league_ids,
    get_enabled_leagues,
)

from app.database.database import (
    Base,
    SessionLocal,
    engine,
)

from app.services.fixture_sync import (
    sync_fixtures,
)

import app.models


# ============================================================
# CONFIG
# ============================================================

# Free API-Football plan currently gives us a limited
# fixture date window.
#
# We therefore sync:
#
# day 0 = today
# day 1 = tomorrow
#
# This is enough for the live prediction pipeline and avoids
# wasting API requests on inaccessible future dates.
#
DAYS_TO_SYNC = 2


# ============================================================
# HELPERS
# ============================================================

def get_api_errors(
    data: dict,
):
    """
    Return API-Football errors in normalized form.
    """

    errors = (
        data.get("errors")
        or {}
    )

    return errors


def is_rate_limited(
    data: dict,
) -> bool:
    """
    Detect API rate-limit errors.
    """

    errors = get_api_errors(
        data
    )

    if not errors:
        return False

    text = str(
        errors
    ).lower()

    return (
        (
            "rate" in text
            and "limit" in text
        )
        or (
            "too many requests"
            in text
        )
    )


def build_league_lookup():
    """
    Build API league ID -> local configuration lookup.
    """

    enabled = (
        get_enabled_leagues()
    )

    return {
        int(config["api_id"]): {
            "key": key,
            **config,
        }
        for key, config
        in enabled.items()
    }


# ============================================================
# MAIN
# ============================================================

def run():

    Base.metadata.create_all(
        bind=engine
    )

    client = (
        APIFootballClient()
    )

    db = (
        SessionLocal()
    )

    start_date = (
        date.today()
    )

    league_ids = (
        get_enabled_league_ids()
    )

    league_lookup = (
        build_league_lookup()
    )

    print()
    print("=" * 80)
    print(
        "ANALITIKO LIVE FOOTBALL FIXTURE SYNC"
    )
    print("=" * 80)

    print(
        f"Start date: "
        f"{start_date.isoformat()}"
    )

    print(
        f"Days: "
        f"{DAYS_TO_SYNC}"
    )

    print(
        f"Enabled leagues: "
        f"{len(league_ids)}"
    )

    print()

    for config in sorted(
        league_lookup.values(),
        key=lambda item: (
            item["priority"],
            item["name"],
            item["country"],
        ),
    ):

        print(
            f"[P{config['priority']}] "
            f"{config['name']} "
            f"({config['country']}) "
            f"- API ID "
            f"{config['api_id']}"
        )

    print("=" * 80)

    total_received = 0
    total_selected = 0
    total_synced = 0

    total_days_completed = 0
    total_days_failed = 0

    rate_limited = False
    api_warning = False

    league_totals = defaultdict(
        lambda: {
            "received": 0,
        }
    )

    try:

        # ====================================================
        # FETCH EACH DATE
        #
        # One API call per date.
        # ====================================================

        for day_offset in range(
            DAYS_TO_SYNC
        ):

            target_date = (
                start_date
                + timedelta(
                    days=day_offset
                )
            )

            date_string = (
                target_date.isoformat()
            )

            print()
            print("=" * 80)
            print(
                f"DATE: {date_string}"
            )
            print("=" * 80)

            data = (
                client
                .get_fixtures_by_date(
                    date_string
                )
            )

            # =================================================
            # API ERRORS
            # =================================================

            errors = get_api_errors(
                data
            )

            if errors:

                total_days_failed += 1
                api_warning = True

                print(
                    f"API error for "
                    f"{date_string}: "
                    f"{errors}"
                )

                if is_rate_limited(
                    data
                ):

                    print()
                    print(
                        "Rate limit detected."
                    )

                    print(
                        "Stopping fixture sync "
                        "to protect remaining requests."
                    )

                    rate_limited = True

                    break

                print(
                    "Skipping this date."
                )

                continue

            fixtures = (
                data.get(
                    "response",
                    []
                )
                or []
            )

            total_received += (
                len(fixtures)
            )

            total_days_completed += 1

            print(
                f"API fixtures received: "
                f"{len(fixtures)}"
            )

            # =================================================
            # LOCAL LEAGUE FILTER
            # =================================================

            selected_fixtures = []

            for fixture in fixtures:

                league_data = (
                    fixture.get(
                        "league",
                        {}
                    )
                    or {}
                )

                api_league_id = (
                    league_data.get(
                        "id"
                    )
                )

                if api_league_id is None:
                    continue

                try:

                    api_league_id = int(
                        api_league_id
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

                if (
                    api_league_id
                    not in league_ids
                ):

                    continue

                selected_fixtures.append(
                    fixture
                )

                league_totals[
                    api_league_id
                ][
                    "received"
                ] += 1

            total_selected += (
                len(
                    selected_fixtures
                )
            )

            print(
                f"Tracked fixtures selected: "
                f"{len(selected_fixtures)}"
            )

            # =================================================
            # DISPLAY
            # =================================================

            if selected_fixtures:

                fixtures_by_league = (
                    defaultdict(list)
                )

                for fixture in selected_fixtures:

                    api_league_id = int(
                        fixture[
                            "league"
                        ][
                            "id"
                        ]
                    )

                    fixtures_by_league[
                        api_league_id
                    ].append(
                        fixture
                    )

                for (
                    api_league_id,
                    league_fixtures,
                ) in sorted(
                    fixtures_by_league.items(),
                    key=lambda item: (
                        league_lookup.get(
                            item[0],
                            {},
                        ).get(
                            "priority",
                            999,
                        ),
                        league_lookup.get(
                            item[0],
                            {},
                        ).get(
                            "name",
                            "",
                        ),
                    ),
                ):

                    config = (
                        league_lookup.get(
                            api_league_id
                        )
                    )

                    if config:

                        league_label = (
                            f"{config['name']} "
                            f"({config['country']})"
                        )

                    else:

                        league_label = (
                            league_fixtures[
                                0
                            ][
                                "league"
                            ][
                                "name"
                            ]
                        )

                    print()
                    print(
                        f"{league_label}: "
                        f"{len(league_fixtures)}"
                    )

                    for fixture in (
                        league_fixtures
                    ):

                        teams = (
                            fixture.get(
                                "teams",
                                {}
                            )
                            or {}
                        )

                        home = (
                            teams.get(
                                "home",
                                {}
                            )
                            .get(
                                "name",
                                "Unknown"
                            )
                        )

                        away = (
                            teams.get(
                                "away",
                                {}
                            )
                            .get(
                                "name",
                                "Unknown"
                            )
                        )

                        fixture_info = (
                            fixture.get(
                                "fixture",
                                {}
                            )
                            or {}
                        )

                        fixture_id = (
                            fixture_info.get(
                                "id"
                            )
                        )

                        fixture_date = (
                            fixture_info.get(
                                "date"
                            )
                        )

                        print(
                            f"  [{fixture_id}] "
                            f"{home} vs {away}"
                        )

                        if fixture_date:

                            print(
                                f"      "
                                f"{fixture_date}"
                            )

            # =================================================
            # DATABASE SYNC
            # =================================================

            if selected_fixtures:

                synced = (
                    sync_fixtures(
                        db=db,
                        fixtures=selected_fixtures,
                    )
                )

                total_synced += (
                    synced
                )

                print()
                print(
                    f"Database synced: "
                    f"{synced}"
                )

            else:

                print(
                    "No tracked fixtures "
                    "for this date."
                )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # SUMMARY
        # ====================================================

        print()
        print("=" * 80)
        print(
            "LIVE FIXTURE SYNC SUMMARY"
        )
        print("=" * 80)

        print(
            f"Days requested: "
            f"{DAYS_TO_SYNC}"
        )

        print(
            f"Days completed: "
            f"{total_days_completed}"
        )

        print(
            f"Days failed/skipped: "
            f"{total_days_failed}"
        )

        print(
            f"API fixtures received: "
            f"{total_received}"
        )

        print(
            f"Tracked fixtures selected: "
            f"{total_selected}"
        )

        print(
            f"Database synced: "
            f"{total_synced}"
        )

        print()

        print(
            "Tracked fixtures by league:"
        )

        if league_totals:

            for (
                api_league_id,
                totals,
            ) in sorted(
                league_totals.items(),
                key=lambda item: (
                    league_lookup.get(
                        item[0],
                        {},
                    ).get(
                        "priority",
                        999,
                    ),
                    league_lookup.get(
                        item[0],
                        {},
                    ).get(
                        "name",
                        "",
                    ),
                ),
            ):

                config = (
                    league_lookup.get(
                        api_league_id,
                        {}
                    )
                )

                name = (
                    config.get(
                        "name",
                        str(
                            api_league_id
                        ),
                    )
                )

                country = (
                    config.get(
                        "country",
                        "Unknown",
                    )
                )

                print(
                    f"  {name} "
                    f"({country}): "
                    f"{totals['received']}"
                )

        else:

            print(
                "  None"
            )

        print()

        # ====================================================
        # FINAL STATUS
        # ====================================================

        if rate_limited:

            print(
                "STATUS: PARTIAL "
                "(API rate limited)"
            )

        elif api_warning:

            print(
                "STATUS: PARTIAL "
                "(one or more API requests failed)"
            )

        else:

            print(
                "STATUS: OK"
            )

        print("=" * 80)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    run()