from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.db.models import BetOutcome, PlanType


# ── Auth ──────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    plan: PlanType


# ── Games ─────────────────────────────────────────────────────
class GameOut(BaseModel):
    id: int
    home_team: str
    away_team: str
    commence_time: datetime
    status: str

    class Config:
        from_attributes = True


# ── Predictions ───────────────────────────────────────────────
class PredictionOut(BaseModel):
    id: int
    game: GameOut
    market: str
    selection: str
    model_probability: float
    implied_probability: float
    decimal_odds: float
    expected_value: float
    confidence_label: str
    feature_summary: Optional[str] = None

    class Config:
        from_attributes = True


# ── Bets ──────────────────────────────────────────────────────
class BetCreate(BaseModel):
    game_id: int
    prediction_id: Optional[int] = None
    stake: float
    decimal_odds: float
    market: str
    selection: str


class BetOut(BaseModel):
    id: int
    game: GameOut
    stake: float
    decimal_odds: float
    market: str
    selection: str
    outcome: BetOutcome
    profit_loss: Optional[float] = None
    placed_at: datetime

    class Config:
        from_attributes = True


# ── Bankroll ──────────────────────────────────────────────────
class BankrollStats(BaseModel):
    bankroll: float
    total_bets: int
    settled_bets: int
    wins: int
    losses: int
    win_rate: Optional[float]
    total_staked: float
    total_profit_loss: float
    roi: Optional[float]
