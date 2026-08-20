from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.collectors.api_football import (
    APIFootballClient,
)

from app.database.database import (
    SessionLocal,
)

from app.models.history_sync_state import (
    HistorySyncState,
)

from app.models.match import Match

from app.models.team_match_history import (
    TeamMatchHistory,
)

from app.services.history_freshness import (
    should_sync_team,
)

from app.services.history_sync import (
    sync_fixture_to_team_history,
)


# ============================================================
# CONFIG
# ============================================================

UPCOMING_DAYS = 3

HISTORY_SEASONS = [
    2026,
    2025,
]

TARGET_HISTORY = 20

MAX_API_CALLS = 120

FRESH_DAYS = 45


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


# ============================================================
# DATETIME HELPERS
# ============================================================

def ensure_utc(
    value: datetime | None,
) -> datetime | None:

    """
    Normalize a datetime to timezone-aware UTC.

    SQLite commonly returns naive datetime values even when
    timezone information existed before persistence.

    API-Football returns timezone-aware ISO timestamps.

    We normalize both sides before Python datetime comparisons.
    """

    if value is None:
        return None

    if value.tzinfo is None:

        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def parse_api_date(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    try:

        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        return ensure_utc(
            parsed
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# UPCOMING MATCHES
# ============================================================

def get_upcoming_matches(
    db,
    now,
    end,
):

    return (
        db.query(Match)
        .filter(
            Match.match_date
            >= now,

            Match.match_date
            <= end,

            ~Match.status.in_(
                FINISHED_STATUSES
            ),
        )
        .order_by(
            Match.match_date.asc()
        )
        .all()
    )


def get_upcoming_team_contexts(
    matches,
):

    contexts = {}

    for match in matches:

        # ----------------------------------------------------
        # HOME TEAM
        # ----------------------------------------------------

        current_home = (
            contexts.get(
                match.home_team_id
            )
        )

        if (
            current_home is None
            or
            ensure_utc(
                match.match_date
            )
            <
            ensure_utc(
                current_home[
                    "next_match_date"
                ]
            )
        ):

            contexts[
                match.home_team_id
            ] = {
                "team":
                    match.home_team,

                "next_match_date":
                    match.match_date,
            }

        # ----------------------------------------------------
        # AWAY TEAM
        # ----------------------------------------------------

        current_away = (
            contexts.get(
                match.away_team_id
            )
        )

        if (
            current_away is None
            or
            ensure_utc(
                match.match_date
            )
            <
            ensure_utc(
                current_away[
                    "next_match_date"
                ]
            )
        ):

            contexts[
                match.away_team_id
            ] = {
                "team":
                    match.away_team,

                "next_match_date":
                    match.match_date,
            }

    return contexts


# ============================================================
# LOCAL HISTORY
# ============================================================

def get_local_history_count(
    db,
    team_id: int,
    before_date,
):

    return (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == team_id,

            TeamMatchHistory.match_date
            < before_date,
        )
        .count()
    )


def get_latest_local_history(
    db,
    team_id: int,
):

    return (
        db.query(
            TeamMatchHistory
        )
        .filter(
            TeamMatchHistory.team_id
            == team_id
        )
        .order_by(
            TeamMatchHistory.match_date
            .desc()
        )
        .first()
    )


# ============================================================
# SYNC STATE
# ============================================================

def update_sync_state(
    db,
    team_id: int,
    *,
    status: str,
    message: str | None,
    success: bool,
):

    now = datetime.now(
        timezone.utc
    )

    state = (
        db.query(
            HistorySyncState
        )
        .filter(
            HistorySyncState.team_id
            == team_id
        )
        .first()
    )

    if state is None:

        state = (
            HistorySyncState(
                team_id=team_id
            )
        )

        db.add(
            state
        )

    state.last_attempt_at = now

    state.last_status = (
        status
    )

    state.last_message = (
        message
    )

    state.updated_at = (
        now
    )

    if success:

        state.last_success_at = (
            now
        )

        latest = (
            get_latest_local_history(
                db=db,
                team_id=team_id,
            )
        )

        state.latest_history_at = (
            latest.match_date
            if latest
            else None
        )


# ============================================================
# API FIXTURE FILTERING
# ============================================================

def extract_finished_fixtures(
    response_data: dict,
    before_date,
):

    rows = []

    normalized_before_date = (
        ensure_utc(
            before_date
        )
    )

    if normalized_before_date is None:
        return rows

    for item in (
        response_data.get(
            "response",
            []
        )
    ):

        fixture = (
            item.get(
                "fixture",
                {}
            )
        )

        status = (
            fixture
            .get(
                "status",
                {}
            )
            .get(
                "short"
            )
        )

        if (
            status
            not in FINISHED_STATUSES
        ):
            continue

        fixture_date = (
            parse_api_date(
                fixture.get(
                    "date"
                )
            )
        )

        if fixture_date is None:
            continue

        # ====================================================
        # STRICT ANTI-LEAKAGE
        #
        # Only use matches completed BEFORE upcoming kickoff.
        # Both datetime objects are normalized to UTC.
        # ====================================================

        if (
            fixture_date
            >= normalized_before_date
        ):
            continue

        rows.append(
            (
                fixture_date,
                item,
            )
        )

    rows.sort(
        key=lambda value:
            value[0],
        reverse=True,
    )

    return rows


# ============================================================
# MAIN
# ============================================================

def run():

    db = SessionLocal()

    client = (
        APIFootballClient()
    )

    now = datetime.now(
        timezone.utc
    )

    end = (
        now
        + timedelta(
            days=UPCOMING_DAYS
        )
    )

    api_calls = 0

    teams_checked = 0
    teams_skipped_cooldown = 0
    teams_ready_before = 0

    teams_synced = 0
    teams_failed = 0

    fixtures_seen = 0
    rows_created = 0

    try:

        # ====================================================
        # UPCOMING MATCHES
        # ====================================================

        matches = (
            get_upcoming_matches(
                db=db,
                now=now,
                end=end,
            )
        )

        team_contexts = (
            get_upcoming_team_contexts(
                matches
            )
        )

        print()
        print("=" * 100)
        print(
            "ANALITIKO PRO LIVE HISTORY SYNC"
        )
        print("=" * 100)

        print(
            f"Upcoming matches: "
            f"{len(matches)}"
        )

        print(
            f"Unique teams: "
            f"{len(team_contexts)}"
        )

        print(
            f"Seasons: "
            f"{HISTORY_SEASONS}"
        )

        print(
            f"Target history: "
            f"{TARGET_HISTORY}"
        )

        print(
            f"Freshness window: "
            f"{FRESH_DAYS} days"
        )

        print(
            f"Max API calls: "
            f"{MAX_API_CALLS}"
        )

        # ====================================================
        # TEAM LOOP
        # ====================================================

        for team_id, context in (
            team_contexts.items()
        ):

            if (
                api_calls
                >= MAX_API_CALLS
            ):

                print()
                print(
                    "API budget reached."
                )

                break

            team = (
                context[
                    "team"
                ]
            )

            before_date = (
                context[
                    "next_match_date"
                ]
            )

            normalized_before_date = (
                ensure_utc(
                    before_date
                )
            )

            teams_checked += 1

            # =================================================
            # LOCAL HISTORY STATE
            # =================================================

            local_count = (
                get_local_history_count(
                    db=db,
                    team_id=team_id,
                    before_date=before_date,
                )
            )

            latest = (
                get_latest_local_history(
                    db=db,
                    team_id=team_id,
                )
            )

            latest_at = (
                latest.match_date
                if latest
                else None
            )

            normalized_latest_at = (
                ensure_utc(
                    latest_at
                )
            )

            fresh_cutoff = (
                normalized_before_date
                - timedelta(
                    days=FRESH_DAYS
                )
            )

            fresh = (
                normalized_latest_at
                is not None
                and
                normalized_latest_at
                >= fresh_cutoff
            )

            print()
            print("-" * 100)

            print(
                f"{team.name} "
                f"(local_id={team.id}, "
                f"external_id={team.external_id})"
            )

            print(
                f"Next match: "
                f"{normalized_before_date}"
            )

            print(
                f"Local history: "
                f"{local_count}"
            )

            print(
                f"Latest local: "
                f"{latest_at}"
            )

            print(
                f"Fresh: "
                f"{fresh}"
            )

            # =================================================
            # ALREADY READY
            # =================================================

            if (
                local_count
                >= TARGET_HISTORY
                and
                fresh
            ):

                teams_ready_before += 1

                print(
                    "READY: fresh local history"
                )

                continue

            # =================================================
            # SYNC COOLDOWN
            # =================================================

            if not (
                should_sync_team(
                    db=db,
                    team_id=team_id,
                    now=now,
                )
            ):

                teams_skipped_cooldown += 1

                print(
                    "SKIPPED: sync cooldown"
                )

                continue

            # =================================================
            # EXTERNAL ID
            # =================================================

            if not team.external_id:

                teams_failed += 1

                update_sync_state(
                    db=db,
                    team_id=team.id,
                    status="FAILED",
                    message=(
                        "Missing external_id"
                    ),
                    success=False,
                )

                db.commit()

                print(
                    "FAILED: missing external_id"
                )

                continue

            # =================================================
            # FETCH API HISTORY
            # =================================================

            merged = {}

            team_had_api_error = (
                False
            )

            for season in (
                HISTORY_SEASONS
            ):

                if (
                    api_calls
                    >= MAX_API_CALLS
                ):
                    break

                print(
                    f"Fetching season "
                    f"{season}..."
                )

                try:

                    data = (
                        client
                        .get_team_fixtures_by_season(
                            team_id=(
                                team.external_id
                            ),
                            season=season,
                        )
                    )

                    api_calls += 1

                except Exception as error:

                    team_had_api_error = (
                        True
                    )

                    print(
                        f"API request failed: "
                        f"{error}"
                    )

                    continue

                if not isinstance(
                    data,
                    dict,
                ):

                    team_had_api_error = (
                        True
                    )

                    print(
                        "API response invalid."
                    )

                    continue

                errors = (
                    data.get(
                        "errors"
                    )
                )

                if errors:

                    team_had_api_error = (
                        True
                    )

                    print(
                        f"API errors: "
                        f"{errors}"
                    )

                    continue

                rows = (
                    extract_finished_fixtures(
                        response_data=data,
                        before_date=(
                            normalized_before_date
                        ),
                    )
                )

                print(
                    f"Usable finished fixtures: "
                    f"{len(rows)}"
                )

                for (
                    fixture_date,
                    fixture_data,
                ) in rows:

                    fixture_id = (
                        fixture_data
                        .get(
                            "fixture",
                            {}
                        )
                        .get(
                            "id"
                        )
                    )

                    if not fixture_id:
                        continue

                    # Fixture ID dedupe across seasons.
                    merged[
                        fixture_id
                    ] = (
                        fixture_date,
                        fixture_data,
                    )

                print(
                    f"Merged history candidates: "
                    f"{len(merged)}"
                )

                # Enough history collected.
                if (
                    len(merged)
                    >= TARGET_HISTORY
                ):

                    break

            # =================================================
            # SELECT LATEST N
            # =================================================

            sorted_rows = sorted(
                merged.values(),
                key=lambda value:
                    value[0],
                reverse=True,
            )

            selected_rows = (
                sorted_rows[
                    :TARGET_HISTORY
                ]
            )

            fixtures_seen += len(
                selected_rows
            )

            before_created = (
                get_local_history_count(
                    db=db,
                    team_id=team.id,
                    before_date=before_date,
                )
            )

            team_rows_created = 0

            # =================================================
            # STORE HISTORY
            # =================================================

            for (
                fixture_date,
                fixture_data,
            ) in selected_rows:

                try:

                    created = (
                        sync_fixture_to_team_history(
                            db=db,
                            fixture_data=(
                                fixture_data
                            ),
                        )
                    )

                    team_rows_created += (
                        created
                    )

                    rows_created += (
                        created
                    )

                except Exception as error:

                    db.rollback()

                    print(
                        f"Fixture store failed: "
                        f"{error}"
                    )

            db.commit()

            after_created = (
                get_local_history_count(
                    db=db,
                    team_id=team.id,
                    before_date=before_date,
                )
            )

            # =================================================
            # UPDATE STATE
            # =================================================

            if (
                selected_rows
                or
                after_created
                > before_created
            ):

                teams_synced += 1

                update_sync_state(
                    db=db,
                    team_id=team.id,
                    status="OK",
                    message=(
                        f"history="
                        f"{after_created}; "
                        f"created="
                        f"{team_rows_created}"
                    ),
                    success=True,
                )

                db.commit()

                print(
                    f"SYNCED: "
                    f"{before_created} "
                    f"-> "
                    f"{after_created}"
                )

                print(
                    f"Rows created this run: "
                    f"{team_rows_created}"
                )

            else:

                teams_failed += 1

                message = (
                    "No finished fixtures "
                    "before kickoff"
                )

                if team_had_api_error:

                    message = (
                        "API errors and "
                        "no usable fixtures"
                    )

                update_sync_state(
                    db=db,
                    team_id=team.id,
                    status="NO_DATA",
                    message=message,
                    success=False,
                )

                db.commit()

                print(
                    f"NO DATA: "
                    f"{message}"
                )

        # ====================================================
        # SUMMARY
        # ====================================================

        print()
        print("=" * 100)
        print(
            "LIVE HISTORY SYNC SUMMARY"
        )
        print("=" * 100)

        print(
            f"Teams checked:          "
            f"{teams_checked}"
        )

        print(
            f"Already ready:          "
            f"{teams_ready_before}"
        )

        print(
            f"Cooldown skipped:       "
            f"{teams_skipped_cooldown}"
        )

        print(
            f"Teams synced:           "
            f"{teams_synced}"
        )

        print(
            f"Teams failed/no data:   "
            f"{teams_failed}"
        )

        print(
            f"API calls:              "
            f"{api_calls}"
        )

        print(
            f"Fixtures selected:      "
            f"{fixtures_seen}"
        )

        print(
            f"History rows created:   "
            f"{rows_created}"
        )

        print()

        if (
            teams_failed == 0
        ):

            print(
                "STATUS: OK"
            )

        elif (
            teams_synced > 0
            or teams_ready_before > 0
        ):

            print(
                "STATUS: PARTIAL"
            )

        else:

            print(
                "STATUS: BLOCKED"
            )

        print("=" * 100)

    finally:

        db.close()


if __name__ == "__main__":
    run()