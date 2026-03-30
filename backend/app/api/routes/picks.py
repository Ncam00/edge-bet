from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import Prediction, Game, User, PlanType
from app.api.schemas import PredictionOut

router = APIRouter(prefix="/picks", tags=["picks"])

FREE_PICKS_LIMIT = 2


@router.get("/today", response_model=list[PredictionOut])
def get_todays_picks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns upcoming value bets (next 48 hours), sorted by EV descending.
    Free users see top 2. Premium users see all.
    """
    now = datetime.now(timezone.utc)
    # Include games from past 24h (in case of timezone issues) to next 48h
    start_window = now - timedelta(hours=24)
    end_window = now + timedelta(hours=48)

    picks = (
        db.query(Prediction)
        .join(Game)
        .filter(
            Game.commence_time >= start_window,
            Game.commence_time < end_window,
            Prediction.expected_value >= 0.03,
        )
        .order_by(Prediction.expected_value.desc())
        .all()
    )

    if current_user.plan == PlanType.free:
        picks = picks[:FREE_PICKS_LIMIT]

    return picks


@router.get("/{prediction_id}", response_model=PredictionOut)
def get_pick_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full detail view of a single prediction including model reasoning.
    Feature summary only available to premium users.
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Pick not found")

    # Strip feature detail from free users
    if current_user.plan == PlanType.free:
        prediction.feature_summary = None

    return prediction
