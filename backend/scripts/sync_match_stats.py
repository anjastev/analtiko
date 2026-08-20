from datetime import datetime, timezone

from app.collectors.api_football import (
    APIFootballClient,
)

from app.database.database import (
    SessionLocal,
)

from app.models.match import Match
from app.models.match_stats import MatchStats

from app.services.team_stats import (
    calculate_form_score,
    parse_team_statistics,
)

from app.services.fixture_stats import (
    get_finished_fixture_ids,
    get_team_statistics_from_fixture,
    aggregate_team_fixture_stats,
)


RECENT_MATCHES = 5

# Намерно само 2 додека сме на free API quota
MATCHES_TO_PROCESS = 2


def get_season(
    match_date: datetime,
) -> int:

    if match_date.month >= 7:
        return match_date.year

    return match_date.year - 1


def get_recent_advanced_stats(
    client: APIFootballClient,
    team_id: int,
    recent_fixtures: list[dict],
    fixture_cache: dict,
) -> dict:

    fixture_ids = get_finished_fixture_ids(
        recent_fixtures,
        limit=RECENT_MATCHES,
    )

    collected_stats = []

    for fixture_id in fixture_ids:

        print(
            f"    Fixture stats: {fixture_id}"
        )

        # Cache за да не повикаме ист fixture двапати
        if fixture_id not in fixture_cache:

            fixture_cache[fixture_id] = (
                client.get_fixture_statistics(
                    fixture_id
                )
            )

        data = fixture_cache[
            fixture_id
        ]

        team_stats = (
            get_team_statistics_from_fixture(
                data=data,
                team_id=team_id,
            )
        )

        if team_stats:
            collected_stats.append(
                team_stats
            )

    return aggregate_team_fixture_stats(
        collected_stats
    )


def run():

    db = SessionLocal()

    client = APIFootballClient()

    fixture_cache = {}

    try:

        now = datetime.now(
            timezone.utc
        )

        matches = (
            db.query(Match)
            .filter(
                Match.external_id.isnot(None),
                Match.match_date >= now,
            )
            .order_by(
                Match.match_date.asc()
            )
            .limit(
                MATCHES_TO_PROCESS
            )
            .all()
        )

        print()
        print("=" * 70)
        print(
            "ANALITIKO ADVANCED MATCH STATS SYNC"
        )
        print("=" * 70)

        print(
            f"Matches to process: {len(matches)}"
        )

        for match in matches:

            print()
            print("=" * 70)

            print(
                f"{match.home_team.name} "
                f"vs "
                f"{match.away_team.name}"
            )

            print("=" * 70)

            league_external_id = (
                match.league.external_id
            )

            home_external_id = (
                match.home_team.external_id
            )

            away_external_id = (
                match.away_team.external_id
            )

            if (
                not league_external_id
                or not home_external_id
                or not away_external_id
            ):
                print(
                    "Missing external IDs - skipped"
                )
                continue

            season = get_season(
                match.match_date
            )

            try:

                # ==========================
                # BASIC TEAM STATS
                # ==========================

                print()
                print(
                    "Fetching season statistics..."
                )

                home_stats_data = (
                    client.get_team_statistics(
                        league_id=league_external_id,
                        season=season,
                        team_id=home_external_id,
                    )
                )

                away_stats_data = (
                    client.get_team_statistics(
                        league_id=league_external_id,
                        season=season,
                        team_id=away_external_id,
                    )
                )


                home_season_stats = (
                    parse_team_statistics(
                        home_stats_data
                    )
                )

                away_season_stats = (
                    parse_team_statistics(
                        away_stats_data
                    )
                )


                # ==========================
                # RECENT FIXTURES
                # ==========================

                print(
                    "Fetching recent fixtures..."
                )

                home_recent_data = (
                    client.get_team_recent_fixtures(
                        team_id=home_external_id,
                        last=RECENT_MATCHES,
                    )
                )

                away_recent_data = (
                    client.get_team_recent_fixtures(
                        team_id=away_external_id,
                        last=RECENT_MATCHES,
                    )
                )


                home_recent = (
                    home_recent_data.get(
                        "response",
                        [],
                    )
                )

                away_recent = (
                    away_recent_data.get(
                        "response",
                        [],
                    )
                )


                # ==========================
                # FORM
                # ==========================

                home_form = (
                    calculate_form_score(
                        fixtures=home_recent,
                        team_id=home_external_id,
                    )
                )

                away_form = (
                    calculate_form_score(
                        fixtures=away_recent,
                        team_id=away_external_id,
                    )
                )


                # ==========================
                # ADVANCED STATS
                # ==========================

                print()
                print(
                    f"Advanced stats for "
                    f"{match.home_team.name}:"
                )

                home_advanced = (
                    get_recent_advanced_stats(
                        client=client,
                        team_id=home_external_id,
                        recent_fixtures=home_recent,
                        fixture_cache=fixture_cache,
                    )
                )


                print()
                print(
                    f"Advanced stats for "
                    f"{match.away_team.name}:"
                )

                away_advanced = (
                    get_recent_advanced_stats(
                        client=client,
                        team_id=away_external_id,
                        recent_fixtures=away_recent,
                        fixture_cache=fixture_cache,
                    )
                )


                # ==========================
                # DATABASE
                # ==========================

                existing = (
                    db.query(MatchStats)
                    .filter(
                        MatchStats.match_id
                        == match.id
                    )
                    .first()
                )


                if existing:
                    stats = existing

                else:
                    stats = MatchStats(
                        match_id=match.id
                    )

                    db.add(stats)


                stats.home_form = (
                    home_form
                )

                stats.away_form = (
                    away_form
                )


                if home_season_stats:
                    stats.home_goals_avg = (
                        home_season_stats[
                            "goals_for_avg"
                        ]
                    )

                if away_season_stats:
                    stats.away_goals_avg = (
                        away_season_stats[
                            "goals_for_avg"
                        ]
                    )


                stats.home_shots_avg = (
                    home_advanced[
                        "shots_avg"
                    ]
                )

                stats.away_shots_avg = (
                    away_advanced[
                        "shots_avg"
                    ]
                )


                stats.home_corners_avg = (
                    home_advanced[
                        "corners_avg"
                    ]
                )

                stats.away_corners_avg = (
                    away_advanced[
                        "corners_avg"
                    ]
                )


                stats.home_possession_avg = (
                    home_advanced[
                        "possession_avg"
                    ]
                )

                stats.away_possession_avg = (
                    away_advanced[
                        "possession_avg"
                    ]
                )


                stats.home_xg_avg = (
                    home_advanced[
                        "xg_avg"
                    ]
                )

                stats.away_xg_avg = (
                    away_advanced[
                        "xg_avg"
                    ]
                )


                db.commit()


                # ==========================
                # OUTPUT
                # ==========================

                print()
                print("RESULT")
                print("-" * 50)

                print(
                    f"Form: "
                    f"{home_form} "
                    f"vs "
                    f"{away_form}"
                )

                print(
                    f"Goals avg: "
                    f"{stats.home_goals_avg} "
                    f"vs "
                    f"{stats.away_goals_avg}"
                )

                print(
                    f"Shots avg: "
                    f"{stats.home_shots_avg} "
                    f"vs "
                    f"{stats.away_shots_avg}"
                )

                print(
                    f"Corners avg: "
                    f"{stats.home_corners_avg} "
                    f"vs "
                    f"{stats.away_corners_avg}"
                )

                print(
                    f"Possession avg: "
                    f"{stats.home_possession_avg}% "
                    f"vs "
                    f"{stats.away_possession_avg}%"
                )

                print(
                    f"xG avg: "
                    f"{stats.home_xg_avg} "
                    f"vs "
                    f"{stats.away_xg_avg}"
                )

                print(
                    "Stats successfully saved."
                )


            except Exception as error:

                db.rollback()

                print()
                print(
                    f"FAILED: {error}"
                )


        print()
        print("=" * 70)

        print(
            "ADVANCED STATS SYNC COMPLETE"
        )

        print("=" * 70)


    finally:

        db.close()


if __name__ == "__main__":
    run()