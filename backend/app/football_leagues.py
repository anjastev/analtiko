# ============================================================
# ANALITIKO FOOTBALL LEAGUES
# ============================================================
#
# Central configuration for football competitions that
# Analitiko should automatically track.
#
# IMPORTANT:
# - "api_id" is the API-Football league ID.
# - "season" is kept for future league-specific endpoints.
# - "enabled" lets us turn a league on/off without deleting it.
# - "priority" can later be used for API budgeting.
#
# The live fixture sync itself fetches fixtures by DATE
# and filters locally by these API IDs. That means:
#
#     1 API request per day
#
# instead of:
#
#     1 API request per league per day
#
# This is intentional because API-Football rate limiting
# is currently one of our biggest operational constraints.
# ============================================================


FOOTBALL_LEAGUES = {

    # ========================================================
    # TOP 5 DOMESTIC LEAGUES
    # ========================================================

    "premier_league": {
        "name": "Premier League",
        "country": "England",
        "api_id": 39,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },

    "la_liga": {
        "name": "La Liga",
        "country": "Spain",
        "api_id": 140,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },

    "bundesliga": {
        "name": "Bundesliga",
        "country": "Germany",
        "api_id": 78,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },

    "serie_a": {
        "name": "Serie A",
        "country": "Italy",
        "api_id": 135,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },

    "ligue_1": {
        "name": "Ligue 1",
        "country": "France",
        "api_id": 61,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },


    # ========================================================
    # UEFA
    # ========================================================

    "champions_league": {
        "name": "UEFA Champions League",
        "country": "World",
        "api_id": 2,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },

    "europa_league": {
        "name": "UEFA Europa League",
        "country": "World",
        "api_id": 3,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },

    "conference_league": {
        "name": "UEFA Europa Conference League",
        "country": "World",
        "api_id": 848,
        "season": 2026,
        "enabled": True,
        "priority": 1,
    },


    # ========================================================
    # SECONDARY EUROPEAN LEAGUES
    # ========================================================

    "eredivisie": {
        "name": "Eredivisie",
        "country": "Netherlands",
        "api_id": 88,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },

    "primeira_liga": {
        "name": "Primeira Liga",
        "country": "Portugal",
        "api_id": 94,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },

    "super_lig": {
        "name": "Süper Lig",
        "country": "Turkey",
        "api_id": 203,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },

    "scottish_premiership": {
        "name": "Premiership",
        "country": "Scotland",
        "api_id": 179,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },

    "belgian_pro_league": {
        "name": "Jupiler Pro League",
        "country": "Belgium",
        "api_id": 144,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },

    "austrian_bundesliga": {
        "name": "Bundesliga",
        "country": "Austria",
        "api_id": 218,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },

    "greek_super_league": {
        "name": "Super League 1",
        "country": "Greece",
        "api_id": 197,
        "season": 2026,
        "enabled": True,
        "priority": 2,
    },


    # ========================================================
    # BALKANS / REGION
    # ========================================================

    "croatia_hnl": {
        "name": "HNL",
        "country": "Croatia",
        "api_id": 210,
        "season": 2026,
        "enabled": True,
        "priority": 3,
    },

    "serbia_super_liga": {
        "name": "Super Liga",
        "country": "Serbia",
        "api_id": 286,
        "season": 2026,
        "enabled": True,
        "priority": 3,
    },

    # Leave disabled initially until we verify API coverage
    # and exact current competition ID/name.
    "north_macedonia": {
        "name": "First League",
        "country": "North Macedonia",
        "api_id": None,
        "season": 2026,
        "enabled": False,
        "priority": 3,
    },
}


# ============================================================
# HELPERS
# ============================================================

def get_enabled_leagues():
    """
    Return enabled leagues with a valid API ID.
    """

    return {
        key: config
        for key, config
        in FOOTBALL_LEAGUES.items()
        if (
            config.get("enabled")
            and config.get("api_id") is not None
        )
    }


def get_enabled_league_ids():
    """
    Return a set of API-Football league IDs.
    """

    return {
        int(config["api_id"])
        for config
        in get_enabled_leagues().values()
    }


def get_league_by_api_id(
    api_id: int,
):
    """
    Return our configured league entry by API-Football ID.
    """

    for key, config in FOOTBALL_LEAGUES.items():

        if config.get("api_id") == api_id:

            return {
                "key": key,
                **config,
            }

    return None