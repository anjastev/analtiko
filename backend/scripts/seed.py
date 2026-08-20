from datetime import datetime, timedelta

from app.database.database import Base, SessionLocal, engine
from app.models.league import League
from app.models.team import Team
from app.models.match import Match
from app.models.match_stats import MatchStats
from app.models.odds import Odds


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if db.query(Match).count() > 0:
            print("Database already contains matches. Skipping seed.")
            return

        premier_league = League(
            name="Premier League",
            country="England",
        )

        la_liga = League(
            name="La Liga",
            country="Spain",
        )

        serie_a = League(
            name="Serie A",
            country="Italy",
        )

        db.add_all([
            premier_league,
            la_liga,
            serie_a,
        ])

        db.flush()

        liverpool = Team(name="Liverpool", country="England")
        arsenal = Team(name="Arsenal", country="England")
        man_city = Team(name="Manchester City", country="England")
        chelsea = Team(name="Chelsea", country="England")

        real_madrid = Team(name="Real Madrid", country="Spain")
        valencia = Team(name="Valencia", country="Spain")
        barcelona = Team(name="Barcelona", country="Spain")
        sevilla = Team(name="Sevilla", country="Spain")

        inter = Team(name="Inter", country="Italy")
        lazio = Team(name="Lazio", country="Italy")

        db.add_all([
            liverpool,
            arsenal,
            man_city,
            chelsea,
            real_madrid,
            valencia,
            barcelona,
            sevilla,
            inter,
            lazio,
        ])

        db.flush()

        now = datetime.now()

        matches = [
            Match(
                league_id=premier_league.id,
                home_team_id=liverpool.id,
                away_team_id=arsenal.id,
                match_date=now + timedelta(hours=2),
            ),
            Match(
                league_id=premier_league.id,
                home_team_id=man_city.id,
                away_team_id=chelsea.id,
                match_date=now + timedelta(hours=4),
            ),
            Match(
                league_id=la_liga.id,
                home_team_id=real_madrid.id,
                away_team_id=valencia.id,
                match_date=now + timedelta(hours=5),
            ),
            Match(
                league_id=la_liga.id,
                home_team_id=barcelona.id,
                away_team_id=sevilla.id,
                match_date=now + timedelta(hours=6),
            ),
            Match(
                league_id=serie_a.id,
                home_team_id=inter.id,
                away_team_id=lazio.id,
                match_date=now + timedelta(hours=7),
            ),
        ]

        db.add_all(matches)

        db.flush()

        now = datetime.now()

        odds_data = [
            Odds(
                match_id=matches[0].id,
                home_win=1.92,
                draw=3.60,
                away_win=4.10,
                over_25=1.75,
                under_25=2.05,
                btts_yes=1.70,
                btts_no=2.10,
                recorded_at=now - timedelta(hours=6),
            ),
            Odds(
                match_id=matches[0].id,
                home_win=1.84,
                draw=3.70,
                away_win=4.25,
                over_25=1.70,
                under_25=2.15,
                btts_yes=1.68,
                btts_no=2.15,
                recorded_at=now - timedelta(hours=3),
            ),
            Odds(
                match_id=matches[0].id,
                home_win=1.76,
                draw=3.80,
                away_win=4.50,
                over_25=1.66,
                under_25=2.20,
                btts_yes=1.65,
                btts_no=2.20,
                recorded_at=now,
            ),

            Odds(
                match_id=matches[1].id,
                home_win=1.55,
                draw=4.20,
                away_win=5.60,
                over_25=1.62,
                under_25=2.25,
                btts_yes=1.78,
                btts_no=1.98,
                recorded_at=now - timedelta(hours=4),
            ),
            Odds(
                match_id=matches[1].id,
                home_win=1.50,
                draw=4.30,
                away_win=5.90,
                over_25=1.58,
                under_25=2.30,
                btts_yes=1.75,
                btts_no=2.02,
                recorded_at=now,
            ),
        ]

        db.add_all(odds_data)

        stats = [
            MatchStats(
                match_id=matches[0].id,
                home_form=8.6,
                away_form=7.4,
                home_goals_avg=2.3,
                away_goals_avg=1.8,
                home_shots_avg=15.4,
                away_shots_avg=13.2,
                home_corners_avg=6.2,
                away_corners_avg=5.7,
                home_possession_avg=61,
                away_possession_avg=57,
                home_xg_avg=2.1,
                away_xg_avg=1.7,
            ),
            MatchStats(
                match_id=matches[1].id,
                home_form=8.1,
                away_form=6.9,
                home_goals_avg=2.2,
                away_goals_avg=1.5,
                home_shots_avg=16.1,
                away_shots_avg=12.5,
                home_corners_avg=6.6,
                away_corners_avg=5.1,
                home_possession_avg=64,
                away_possession_avg=55,
                home_xg_avg=2.3,
                away_xg_avg=1.4,
            ),
        ]

        db.add_all(stats)

        db.commit()

        print("Demo data inserted successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()