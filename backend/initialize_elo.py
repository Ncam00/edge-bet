"""
Initialize ELO ratings based on 2024-25 season standings.
Run this once to seed realistic ELO values.
"""
import sys
sys.path.insert(0, '.')

from app.ml.elo_system import EloSystem

# Current standings-based ELO estimates (March 2026)
# Based on win-loss records translated to ELO
INITIAL_ELO = {
    # Elite (Top 5)
    "Oklahoma City Thunder": 1680,
    "Cleveland Cavaliers": 1665,
    "Boston Celtics": 1655,
    "Denver Nuggets": 1620,
    "Houston Rockets": 1590,
    
    # Contenders (6-12)
    "Dallas Mavericks": 1575,
    "Minnesota Timberwolves": 1570,
    "Milwaukee Bucks": 1560,
    "Memphis Grizzlies": 1555,
    "LA Clippers": 1545,
    "Phoenix Suns": 1540,
    "Golden State Warriors": 1535,
    
    # Playoff bubble (13-18)
    "Miami Heat": 1525,
    "Los Angeles Lakers": 1520,
    "Indiana Pacers": 1515,
    "Detroit Pistons": 1505,
    "Sacramento Kings": 1500,
    "New York Knicks": 1498,
    
    # Below average (19-25)
    "Atlanta Hawks": 1480,
    "San Antonio Spurs": 1475,
    "Chicago Bulls": 1465,
    "Toronto Raptors": 1455,
    "Brooklyn Nets": 1450,
    "Portland Trail Blazers": 1440,
    "Orlando Magic": 1435,
    
    # Bottom tier (26-30)
    "Charlotte Hornets": 1395,
    "Utah Jazz": 1385,
    "New Orleans Pelicans": 1380,
    "Philadelphia 76ers": 1370,  # Injuries have hurt them
    "Washington Wizards": 1320,
}

def initialize_elo():
    """Initialize ELO ratings with season-accurate values."""
    elo = EloSystem()
    
    print("🏀 Initializing ELO Ratings for 2024-25 Season")
    print("=" * 50)
    
    for team, rating in INITIAL_ELO.items():
        elo.ratings[team] = rating
    
    elo.save_ratings()
    
    print("\n📊 Current Power Rankings:")
    print("-" * 50)
    
    for i, (team, rating) in enumerate(elo.get_top_teams(30), 1):
        tier = "🔥" if rating >= 1600 else "⭐" if rating >= 1500 else "📉"
        print(f"{i:2}. {tier} {team}: {rating:.0f}")
    
    # Test some matchup probabilities
    print("\n🎲 Sample Matchup Probabilities:")
    print("-" * 50)
    
    matchups = [
        ("Boston Celtics", "Los Angeles Lakers"),
        ("Oklahoma City Thunder", "Washington Wizards"),
        ("Phoenix Suns", "Miami Heat"),
        ("Cleveland Cavaliers", "Denver Nuggets"),
    ]
    
    for home, away in matchups:
        prob = elo.expected_score(home, away)
        print(f"   {away} @ {home}: {prob:.1%} home win")
    
    print("\n✅ ELO ratings initialized successfully!")
    print(f"   Saved to: data/elo_ratings.json")

if __name__ == "__main__":
    initialize_elo()
