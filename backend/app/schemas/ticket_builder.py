from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)


class TicketBuilderRequest(BaseModel):

    message: str = Field(
        min_length=2,
        max_length=1000,
    )

    sport: str = "football"

    strategy: Optional[str] = None

    date: Optional[str] = None

    leagues: Optional[list[str]] = None

    selections: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
    )

    min_probability: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    target_odds: Optional[float] = Field(
        default=None,
        gt=1.0,
    )


class ParsedTicketRequest(BaseModel):

    sport: str

    strategy: str

    date: str

    leagues: list[str]

    selections: int

    min_probability: float

    target_odds: Optional[float]


class TicketBuilderSelection(BaseModel):

    signal_id: int

    match_id: int

    match: str

    league: str | None

    kickoff: str | None

    market: str

    selection: str

    probability: float

    market_probability: float | None

    edge: float | None

    expected_value: float | None

    odds: float

    bookmaker: str | None


class TicketBuilderResponse(BaseModel):

    success: bool

    message: str

    parsed_request: ParsedTicketRequest

    selections: list[
        TicketBuilderSelection
    ]

    total_odds: float | None

    estimated_probability: float | None

    strategy: str

    risk_level: str

    candidates_found: int