"""Fetch real NBA odds from The Odds API"""
import httpx
import os
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"


async def fetch_nba_odds() -> dict:
    """Fetch upcoming NBA games with h2h odds"""
    url = f"{BASE_URL}/sports/basketball_nba/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,au",  # US and AU bookmakers
        "markets": "h2h",
        "oddsFormat": "decimal",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            remaining = response.headers.get("x-requests-remaining", "?")
            print(f"✅ Odds API: {len(data)} games | Requests remaining: {remaining}")
            return {"success": True, "games": data, "remaining": remaining}
        else:
            print(f"❌ Odds API error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}


def sync_fetch_nba_odds() -> dict:
    """Synchronous version for scripts"""
    import asyncio
    return asyncio.run(fetch_nba_odds())


if __name__ == "__main__":
    result = sync_fetch_nba_odds()
    if result["success"]:
        for game in result["games"][:5]:  # Show first 5
            home = game["home_team"]
            away = game["away_team"]
            start = game["commence_time"]
            
            # Get best odds
            if game.get("bookmakers"):
                book = game["bookmakers"][0]
                outcomes = book["markets"][0]["outcomes"]
                home_odds = next((o["price"] for o in outcomes if o["name"] == home), None)
                away_odds = next((o["price"] for o in outcomes if o["name"] == away), None)
                print(f"{away} @ {home} | {home}: {home_odds} | {away}: {away_odds}")
            else:
                print(f"{away} @ {home} | No odds available")
