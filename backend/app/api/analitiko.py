from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from datetime import timedelta

from app.services.ticket_optimizer import (
    optimize_ticket,
)

from sqlalchemy.orm import Session

from app.database.database import (
    SessionLocal,
)

from app.models.combination import (
    Combination,
)
from app.models.combination_selection import (
    CombinationSelection,
)
from app.models.market import Market
from app.models.market_prediction import (
    MarketPrediction,
)
from app.models.match import Match
from app.models.signal import Signal

from app.services.backend_health import (
    get_backend_health,
)

from app.services.match_data_quality import (
    evaluate_match_data_quality,
)


from app.schemas.ticket_builder import (
    TicketBuilderRequest,
    TicketBuilderResponse,
)

from app.services.ai_ticket_builder import (
    build_ticket,
)



router = APIRouter(
    prefix="/api",
    tags=[
        "Analitiko",
    ],
)


FINISHED_STATUSES = {
    "FT",
    "AET",
    "PEN",
}


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def serialize_match(
    db,
    match,
):

    quality = (
        evaluate_match_data_quality(
            db=db,
            match=match,
        )
    )

    return {
        "id":
            match.id,

        "external_id":
            getattr(
                match,
                "external_id",
                None,
            ),

        "match_date":
            (
                match.match_date.isoformat()
                if match.match_date
                else None
            ),

        "league":
            getattr(
                match,
                "league",
                None,
            ),

        "status":
            match.status,

        "home_team": {
            "id":
                match.home_team_id,

            "name":
                (
                    match.home_team.name
                    if match.home_team
                    else None
                ),
        },

        "away_team": {
            "id":
                match.away_team_id,

            "name":
                (
                    match.away_team.name
                    if match.away_team
                    else None
                ),
        },

        "home_score":
            getattr(
                match,
                "home_score",
                None,
            ),

        "away_score":
            getattr(
                match,
                "away_score",
                None,
            ),

        "data_quality":
            quality["status"],

        "production_ready":
            quality["ready"],
    }


def serialize_signal(
    signal,
    market_code=None,
):

    return {
        "id":
            signal.id,

        "match_id":
            signal.match_id,

        "market_id":
            signal.market_id,

        "market_code":
            market_code,

        "selection":
            signal.selection,

        "signal_type":
            signal.signal_type,

        "model_probability":
            signal.model_probability,

        "market_probability":
            signal.market_probability,

        "edge":
            signal.edge,

        "odds":
            signal.odds,

        "bookmaker":
            getattr(
                signal,
                "bookmaker",
                None,
            ),

        "expected_value":
            getattr(
                signal,
                "expected_value",
                None,
            ),

        "is_value":
            bool(
                getattr(
                    signal,
                    "is_value",
                    False,
                )
            ),

        "confidence_score":
            signal.confidence_score,

        "risk_level":
            signal.risk_level,

        "active":
            signal.active,

        "odds_recorded_at":
            (
                signal.odds_recorded_at.isoformat()
                if getattr(
                    signal,
                    "odds_recorded_at",
                    None,
                )
                else None
            ),

        "created_at":
            (
                signal.created_at.isoformat()
                if signal.created_at
                else None
            ),
    }


def serialize_combination(
    db,
    combination,
):

    selections = (
        db.query(
            CombinationSelection
        )
        .filter(
            CombinationSelection.combination_id
            == combination.id
        )
        .all()
    )

    serialized_selections = []

    for selection in selections:

        signal = (
            db.query(Signal)
            .filter(
                Signal.id
                == selection.signal_id
            )
            .first()
        )

        match = (
            db.query(Match)
            .filter(
                Match.id
                == selection.match_id
            )
            .first()
        )

        serialized_selections.append(
            {
                "id":
                    selection.id,

                "signal_id":
                    selection.signal_id,

                "match_id":
                    selection.match_id,

                "match":
                    (
                        f"{match.home_team.name} "
                        f"vs "
                        f"{match.away_team.name}"
                        if match
                        else None
                    ),

                "selection":
                    selection.selection,

                "odds":
                    selection.odds,

                "probability":
                    selection.probability,

                "correct":
                    getattr(
                        selection,
                        "correct",
                        None,
                    ),

                "signal_edge":
                    (
                        signal.edge
                        if signal
                        else None
                    ),

                "signal_ev":
                    (
                        getattr(
                            signal,
                            "expected_value",
                            None,
                        )
                        if signal
                        else None
                    ),
            }
        )

    return {
        "id":
            combination.id,

        "name":
            combination.name,

        "strategy":
            combination.strategy,

        "sport":
            combination.sport,

        "total_odds":
            combination.total_odds,

        "estimated_probability":
            combination.estimated_probability,

        "risk_score":
            combination.risk_score,

        "status":
            combination.status,

        "profit":
            getattr(
                combination,
                "profit",
                None,
            ),

        "roi":
            getattr(
                combination,
                "roi",
                None,
            ),

        "created_at":
            (
                combination.created_at.isoformat()
                if combination.created_at
                else None
            ),

        "evaluated_at":
            (
                combination.evaluated_at.isoformat()
                if getattr(
                    combination,
                    "evaluated_at",
                    None,
                )
                else None
            ),

        "selections":
            serialized_selections,
    }


# ============================================================
# HEALTH
# ============================================================

@router.get(
    "/health"
)
def health(
    db: Session = Depends(
        get_db
    ),
):

    return get_backend_health(
        db
    )


# ============================================================
# DASHBOARD
# ============================================================

@router.get(
    "/dashboard"
)
def dashboard(
    db: Session = Depends(
        get_db
    ),
):

    now = datetime.now(
        timezone.utc
    )

    health_data = (
        get_backend_health(
            db
        )
    )

    upcoming = (
        db.query(Match)
        .filter(
            Match.match_date >= now,
            ~Match.status.in_(
                FINISHED_STATUSES
            ),
        )
        .order_by(
            Match.match_date.asc()
        )
        .limit(10)
        .all()
    )

    value_signals = (
        db.query(Signal)
        .join(
            Match,
            Match.id
            == Signal.match_id,
        )
        .filter(
            Signal.active.is_(True),
            Signal.is_value.is_(True),
            Match.match_date >= now,
        )
        .order_by(
            Signal.expected_value.desc()
        )
        .limit(10)
        .all()
    )

    combinations = (
        db.query(Combination)
        .filter(
            Combination.status
            == "pending"
        )
        .order_by(
            Combination.created_at.desc()
        )
        .limit(3)
        .all()
    )

    markets = {
        market.id:
            market.code
        for market in (
            db.query(Market)
            .all()
        )
    }

    return {
        "health":
            health_data,

        "upcoming_matches": [
            serialize_match(
                db,
                match,
            )
            for match in upcoming
        ],

        "value_signals": [
            serialize_signal(
                signal,
                markets.get(
                    signal.market_id
                ),
            )
            for signal
            in value_signals
        ],

        "combinations": [
            serialize_combination(
                db,
                combination,
            )
            for combination
            in combinations
        ],
    }


# ============================================================
# MATCHES
# ============================================================

@router.get(
    "/matches"
)
def matches(
    ready_only: bool = False,
    limit: int = 100,
    db: Session = Depends(
        get_db
    ),
):

    limit = min(
        max(
            limit,
            1,
        ),
        500,
    )

    now = datetime.now(
        timezone.utc
    )

    rows = (
        db.query(Match)
        .filter(
            Match.match_date >= now
        )
        .order_by(
            Match.match_date.asc()
        )
        .limit(
            limit
        )
        .all()
    )

    result = []

    for match in rows:

        payload = (
            serialize_match(
                db,
                match,
            )
        )

        if (
            ready_only
            and
            not payload[
                "production_ready"
            ]
        ):
            continue

        result.append(
            payload
        )

    return {
        "count":
            len(result),

        "items":
            result,
    }


@router.get(
    "/matches/{match_id}"
)
def match_detail(
    match_id: int,
    db: Session = Depends(
        get_db
    ),
):

    match = (
        db.query(Match)
        .filter(
            Match.id == match_id
        )
        .first()
    )

    if match is None:

        raise HTTPException(
            status_code=404,
            detail="Match not found",
        )

    markets = {
        market.id:
            market.code
        for market
        in db.query(Market).all()
    }

    predictions = (
        db.query(
            MarketPrediction
        )
        .filter(
            MarketPrediction.match_id
            == match_id
        )
        .order_by(
            MarketPrediction.created_at.desc()
        )
        .all()
    )

    signals = (
        db.query(Signal)
        .filter(
            Signal.match_id
            == match_id
        )
        .order_by(
            Signal.created_at.desc()
        )
        .all()
    )

    return {
        "match":
            serialize_match(
                db,
                match,
            ),

        "market_predictions": [
            {
                "id":
                    prediction.id,

                "market_code":
                    markets.get(
                        prediction.market_id
                    ),

                "selection":
                    prediction.selection,

                "probability":
                    prediction.probability,

                "confidence":
                    prediction.confidence,

                "confidence_level":
                    prediction.confidence_level,

                "recommended":
                    prediction.is_recommended,

                "model_version":
                    prediction.model_version,
            }
            for prediction
            in predictions
        ],

        "signals": [
            serialize_signal(
                signal,
                markets.get(
                    signal.market_id
                ),
            )
            for signal
            in signals
        ],
    }


# ============================================================
# SIGNALS
# ============================================================

@router.get(
    "/signals"
)
def signals(
    value_only: bool = False,
    active_only: bool = True,
    limit: int = 100,
    db: Session = Depends(
        get_db
    ),
):

    query = (
        db.query(Signal)
    )

    if active_only:

        query = query.filter(
            Signal.active.is_(True)
        )

    if value_only:

        query = query.filter(
            Signal.is_value.is_(True)
        )

    rows = (
        query
        .order_by(
            Signal.created_at.desc()
        )
        .limit(
            min(
                max(
                    limit,
                    1,
                ),
                500,
            )
        )
        .all()
    )

    markets = {
        market.id:
            market.code
        for market
        in db.query(Market).all()
    }

    return {
        "count":
            len(rows),

        "items": [
            serialize_signal(
                row,
                markets.get(
                    row.market_id
                ),
            )
            for row
            in rows
        ],
    }


@router.get(
    "/signals/value"
)
def value_signals(
    limit: int = 100,
    db: Session = Depends(
        get_db
    ),
):

    now = datetime.now(
        timezone.utc
    )

    rows = (
        db.query(Signal)
        .join(
            Match,
            Match.id
            == Signal.match_id,
        )
        .filter(
            Signal.active.is_(True),
            Signal.is_value.is_(True),
            Match.match_date >= now,
        )
        .order_by(
            Signal.expected_value.desc()
        )
        .limit(
            min(
                max(
                    limit,
                    1,
                ),
                500,
            )
        )
        .all()
    )

    markets = {
        market.id:
            market.code
        for market
        in db.query(Market).all()
    }

    return {
        "count":
            len(rows),

        "items": [
            serialize_signal(
                row,
                markets.get(
                    row.market_id
                ),
            )
            for row
            in rows
        ],
    }


# ============================================================
# COMBINATIONS
# ============================================================

@router.get(
    "/combinations"
)
def combinations(
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(
        get_db
    ),
):

    query = (
        db.query(
            Combination
        )
    )

    if status:

        query = (
            query.filter(
                Combination.status
                == status
            )
        )

    rows = (
        query
        .order_by(
            Combination.created_at.desc()
        )
        .limit(
            min(
                max(
                    limit,
                    1,
                ),
                500,
            )
        )
        .all()
    )

    return {
        "count":
            len(rows),

        "items": [
            serialize_combination(
                db,
                row,
            )
            for row
            in rows
        ],
    }


@router.get(
    "/combinations/{combination_id}"
)
def combination_detail(
    combination_id: int,
    db: Session = Depends(
        get_db
    ),
):

    row = (
        db.query(Combination)
        .filter(
            Combination.id
            == combination_id
        )
        .first()
    )

    if row is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Combination not found"
            ),
        )

    return serialize_combination(
        db,
        row,
    )


# ============================================================
# MARKETS
# ============================================================

@router.get(
    "/markets"
)
def markets(
    db: Session = Depends(
        get_db
    ),
):

    rows = (
        db.query(Market)
        .order_by(
            Market.sport.asc(),
            Market.code.asc(),
        )
        .all()
    )

    return {
        "count":
            len(rows),

        "items": [
            {
                "id":
                    row.id,

                "sport":
                    row.sport,

                "code":
                    row.code,

                "name":
                    row.name,

                "category":
                    row.category,

                "enabled":
                    row.enabled,
            }
            for row
            in rows
        ],
    }


# ============================================================
# PERFORMANCE
# ============================================================

@router.get(
    "/stats"
)
def stats(
    db: Session = Depends(
        get_db
    ),
):

    signals = (
        db.query(Signal)
        .filter(
            Signal.is_value.is_(True),
            Signal.evaluated_at.isnot(None),
        )
        .all()
    )

    signal_wins = sum(
        1
        for row in signals
        if row.correct is True
    )

    signal_profit = sum(
        float(
            row.profit or 0
        )
        for row in signals
    )

    combinations = (
        db.query(Combination)
        .filter(
            Combination.evaluated_at.isnot(
                None
            )
        )
        .all()
    )

    combo_wins = sum(
        1
        for row in combinations
        if row.status == "won"
    )

    combo_profit = sum(
        float(
            row.profit or 0
        )
        for row in combinations
    )

    return {
        "value_signals": {
            "evaluated":
                len(signals),

            "wins":
                signal_wins,

            "losses":
                (
                    len(signals)
                    - signal_wins
                ),

            "hit_rate":
                round(
                    signal_wins
                    / len(signals)
                    * 100.0,
                    2,
                )
                if signals
                else 0.0,

            "profit_units":
                round(
                    signal_profit,
                    4,
                ),

            "roi":
                round(
                    signal_profit
                    / len(signals)
                    * 100.0,
                    2,
                )
                if signals
                else 0.0,
        },

        "combinations": {
            "evaluated":
                len(combinations),

            "wins":
                combo_wins,

            "losses":
                (
                    len(combinations)
                    - combo_wins
                ),

            "hit_rate":
                round(
                    combo_wins
                    / len(combinations)
                    * 100.0,
                    2,
                )
                if combinations
                else 0.0,

            "profit_units":
                round(
                    combo_profit,
                    4,
                ),

            "roi":
                round(
                    combo_profit
                    / len(combinations)
                    * 100.0,
                    2,
                )
                if combinations
                else 0.0,
        },
    }

# ============================================================
# AI TICKET BUILDER
# ============================================================

@router.post(
    "/ticket-builder",
    response_model=(
        TicketBuilderResponse
    ),
)
def ticket_builder(
    request: TicketBuilderRequest,
    db: Session = Depends(
        get_db
    ),
):

    return build_ticket(
        db=db,

        message=(
            request.message
        ),

        strategy=(
            request.strategy
        ),

        date=(
            request.date
        ),

        leagues=(
            request.leagues
        ),

        selections=(
            request.selections
        ),

        min_probability=(
            request.min_probability
        ),

        target_odds=(
            request.target_odds
        ),
    )

@router.get(
    "/optimized-tickets"
)
def optimized_tickets(
    days: int = 1,
    db: Session = Depends(
        get_db
    ),
):

    now = datetime.now(
        timezone.utc
    )

    db_now = (
        now.replace(
            tzinfo=None
        )
    )

    end = (
        db_now
        + timedelta(
            days=max(
                1,
                min(
                    days,
                    7,
                ),
            )
        )
    )

    results = []

    for strategy in [
        "SAFE",
        "BALANCED",
        "AGGRESSIVE",
    ]:

        result = (
            optimize_ticket(
                db,
                strategy=strategy,
                date_from=db_now,
                date_to=end,
            )
        )

        results.append(
            result
        )

    return {
        "generated_at":
            now.isoformat(),

        "days":
            days,

        "tickets":
            results,
    }