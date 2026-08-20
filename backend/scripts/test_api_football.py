from datetime import date

from app.collectors.api_football import APIFootballClient


client = APIFootballClient()

today = date.today().isoformat()

data = client.get_fixtures_by_date(today)

print("Date:", today)
print("Results:", data.get("results"))
print("Requests:", data.get("paging"))

fixtures = data.get("response", [])

print()
print("Fixtures found:", len(fixtures))

for fixture in fixtures[:10]:

    league = fixture["league"]["name"]

    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]

    kickoff = fixture["fixture"]["date"]

    print(
        league,
        "|",
        home,
        "vs",
        away,
        "|",
        kickoff,
    )