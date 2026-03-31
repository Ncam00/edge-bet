"""
Multi-Sport Odds Service
Fetches odds from The Odds API for all supported sports.
"""
import httpx
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import Game
from app.services.sports_config import (
    SPORTS_CONFIG, 
    get_active_sports, 
    SportConfig,
    SportCategory,
)

logger = logging.getLogger(__name__)
settings = get_settings()

REGIONS = "us,uk,au,eu"
ODDS_FORMAT = "decimal"


class MultiSportOddsService:
    """Service for fetching odds across all sports."""
    
    def __init__(self):
        self.api_key = settings.odds_api_key
        self.base_url = settings.odds_api_base_url
        
    async def fetch_all_sports(self, db: Session) -> dict:
        """
        Fetch odds for all active sports.
        Returns dict with counts per sport.
        """
        results = {}
        active_sports = get_active_sports()
        
        # Fetch in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(active_sports), batch_size):
            batch = active_sports[i:i + batch_size]
            tasks = [self.fetch_sport_odds(db, sport) for sport in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for sport, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching {sport.key}: {result}")
                    results[sport.key] = {"error": str(result)}
                else:
                    results[sport.key] = result
            
            # Small delay between batches
            if i + batch_size < len(active_sports):
                await asyncio.sleep(0.5)
        
        return results
    
    async def fetch_sport_odds(
        self, 
        db: Session, 
        sport: SportConfig,
        days_ahead: int = 7
    ) -> dict:
        """
        Fetch odds for a specific sport.
        Returns dict with game count and details.
        """
        if not self.api_key:
            logger.warning("ODDS_API_KEY not set — skipping odds fetch")
            return {"games": 0, "error": "No API key"}
        
        markets = ",".join(sport.markets)
        
        url = f"{self.base_url}/sports/{sport.key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": REGIONS,
            "markets": markets,
            "oddsFormat": ODDS_FORMAT,
            "dateFormat": "iso",
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                
                # Handle no events for this sport
                if resp.status_code == 404:
                    return {"games": 0, "sport": sport.name}
                    
                resp.raise_for_status()
                games_data = resp.json()
            
            logger.info(f"Fetched {len(games_data)} {sport.name} games")
            self._upsert_games(db, games_data, sport)
            
            return {
                "games": len(games_data),
                "sport": sport.name,
                "category": sport.category.value,
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {"games": 0, "error": "Invalid API key"}
            raise
    
    def _upsert_games(
        self, 
        db: Session, 
        games_data: list[dict],
        sport: SportConfig
    ) -> int:
        """Insert/update games. Returns count of new games."""
        new_count = 0
        
        for g in games_data:
            existing = db.query(Game).filter(Game.external_id == g["id"]).first()
            
            # Convert bookmakers to JSON string
            import json
            raw_odds_json = json.dumps(g.get("bookmakers", []))
            
            if existing:
                # Update existing game odds
                existing.raw_odds = raw_odds_json
                continue
                
            game = Game(
                external_id=g["id"],
                sport=sport.key,
                home_team=g["home_team"],
                away_team=g["away_team"],
                commence_time=datetime.fromisoformat(
                    g["commence_time"].replace("Z", "+00:00")
                ),
                raw_odds=raw_odds_json,
            )
            db.add(game)
            new_count += 1
        
        db.commit()
        return new_count
    
    async def fetch_category(
        self,
        db: Session,
        category: SportCategory
    ) -> dict:
        """Fetch odds for all sports in a category."""
        sports = [s for s in get_active_sports() if s.category == category]
        
        results = {}
        for sport in sports:
            results[sport.key] = await self.fetch_sport_odds(db, sport)
        
        return results
    
    async def get_available_sports(self) -> list[dict]:
        """
        Query The Odds API for currently available sports.
        Returns list of sports with active events.
        """
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/sports"
        params = {"apiKey": self.api_key}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                sports = resp.json()
            
            # Match with our config
            available = []
            for sport in sports:
                config = SPORTS_CONFIG.get(sport["key"])
                available.append({
                    "key": sport["key"],
                    "name": config.name if config else sport["title"],
                    "emoji": config.emoji if config else "🎯",
                    "active": sport.get("active", False),
                    "has_outrights": sport.get("has_outrights", False),
                    "configured": config is not None,
                })
            
            return available
            
        except Exception as e:
            logger.error(f"Error fetching available sports: {e}")
            return []


# Singleton instance
_odds_service: Optional[MultiSportOddsService] = None


def get_multi_sport_odds_service() -> MultiSportOddsService:
    """Get or create the multi-sport odds service."""
    global _odds_service
    if _odds_service is None:
        _odds_service = MultiSportOddsService()
    return _odds_service


def extract_best_odds(
    game_data: dict, 
    market: str, 
    selection: str
) -> Optional[float]:
    """
    From raw odds API game dict, return the best decimal odds available
    across all bookmakers for a given market + selection.
    """
    best = None
    bookmakers = game_data.get("bookmakers", [])
    if not bookmakers:
        bookmakers = game_data.get("raw_odds", [])
    
    for bookmaker in bookmakers:
        for mkt in bookmaker.get("markets", []):
            if mkt["key"] != market:
                continue
            for outcome in mkt.get("outcomes", []):
                if outcome["name"] == selection or selection in outcome["name"]:
                    price = outcome["price"]
                    if best is None or price > best:
                        best = price
    return best
