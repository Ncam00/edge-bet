"""
Sports API Routes
Provides endpoints for multi-sport data and configuration.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.core.database import get_db
from app.services.sports_config import (
    SPORTS_CONFIG,
    get_active_sports,
    get_sports_by_category,
    get_all_categories,
    SportCategory,
)
from app.services.multi_sport_odds import get_multi_sport_odds_service
from app.db.models import Game, Prediction

router = APIRouter(tags=["sports"])


@router.get("/categories")
def list_categories():
    """Get all sport categories with their sports."""
    return get_all_categories()


@router.get("/available")
async def list_available_sports():
    """Get currently available sports from The Odds API."""
    service = get_multi_sport_odds_service()
    return await service.get_available_sports()


@router.get("/all")
def list_all_sports():
    """Get all configured sports."""
    return [
        {
            "key": s.key,
            "name": s.name,
            "category": s.category.value,
            "emoji": s.emoji,
            "active": s.active,
            "markets": s.markets,
        }
        for s in SPORTS_CONFIG.values()
    ]


@router.get("/{sport_key}/picks")
def get_sport_picks(
    sport_key: str,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Get value picks for a specific sport."""
    if sport_key not in SPORTS_CONFIG:
        return {"error": f"Unknown sport: {sport_key}", "picks": []}
    
    sport = SPORTS_CONFIG[sport_key]
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=12)
    end = now + timedelta(hours=72)
    
    # Query games for this sport
    picks = (
        db.query(Prediction)
        .join(Game)
        .filter(
            Game.sport == sport_key,
            Game.commence_time >= start,
            Game.commence_time < end,
            Prediction.expected_value >= 0.03,
        )
        .order_by(Prediction.expected_value.desc())
        .limit(limit)
        .all()
    )
    
    # If no DB picks, return demo data
    if not picks:
        return _get_demo_picks_for_sport(sport_key, sport)
    
    return {
        "sport": sport.name,
        "emoji": sport.emoji,
        "picks": [
            {
                "id": p.id,
                "game": {
                    "id": p.game.id,
                    "home_team": p.game.home_team,
                    "away_team": p.game.away_team,
                    "commence_time": p.game.commence_time.isoformat(),
                },
                "market": p.market,
                "selection": p.selection,
                "model_probability": p.model_probability,
                "implied_probability": p.implied_probability,
                "decimal_odds": p.decimal_odds,
                "expected_value": p.expected_value,
                "confidence_label": p.confidence_label,
            }
            for p in picks
        ],
    }


@router.get("/category/{category}/picks")
def get_category_picks(
    category: str,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Get value picks for all sports in a category."""
    try:
        cat = SportCategory(category)
    except ValueError:
        return {"error": f"Unknown category: {category}", "picks": []}
    
    sports = get_sports_by_category(cat)
    sport_keys = [s.key for s in sports]
    
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=12)
    end = now + timedelta(hours=72)
    
    picks = (
        db.query(Prediction)
        .join(Game)
        .filter(
            Game.sport.in_(sport_keys),
            Game.commence_time >= start,
            Game.commence_time < end,
            Prediction.expected_value >= 0.03,
        )
        .order_by(Prediction.expected_value.desc())
        .limit(limit)
        .all()
    )
    
    return {
        "category": category,
        "sports": [s.name for s in sports],
        "picks": [_format_pick(p) for p in picks] if picks else _get_demo_category_picks(cat),
    }


@router.post("/refresh")
async def refresh_odds(
    sport_key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Manually refresh odds for one or all sports.
    Admin/premium endpoint.
    """
    service = get_multi_sport_odds_service()
    
    if sport_key:
        if sport_key not in SPORTS_CONFIG:
            return {"error": f"Unknown sport: {sport_key}"}
        sport = SPORTS_CONFIG[sport_key]
        result = await service.fetch_sport_odds(db, sport)
        return {"sport": sport_key, "result": result}
    else:
        results = await service.fetch_all_sports(db)
        total = sum(r.get("games", 0) for r in results.values() if isinstance(r, dict))
        return {"total_games": total, "by_sport": results}


def _format_pick(p: Prediction) -> dict:
    """Format a prediction for API response."""
    return {
        "id": p.id,
        "sport": p.game.sport,
        "game": {
            "id": p.game.id,
            "home_team": p.game.home_team,
            "away_team": p.game.away_team,
            "commence_time": p.game.commence_time.isoformat(),
        },
        "market": p.market,
        "selection": p.selection,
        "model_probability": p.model_probability,
        "implied_probability": p.implied_probability,
        "decimal_odds": p.decimal_odds,
        "expected_value": p.expected_value,
        "confidence_label": p.confidence_label,
    }


def _get_demo_picks_for_sport(sport_key: str, sport) -> dict:
    """Generate demo picks for a sport."""
    import random
    from datetime import timedelta
    
    teams = {
        "basketball_nba": [("Lakers", "Celtics"), ("Warriors", "Suns"), ("Bucks", "Heat")],
        "americanfootball_nfl": [("Chiefs", "Eagles"), ("Bills", "Cowboys"), ("49ers", "Ravens")],
        "baseball_mlb": [("Yankees", "Dodgers"), ("Red Sox", "Cubs"), ("Astros", "Braves")],
        "icehockey_nhl": [("Bruins", "Rangers"), ("Maple Leafs", "Oilers"), ("Lightning", "Penguins")],
        "soccer_epl": [("Liverpool", "Man City"), ("Arsenal", "Chelsea"), ("Man Utd", "Tottenham")],
        "mma_mixed_martial_arts": [("Fighter A", "Fighter B"), ("Champion", "Challenger")],
    }
    
    matchups = teams.get(sport_key, [("Team A", "Team B"), ("Team C", "Team D")])
    picks = []
    
    for i, (home, away) in enumerate(matchups[:3]):
        ev = random.uniform(0.05, 0.20)
        picks.append({
            "id": i + 1,
            "game": {
                "id": i + 1,
                "home_team": home,
                "away_team": away,
                "commence_time": (datetime.now(timezone.utc) + timedelta(hours=i * 2 + 1)).isoformat(),
            },
            "market": random.choice(["h2h", "spreads", "totals"]),
            "selection": random.choice([home, away, "Over", "Under"]),
            "model_probability": round(random.uniform(0.45, 0.70), 3),
            "implied_probability": round(random.uniform(0.40, 0.55), 3),
            "decimal_odds": round(random.uniform(1.70, 2.50), 2),
            "expected_value": round(ev, 3),
            "confidence_label": "high" if ev > 0.10 else "medium",
        })
    
    return {
        "sport": sport.name,
        "emoji": sport.emoji,
        "picks": picks,
    }


def _get_demo_category_picks(category: SportCategory) -> list:
    """Generate demo picks for a category."""
    return []  # Return empty for simplicity
