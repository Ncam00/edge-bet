from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import Bet, BetOutcome, User, Game
from app.api.schemas import BetCreate, BetOut, BankrollStats

router = APIRouter(tags=["bets"])


# ── Log a bet ─────────────────────────────────────────────────
@router.post("/bets", response_model=BetOut, status_code=201)
def place_bet(
    body: BetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = db.query(Game).filter(Game.id == body.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    bet = Bet(
        user_id=current_user.id,
        game_id=body.game_id,
        prediction_id=body.prediction_id,
        stake=body.stake,
        decimal_odds=body.decimal_odds,
        market=body.market,
        selection=body.selection,
    )
    db.add(bet)
    current_user.bankroll -= body.stake
    db.commit()
    db.refresh(bet)
    return bet


# ── Bet history ───────────────────────────────────────────────
@router.get("/bets", response_model=list[BetOut])
def get_bets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Bet)
        .filter(Bet.user_id == current_user.id)
        .order_by(Bet.placed_at.desc())
        .limit(50)
        .all()
    )


# ── Bankroll stats ────────────────────────────────────────────
@router.get("/bankroll", response_model=BankrollStats)
def get_bankroll(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bets = db.query(Bet).filter(Bet.user_id == current_user.id).all()
    settled = [b for b in bets if b.outcome != BetOutcome.pending]
    wins = [b for b in settled if b.outcome == BetOutcome.win]
    losses = [b for b in settled if b.outcome == BetOutcome.loss]

    total_staked = sum(b.stake for b in bets)
    total_pl = sum(b.profit_loss or 0 for b in settled)
    win_rate = len(wins) / len(settled) if settled else None
    roi = total_pl / total_staked if total_staked > 0 else None

    return BankrollStats(
        bankroll=current_user.bankroll,
        total_bets=len(bets),
        settled_bets=len(settled),
        wins=len(wins),
        losses=len(losses),
        win_rate=round(win_rate, 4) if win_rate is not None else None,
        total_staked=round(total_staked, 2),
        total_profit_loss=round(total_pl, 2),
        roi=round(roi, 4) if roi is not None else None,
    )
