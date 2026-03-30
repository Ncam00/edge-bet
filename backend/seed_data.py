"""Seed demo data for EdgeBet"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import json

from app.db.models import Base, Game, Prediction
from app.ml.ev_engine import compute_ev, confidence_label

# Connect to SQLite
engine = create_engine('sqlite:///./edgebet.db')
Session = sessionmaker(bind=engine)
db = Session()

games_data = [
    {'id': 'nba_cel_heat', 'home': 'Boston Celtics', 'away': 'Miami Heat', 'home_odds': 1.65, 'away_odds': 2.30},
    {'id': 'nba_gsw_lakers', 'home': 'Golden State Warriors', 'away': 'LA Lakers', 'home_odds': 1.90, 'away_odds': 1.95},
    {'id': 'nba_nuggets_suns', 'home': 'Denver Nuggets', 'away': 'Phoenix Suns', 'home_odds': 1.55, 'away_odds': 2.55},
]

print("Seeding EdgeBet demo data...\n")

for g in games_data:
    existing = db.query(Game).filter(Game.external_id == g['id']).first()
    if not existing:
        game = Game(
            external_id=g['id'],
            sport='basketball_nba',
            home_team=g['home'],
            away_team=g['away'],
            commence_time=datetime.now(timezone.utc)
        )
        db.add(game)
        db.flush()
        
        implied = 1 / g['home_odds']
        model_prob = min(implied + 0.06, 0.85)
        ev = compute_ev(model_prob, g['home_odds'])
        conf = confidence_label(model_prob, ev)
        
        pred = Prediction(
            game_id=game.id,
            market='h2h',
            selection=g['home'],
            model_probability=round(model_prob, 4),
            implied_probability=round(implied, 4),
            decimal_odds=g['home_odds'],
            expected_value=ev,
            confidence_label=conf,
            feature_summary=json.dumps({'form': 'strong', 'h2h': 'favorable'}),
            model_version='v0.1'
        )
        db.add(pred)
        print(f"✅ {g['away']} @ {g['home']} | EV: {ev*100:+.1f}% | {conf}")
    else:
        print(f"⏭️  {g['away']} @ {g['home']} already exists")

db.commit()
db.close()
print("\n🎉 Done! Check http://localhost:8000/docs")
