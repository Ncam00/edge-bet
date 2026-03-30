"""
Full pipeline: Fetch odds → Run model → Calculate EV → Save predictions
"""
import sys
sys.path.insert(0, '.')

import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.fetch_odds import fetch_nba_odds
from app.ml.ev_engine import compute_ev, implied_probability, confidence_label
from app.db.models import Base, Game, Prediction
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
Session = sessionmaker(bind=engine)


def estimate_model_probability(home_team: str, away_team: str, home_implied: float) -> float:
    """
    Simple model: adjust implied probability based on known factors.
    In production, this would use XGBoost with real features.
    """
    # Known strong home teams (simplified for MVP)
    strong_home = ["Boston Celtics", "Denver Nuggets", "Oklahoma City Thunder", "Cleveland Cavaliers"]
    weak_away = ["Chicago Bulls", "Washington Wizards", "Utah Jazz", "Portland Trail Blazers"]
    
    adjustment = 0.0
    
    if home_team in strong_home:
        adjustment += 0.03
    if away_team in weak_away:
        adjustment += 0.02
    
    # Add slight home court advantage not fully priced in
    adjustment += 0.015
    
    # Cap probability
    model_prob = min(max(home_implied + adjustment, 0.1), 0.95)
    return round(model_prob, 4)


async def run_pipeline():
    """Main pipeline: fetch → predict → save"""
    print("=" * 60)
    print("🏀 EdgeBet Pipeline - Fetching NBA Odds")
    print("=" * 60)
    
    # 1. Fetch live odds
    result = await fetch_nba_odds()
    if not result["success"]:
        print(f"❌ Failed to fetch odds: {result.get('error')}")
        return
    
    games_data = result["games"]
    print(f"\n📊 Processing {len(games_data)} games...\n")
    
    # 2. Process each game
    db = Session()
    value_bets = []
    
    for game_data in games_data:
        home = game_data["home_team"]
        away = game_data["away_team"]
        external_id = game_data["id"]
        commence = datetime.fromisoformat(game_data["commence_time"].replace("Z", "+00:00"))
        
        # Skip if no bookmakers
        if not game_data.get("bookmakers"):
            continue
        
        # Get best odds (first bookmaker for simplicity)
        book = game_data["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]
        
        home_odds = next((o["price"] for o in outcomes if o["name"] == home), None)
        away_odds = next((o["price"] for o in outcomes if o["name"] == away), None)
        
        if not home_odds or not away_odds:
            continue
        
        # Calculate implied probabilities
        home_implied = implied_probability(home_odds)
        away_implied = implied_probability(away_odds)
        
        # Run model prediction
        home_model_prob = estimate_model_probability(home, away, home_implied)
        away_model_prob = 1 - home_model_prob
        
        # Calculate EVs
        home_ev = compute_ev(home_model_prob, home_odds)
        away_ev = compute_ev(away_model_prob, away_odds)
        
        # Check/create game in DB
        existing_game = db.query(Game).filter(Game.external_id == external_id).first()
        if not existing_game:
            game = Game(
                external_id=external_id,
                sport="basketball_nba",
                home_team=home,
                away_team=away,
                commence_time=commence
            )
            db.add(game)
            db.flush()
        else:
            game = existing_game
        
        # Create predictions for both sides if EV > 0
        for selection, odds, model_prob, implied, ev in [
            (home, home_odds, home_model_prob, home_implied, home_ev),
            (away, away_odds, away_model_prob, away_implied, away_ev)
        ]:
            if ev > 0:
                # Check if prediction exists
                existing_pred = db.query(Prediction).filter(
                    Prediction.game_id == game.id,
                    Prediction.selection == selection
                ).first()
                
                if not existing_pred:
                    conf = confidence_label(model_prob, ev)
                    pred = Prediction(
                        game_id=game.id,
                        market="h2h",
                        selection=selection,
                        model_probability=model_prob,
                        implied_probability=round(implied, 4),
                        decimal_odds=odds,
                        expected_value=ev,
                        confidence_label=conf,
                        feature_summary=json.dumps({
                            "bookmaker": book["title"],
                            "last_update": book["last_update"]
                        }),
                        model_version="v0.1-simple"
                    )
                    db.add(pred)
                    
                    value_bets.append({
                        "game": f"{away} @ {home}",
                        "pick": selection,
                        "odds": odds,
                        "model": f"{model_prob*100:.1f}%",
                        "implied": f"{implied*100:.1f}%",
                        "ev": f"{ev*100:+.1f}%",
                        "conf": conf
                    })
    
    db.commit()
    db.close()
    
    # 3. Print results
    print("=" * 60)
    print(f"🎯 VALUE BETS FOUND: {len(value_bets)}")
    print("=" * 60)
    
    if value_bets:
        # Sort by EV
        value_bets.sort(key=lambda x: float(x["ev"].replace("%", "").replace("+", "")), reverse=True)
        
        for bet in value_bets:
            emoji = "🟢" if "high" in bet["conf"] else "🟡" if "medium" in bet["conf"] else "⚪"
            print(f"{emoji} {bet['game']}")
            print(f"   Pick: {bet['pick']} @ {bet['odds']}")
            print(f"   Model: {bet['model']} vs Implied: {bet['implied']} → EV: {bet['ev']}")
            print()
    else:
        print("No value bets found at current odds.")
    
    print(f"\n✅ Saved to database. Check http://localhost:8000/api/v1/picks/today")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
