from __future__ import annotations

import re

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy.orm import Session

from app.models.market import Market
from app.models.match import Match
from app.models.signal import Signal

from app.services.match_data_quality import (
    is_match_production_ready,
)
from app.services.ticket_optimizer import (
    optimize_ticket,
)


STRATEGIES = {
    "SAFE",
    "BALANCED",
    "AGGRESSIVE",
}


STRATEGY_DEFAULTS = {

    "SAFE": {
        "selections": 2,
        "min_probability": 78.0,
        "min_edge": 5.0,
        "max_selections": 4,
    },

    "BALANCED": {
        "selections": 3,
        "min_probability": 72.0,
        "min_edge": 5.0,
        "max_selections": 5,
    },

    "AGGRESSIVE": {
        "selections": 4,
        "min_probability": 65.0,
        "min_edge": 5.0,
        "max_selections": 6,
    },
}


LEAGUE_ALIASES = {

    "premier league":
        "Premier League",

    "epl":
        "Premier League",

    "la liga":
        "La Liga",

    "serie a":
        "Serie A",

    "bundesliga":
        "Bundesliga",

    "ligue 1":
        "Ligue 1",

    "champions league":
        "UEFA Champions League",

    "ucl":
        "UEFA Champions League",

    "europa league":
        "UEFA Europa League",

    "conference league":
        "UEFA Europa Conference League",

    "eredivisie":
        "Eredivisie",

    "primeira liga":
        "Primeira Liga",

    "super lig":
        "Süper Lig",

    "süper lig":
        "Süper Lig",

    "scottish premiership":
        "Premiership",
}


def ensure_utc(
    value,
):

    if value is None:
        return None

    if value.tzinfo is None:

        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def parse_strategy(
    message: str,
    explicit: str | None,
):

    if explicit:

        normalized = (
            explicit
            .strip()
            .upper()
        )

        if normalized in STRATEGIES:
            return normalized

    text = message.lower()

    if any(
        word in text
        for word in [
            "safe",
            "siguren",
            "sigurna",
            "сигурен",
            "сигурна",
            "bezbeden",
            "безбеден",
        ]
    ):
        return "SAFE"

    if any(
        word in text
        for word in [
            "aggressive",
            "agresiven",
            "agresivna",
            "агресивен",
            "агресивна",
            "risk",
            "risky",
        ]
    ):
        return "AGGRESSIVE"

    return "BALANCED"


def parse_date(
    message: str,
    explicit: str | None,
):

    if explicit:

        normalized = (
            explicit
            .strip()
            .lower()
        )

        if normalized in {
            "today",
            "tomorrow",
        }:
            return normalized

    text = message.lower()

    tomorrow_terms = [
        "tomorrow",
        "utre",
        "утре",
    ]

    if any(
        term in text
        for term in tomorrow_terms
    ):
        return "tomorrow"

    return "today"


def parse_leagues(
    message: str,
    explicit: list[str] | None,
):

    if explicit:
        return list(
            dict.fromkeys(
                explicit
            )
        )

    text = message.lower()

    found = []

    for alias, league in (
        LEAGUE_ALIASES.items()
    ):

        if alias in text:

            if league not in found:
                found.append(
                    league
                )

    return found


def parse_selections(
    message: str,
    explicit: int | None,
    strategy: str,
):

    config = (
        STRATEGY_DEFAULTS[
            strategy
        ]
    )

    if explicit is not None:

        return min(
            explicit,
            config[
                "max_selections"
            ],
        )

    patterns = [
        r"(\d+)\s*(?:matches|match|games|picks|selections)",
        r"(\d+)\s*(?:meca|mecevi|utakmici|tipovi)",
        r"(\d+)\s*(?:меча|мечеви|утакмици|типови)",
    ]

    text = message.lower()

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            value = int(
                match.group(1)
            )

            return max(
                1,
                min(
                    value,
                    config[
                        "max_selections"
                    ],
                ),
            )

    return config[
        "selections"
    ]


def parse_probability(
    message: str,
    explicit: float | None,
    strategy: str,
):

    if explicit is not None:
        return float(
            explicit
        )

    text = message.lower()

    patterns = [
        r"(?:above|over|min|minimum|nad|над)\s*(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%\s*(?:probability|confidence|verojatnost)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            return float(
                match.group(1)
            )

    return float(
        STRATEGY_DEFAULTS[
            strategy
        ][
            "min_probability"
        ]
    )


def parse_target_odds(
    message: str,
    explicit: float | None,
):

    if explicit is not None:

        return float(
            explicit
        )

    text = message.lower()

    patterns = [
        r"(?:odds|quota|kvota|квота)\s*(?:around|okolu|околу|~|:)?\s*(\d+(?:\.\d+)?)",
        r"(?:around|okolu|околу)\s*(\d+(?:\.\d+)?)\s*(?:odds|quota|kvota|квота)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            value = float(
                match.group(1)
            )

            if value > 1.0:
                return value

    return None


def parse_request(
    *,
    message: str,
    strategy: str | None,
    date: str | None,
    leagues: list[str] | None,
    selections: int | None,
    min_probability: float | None,
    target_odds: float | None,
):

    parsed_strategy = (
        parse_strategy(
            message,
            strategy,
        )
    )

    return {
        "sport":
            "football",

        "strategy":
            parsed_strategy,

        "date":
            parse_date(
                message,
                date,
            ),

        "leagues":
            parse_leagues(
                message,
                leagues,
            ),

        "selections":
            parse_selections(
                message,
                selections,
                parsed_strategy,
            ),

        "min_probability":
            parse_probability(
                message,
                min_probability,
                parsed_strategy,
            ),

        "target_odds":
            parse_target_odds(
                message,
                target_odds,
            ),
    }


def get_date_window(
    date_name: str,
):

    now = datetime.now(
        timezone.utc
    )

    if date_name == "tomorrow":

        target = (
            now.date()
            + timedelta(
                days=1
            )
        )

    else:

        target = now.date()

    start = datetime(
        target.year,
        target.month,
        target.day,
        tzinfo=timezone.utc,
    )

    end = (
        start
        + timedelta(
            days=1
        )
    )

    # For today we must never include
    # already-started matches.

    if date_name == "today":

        start = max(
            start,
            now,
        )

    return (
        start,
        end,
    )


def get_league_name(
    match: Match,
):

    league = getattr(
        match,
        "league",
        None,
    )

    if league is None:
        return None

    return getattr(
        league,
        "name",
        None,
    )


def candidate_score(
    signal: Signal,
    strategy: str,
):

    probability = float(
        signal.model_probability
    )

    edge = float(
        signal.edge
        or 0.0
    )

    ev = float(
        signal.expected_value
        or 0.0
    )

    odds = float(
        signal.odds
        or 1.0
    )

    if strategy == "SAFE":

        return (
            probability
            * 1.50
            + edge
            * 0.45
            + min(
                ev,
                30.0,
            )
            * 0.10
            - max(
                odds - 2.0,
                0.0,
            )
            * 5.0
        )

    if strategy == "AGGRESSIVE":

        return (
            probability
            * 0.80
            + edge
            * 1.15
            + min(
                ev,
                60.0,
            )
            * 0.30
            + min(
                odds,
                5.0,
            )
            * 3.0
        )

    return (
        probability
        * 1.10
        + edge
        * 0.75
        + min(
            ev,
            40.0,
        )
        * 0.20
    )


def select_ticket(
    candidates: list[dict],
    *,
    strategy: str,
    count: int,
    target_odds: float | None,
):

    if not candidates:
        return []

    ranked = sorted(
        candidates,
        key=lambda item:
            item[
                "score"
            ],
        reverse=True,
    )

    # Never select more than one signal
    # from the same match.

    unique = []

    seen_matches = set()

    for item in ranked:

        match_id = (
            item[
                "signal"
            ].match_id
        )

        if match_id in seen_matches:
            continue

        seen_matches.add(
            match_id
        )

        unique.append(
            item
        )

    if not target_odds:

        return unique[
            :count
        ]

    # Simple bounded search for a set whose
    # total odds is reasonably close to the
    # requested target.

    pool = unique[
        :min(
            len(unique),
            18,
        )
    ]

    best = None
    best_distance = None

    from itertools import (
        combinations,
    )

    for combo in combinations(
        pool,
        min(
            count,
            len(pool),
        ),
    ):

        total_odds = 1.0

        for item in combo:

            total_odds *= float(
                item[
                    "signal"
                ].odds
            )

        distance = abs(
            total_odds
            - target_odds
        )

        if (
            best is None
            or distance
            < best_distance
        ):

            best = list(
                combo
            )

            best_distance = (
                distance
            )

    if best is not None:
        return best

    return unique[
        :count
    ]


def build_ticket(
    db: Session,
    *,
    message: str,
    strategy: str | None = None,
    date: str | None = None,
    leagues: list[str] | None = None,
    selections: int | None = None,
    min_probability: float | None = None,
    target_odds: float | None = None,
):

    parsed = (
        parse_request(
            message=message,
            strategy=strategy,
            date=date,
            leagues=leagues,
            selections=selections,
            min_probability=(
                min_probability
            ),
            target_odds=(
                target_odds
            ),
        )
    )

    date_from, date_to = (
        get_date_window(
            parsed[
                "date"
            ]
        )
    )

    optimized = (
        optimize_ticket(
            db,
            strategy=(
                parsed[
                    "strategy"
                ]
            ),
            date_from=date_from,
            date_to=date_to,
            selections=(
                parsed[
                    "selections"
                ]
            ),
            target_odds=(
                parsed[
                    "target_odds"
                ]
            ),
            leagues=(
                parsed[
                    "leagues"
                ]
            ),
            min_probability=(
                parsed[
                    "min_probability"
                ]
            ),
        )
    )

    if not optimized[
        "success"
    ]:

        return {
            "success":
                False,

            "message":
                optimized[
                    "message"
                ],

            "parsed_request":
                parsed,

            "selections":
                [],

            "total_odds":
                None,

            "estimated_probability":
                None,

            "strategy":
                parsed[
                    "strategy"
                ],

            "risk_level":
                "N/A",

            "candidates_found":
                optimized[
                    "candidates_found"
                ],
        }

    response_selections = []

    for item in optimized[
        "selections"
    ]:

        response_selections.append(
            {
                "signal_id":
                    item[
                        "signal_id"
                    ],

                "match_id":
                    item[
                        "match_id"
                    ],

                "match":
                    item[
                        "match"
                    ],

                "league":
                    item[
                        "league"
                    ],

                "kickoff":
                    item[
                        "kickoff"
                    ],

                "market":
                    item[
                        "market"
                    ],

                "selection":
                    item[
                        "selection"
                    ],

                "probability":
                    item[
                        "calibrated_probability"
                    ],

                "market_probability":
                    None,

                "edge":
                    item[
                        "edge"
                    ],

                "expected_value":
                    item[
                        "expected_value"
                    ],

                "odds":
                    item[
                        "odds"
                    ],

                "bookmaker":
                    item[
                        "bookmaker"
                    ],
            }
        )

    strategy_name = (
        optimized[
            "strategy"
        ]
    )

    if strategy_name == "SAFE":

        risk_level = "LOW"

    elif strategy_name == "AGGRESSIVE":

        risk_level = "HIGH"

    else:

        risk_level = "MEDIUM"

    metrics = (
        optimized[
            "metrics"
        ]
    )

    return {
        "success":
            True,

        "message":
            (
                f"I optimized a "
                f"{strategy_name} ticket "
                f"from "
                f"{optimized['candidates_found']} "
                f"production-qualified candidates. "
                f"Average quality is "
                f"{metrics['average_quality']:.1f}/100 "
                f"with "
                f"{metrics['average_uncertainty']:.1f}% "
                f"average uncertainty."
            ),

        "parsed_request":
            parsed,

        "selections":
            response_selections,

        "total_odds":
            metrics[
                "total_odds"
            ],

        "estimated_probability":
            metrics[
                "estimated_probability"
            ],

        "strategy":
            strategy_name,

        "risk_level":
            risk_level,

        "candidates_found":
            optimized[
                "candidates_found"
            ],
    }

    total_odds = 1.0

    combined_probability = 1.0

    response_selections = []

    for item in selected:

        signal = item[
            "signal"
        ]

        match = item[
            "match"
        ]

        odds = float(
            signal.odds
        )

        probability = float(
            signal.model_probability
        )

        total_odds *= odds

        combined_probability *= (
            probability
            / 100.0
        )

        response_selections.append(
            {
                "signal_id":
                    signal.id,

                "match_id":
                    match.id,

                "match":
                    (
                        f"{match.home_team.name} "
                        f"vs "
                        f"{match.away_team.name}"
                    ),

                "league":
                    item[
                        "league"
                    ],

                "kickoff":
                    (
                        match.match_date
                        .isoformat()
                        if match.match_date
                        else None
                    ),

                "market":
                    item[
                        "market_code"
                    ],

                "selection":
                    signal.selection,

                "probability":
                    round(
                        probability,
                        2,
                    ),

                "market_probability":
                    (
                        round(
                            float(
                                signal.market_probability
                            ),
                            2,
                        )
                        if signal.market_probability
                        is not None
                        else None
                    ),

                "edge":
                    (
                        round(
                            float(
                                signal.edge
                            ),
                            2,
                        )
                        if signal.edge
                        is not None
                        else None
                    ),

                "expected_value":
                    (
                        round(
                            float(
                                signal.expected_value
                            ),
                            2,
                        )
                        if signal.expected_value
                        is not None
                        else None
                    ),

                "odds":
                    round(
                        odds,
                        2,
                    ),

                "bookmaker":
                    signal.bookmaker,
            }
        )

    combined_probability *= 100.0

    strategy_name = (
        parsed[
            "strategy"
        ]
    )

    if strategy_name == "SAFE":
        risk_level = "LOW"

    elif strategy_name == "AGGRESSIVE":
        risk_level = "HIGH"

    else:
        risk_level = "MEDIUM"

    requested_count = (
        parsed[
            "selections"
        ]
    )

    actual_count = len(
        response_selections
    )

    if (
        actual_count
        < requested_count
    ):

        message_text = (
            f"I found only {actual_count} "
            f"production-qualified selections "
            f"for those conditions, so I did "
            f"not add weaker picks."
        )

    else:

        message_text = (
            f"I built a {strategy_name} "
            f"ticket with {actual_count} "
            f"production-qualified selections."
        )

    return {
        "success":
            True,

        "message":
            message_text,

        "parsed_request":
            parsed,

        "selections":
            response_selections,

        "total_odds":
            round(
                total_odds,
                2,
            ),

        "estimated_probability":
            round(
                combined_probability,
                2,
            ),

        "strategy":
            strategy_name,

        "risk_level":
            risk_level,

        "candidates_found":
            len(
                candidates
            ),
    }