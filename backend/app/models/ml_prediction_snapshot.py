from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.database.database import Base


class MLPredictionSnapshot(Base):

    __tablename__ = (
        "ml_prediction_snapshots"
    )


    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )


    # ========================================================
    # MATCH
    # ========================================================

    match_id = Column(
        Integer,
        ForeignKey(
            "matches.id"
        ),
        nullable=False,
        index=True,
    )


    # ========================================================
    # MODEL
    # ========================================================

    model_version = Column(
        String,
        nullable=False,
        default=
            "logistic_regression_v2",
    )


    league = Column(
        String,
        nullable=False,
    )


    # ========================================================
    # PREDICTION
    # ========================================================

    pick = Column(
        String,
        nullable=False,
    )


    home_probability = Column(
        Float,
        nullable=False,
    )


    draw_probability = Column(
        Float,
        nullable=False,
    )


    away_probability = Column(
        Float,
        nullable=False,
    )


    confidence = Column(
        Float,
        nullable=False,
    )


    margin = Column(
        Float,
        nullable=False,
    )


    analitiko_score = Column(
        Float,
        nullable=False,
    )


    league_threshold = Column(
        Float,
        nullable=False,
    )


    is_strong_pick = Column(
        Boolean,
        nullable=False,
        default=False,
    )


    confidence_level = Column(
        String,
        nullable=False,
    )


    # ========================================================
    # SNAPSHOT TIME
    # ========================================================

    created_at = Column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=lambda:
            datetime.now(
                timezone.utc
            ),
    )


    # ========================================================
    # RESULT / EVALUATION
    # ========================================================

    actual_result = Column(
        String,
        nullable=True,
    )


    correct = Column(
        Boolean,
        nullable=True,
    )


    evaluated_at = Column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    elite_threshold = Column(
        Float,
        nullable=False,
        default=50.0,
    )

    is_elite_pick = Column(
        Boolean,
        nullable=False,
        default=False,
    )