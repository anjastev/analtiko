from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from app.database.database import Base


class HistorySyncState(Base):
    __tablename__ = "history_sync_states"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    last_attempt_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_success_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    latest_history_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_status = Column(
        String,
        nullable=True,
    )

    last_message = Column(
        String,
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda:
            datetime.now(
                timezone.utc
            ),
    )