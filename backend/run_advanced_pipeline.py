"""
Advanced Pipeline: Fetch odds → Run PATSM model → Calculate EV → Save predictions
================================================================================
Uses the Player-Adjusted Team Strength Model combining:
- ELO ratings (50%)
- Recent form (20%)  
- Efficiency matchup (20%)
- Player/injury adjustments (10%)
"""
import sys
sys.path.insert(0, '.')

import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.fetch_odds import fetch_nba_odds
from app.ml.advanced_model import get_advanced_model, AdvancedModel
from app.ml.ev_engine import compute_ev, confidence_label
from app.db.models import Base, Game, Prediction
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
Session = sessionmaker(bind=engine)


async def run_advanced_pipeline(apply_injuries: bool = True):
    """
    Main pipeline using the advanced PATSM model.
    
    Args:
        apply_injuries: If True, fetch and apply injury data
    """
    print("=" * 70)
    print("🏀 EdgeBet ADVANCED Pipeline - PATSM Model")
    print("=" * 70)
    
    # Initialize advanced model
    model = get_advanced_model()
    
    # Apply sample injuries (in production, fetch from API)
    if apply_injuries:
        print("\n🤕 Loading injury data...")
        # Sample injuries - replace with real API call
        injuries = [
            ("Philadelphia 76ers", "Joel Embiid", "questionable"),
            ("Milwaukee Bucks", "Khris Middleton", "out"),
            ("LA Clippers", "Kawhi Leonard", "questionable"),
            ("Phoenix Suns", "Bradley Beal", "doubtful"),
        ]
        for team, player, status in injuries:
            model.set_injury(team, player, status)
            print(f"   {player} ({team}): {status.upper()}")
    
    # 1. Fetch live odds
    print("\n📡 Fetching live odds...")
    result = await fetch_nba_odds()
    
    if not result["success"]:
        print(f"❌ Failed to fetch odds: {result.get('error')}")
        return
    
    games_data = result["games"]
    print(f"\n📊 Processing {len(games_data)} games with PATSM model...\n")
    
    # 2. Process each game
    db = Session()
    value_bets = []
    all_predictions = []
    
    for game_data in games_data:
        home = game_data["home_team"]
        away = game_data["away_team"]
        external_id = game_data["id"]
        commence = datetime.fromisoformat(game_data["commence_time"].replace("Z", "+00:00"))
        
        # Skip if no bookmakers
        if not game_data.get("bookmakers"):
            continue
        
        # Get best odds (first bookmaker)
        book = game_data["bookmakers"][0]
        outcomes = book["markets"][0]["outcomes"]
        
        home_odds = next((o["price"] for o in outcomes if o["name"] == home), None)
        away_odds = next((o["price"] for o in outcomes if o["name"] == away), None)
        
        if not home_odds or not away_odds:
            continue
        
        # Run ADVANCED model
        analysis = model.get_value_bet(home, away, home_odds, away_odds)
        prediction = analysis["prediction"]
        
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
        
        # Process value bets from model
        for bet in analysis["value_bets"]:
            selection = bet["selection"]
            odds = bet["odds"]
            model_prob = bet["model_prob"]
            implied_prob = bet["implied_prob"]
            ev = bet["ev"]
            conf = bet["confidence"]
            
            # Check if prediction exists
            existing_pred = db.query(Prediction).filter(
                Prediction.game_id == game.id,
                Prediction.selection == selection
            ).first()
            
            if existing_pred:
                # Update existing prediction
                existing_pred.model_probability = model_prob
                existing_pred.implied_probability = implied_prob
                existing_pred.decimal_odds = odds
                existing_pred.expected_value = ev
                existing_pred.confidence_label = conf
                existing_pred.feature_summary = json.dumps({
                    "model": "PATSM-v1",
                    "bookmaker": book["title"],
                    "elo_prob": prediction["elo_prob"],
                    "form_home": prediction["form_home"],
                    "form_away": prediction["form_away"],
                    "efficiency": prediction["efficiency"],
                    "player_adj": prediction["player_adj"],
                })
                existing_pred.model_version = "PATSM-v1"
            else:
                # Create new prediction
                pred = Prediction(
                    game_id=game.id,
                    market="h2h",
                    selection=selection,
                    model_probability=model_prob,
                    implied_probability=implied_prob,
                    decimal_odds=odds,
                    expected_value=ev,
                    confidence_label=conf,
                    feature_summary=json.dumps({
                        "model": "PATSM-v1",
                        "bookmaker": book["title"],
                        "elo_prob": prediction["elo_prob"],
                        "form_home": prediction["form_home"],
                        "form_away": prediction["form_away"],
                        "efficiency": prediction["efficiency"],
                        "player_adj": prediction["player_adj"],
                    }),
                    model_version="PATSM-v1"
                )
                db.add(pred)
            
            # Calculate Kelly stake
            stake = model.get_kelly_stake(model_prob, odds, 1000)
            
            value_bets.append({
                "game": f"{away} @ {home}",
                "pick": selection,
                "side": bet["side"],
                "odds": odds,
                "model": f"{model_prob*100:.1f}%",
                "implied": f"{implied_prob*100:.1f}%",
                "value": f"{bet['value']*100:+.1f}%",
                "ev": f"{ev*100:+.1f}%",
                "conf": conf,
                "kelly_stake": f"${stake}",
                "reasoning": {
                    "elo": f"{prediction['elo_prob']*100:.1f}%",
                    "form": f"H:{prediction['form_home']:.2f} A:{prediction['form_away']:.2f}",
                    "eff": f"{prediction['efficiency']:.2f}",
                }
            })
    
    db.commit()
    db.close()
    
    # 3. Print results
    print("=" * 70)
    print(f"🎯 VALUE BETS FOUND: {len(value_bets)}")
    print("=" * 70)
    
    if value_bets:
        # Sort by EV
        value_bets.sort(key=lambda x: float(x["ev"].replace("%", "").replace("+", "")), reverse=True)
        
        for bet in value_bets:
            emoji = "🟢" if bet["conf"] == "high" else "🟡" if bet["conf"] == "medium" else "⚪"
            print(f"\n{emoji} {bet['game']}")
            print(f"   📌 Pick: {bet['pick']} @ {bet['odds']}")
            print(f"   📊 Model: {bet['model']} vs Implied: {bet['implied']}")
            print(f"   💰 Value: {bet['value']} | EV: {bet['ev']} | Kelly: {bet['kelly_stake']}")
            print(f"   🧠 Reasoning: ELO={bet['reasoning']['elo']}, Form={bet['reasoning']['form']}, Eff={bet['reasoning']['eff']}")
            print(f"   🎯 Confidence: {bet['conf'].upper()}")
    else:
        print("\nNo value bets found at current odds.")
    
    print(f"\n✅ Saved to database. Check http://localhost:8000/api/v1/picks/today")
    print(f"📊 Model: PATSM-v1 (ELO 50% + Form 20% + Efficiency 20% + Player 10%)")
    
    return value_bets


if __name__ == "__main__":
    asyncio.run(run_advanced_pipeline())
