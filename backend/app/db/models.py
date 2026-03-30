from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class PlanType(str, enum.Enum):
    free = "free"
    premium = "premium"


class BetOutcome(str, enum.Enum):
    pending = "pending"
    win = "win"
    loss = "loss"
    push = "push"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.free)
    bankroll = Column(Float, default=1000.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bets = relationship("Bet", back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # odds API game id
    sport = Column(String, default="basketball_nba")
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    commence_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="upcoming")  # upcoming, live, completed
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    predictions = relationship("Prediction", back_populates="game")
    bets = relationship("Bet", back_populates="game")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    market = Column(String, nullable=False)       # h2h, totals, spreads
    selection = Column(String, nullable=False)     # home_win, over, etc.
    model_probability = Column(Float, nullable=False)
    implied_probability = Column(Float, nullable=False)
    decimal_odds = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=False) # (model_prob * odds) - 1
    confidence_label = Column(String, nullable=False)  # high, medium, low
    feature_summary = Column(Text, nullable=True)  # JSON string of key features
    model_version = Column(String, default="v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game", back_populates="predictions")
    bets = relationship("Bet", back_populates="prediction")


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    stake = Column(Float, nullable=False)
    decimal_odds = Column(Float, nullable=False)
    market = Column(String, nullable=False)
    selection = Column(String, nullable=False)
    outcome = Column(Enum(BetOutcome), default=BetOutcome.pending)
    profit_loss = Column(Float, nullable=True)
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
    settled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="bets")
    game = relationship("Game", back_populates="bets")
    prediction = relationship("Prediction", back_populates="bets")
