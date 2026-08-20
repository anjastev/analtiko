import os

from dotenv import load_dotenv


load_dotenv()


API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"

SELECTED_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Conference League",
}