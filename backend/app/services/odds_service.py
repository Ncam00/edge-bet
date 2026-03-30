"""
Odds API ingestion service.
Pulls upcoming games and bookmaker odds from The Odds API.
Docs: https://the-odds-api.com/liveapi/guides/v4/
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import Game

logger = logging.getLogger(__name__)
settings = get_settings()

SPORT = "basketball_nba"
REGIONS = "us,uk,au"
MARKETS = "h2h,totals"
ODDS_FORMAT = "decimal"


async def fetch_upcoming_games(db: Session) -> list[dict]:
    """
    Fetch upcoming NBA games with bookmaker odds and upsert into DB.
    Returns list of raw game dicts from the API.
    """
    if not settings.odds_api_key:
        logger.warning("ODDS_API_KEY not set — skipping odds fetch")
        return []

    url = f"{settings.odds_api_base_url}/sports/{SPORT}/odds"
    params = {
        "apiKey": settings.odds_api_key,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": "iso",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        games_data = resp.json()

    logger.info(f"Fetched {len(games_data)} games from Odds API")
    _upsert_games(db, games_data)
    return games_data


def _upsert_games(db: Session, games_data: list[dict]) -> None:
    """Insert new games, skip existing ones (idempotent)."""
    for g in games_data:
        existing = db.query(Game).filter(Game.external_id == g["id"]).first()
        if existing:
            continue
        game = Game(
            external_id=g["id"],
            sport=g.get("sport_key", SPORT),
            home_team=g["home_team"],
            away_team=g["away_team"],
            commence_time=datetime.fromisoformat(g["commence_time"].replace("Z", "+00:00")),
        )
        db.add(game)
    db.commit()


def extract_best_odds(game_data: dict, market: str, selection: str) -> Optional[float]:
    """
    From raw odds API game dict, return the best decimal odds available
    across all bookmakers for a given market + selection.
    market: 'h2h' | 'totals'
    selection: team name (h2h) | 'Over' | 'Under' (totals)
    """
    best = None
    for bookmaker in game_data.get("bookmakers", []):
        for mkt in bookmaker.get("markets", []):
            if mkt["key"] != market:
                continue
            for outcome in mkt.get("outcomes", []):
                if outcome["name"] == selection:
                    price = outcome["price"]
                    if best is None or price > best:
                        best = price
    return best
