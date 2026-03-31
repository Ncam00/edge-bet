"""
Test all EdgeBet models - PATSM, Player Props, Live Betting, Sharp Money.
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime

def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def test_player_props():
    """Test Player Props Model."""
    print_header("🏀 PLAYER PROPS MODEL (PPM)")
    
    from app.ml.player_props import PlayerPropsModel
    
    model = PlayerPropsModel(
        missing_players={
            "Milwaukee Bucks": ["Khris Middleton"],
            "Phoenix Suns": ["Bradley Beal"],
        }
    )
    
    # Test individual prediction
    pred = model.predict_prop(
        player_name="Giannis Antetokounmpo",
        opponent="Miami Heat",
        prop_type="points",
        line=28.5,
        odds_over=1.87,
        odds_under=1.93,
    )
    
    if pred:
        print(f"\n📊 {pred.player} ({pred.team}) vs {pred.opponent}")
        print(f"   Prop: {pred.prop_type.upper()} {pred.line}")
        print(f"   Projection: {pred.projection} (±{pred.std_dev})")
        print(f"   OVER: {pred.prob_over:.1%} vs {pred.implied_over:.1%} = {pred.value_over:+.1%}")
        print(f"   UNDER: {pred.prob_under:.1%} vs {pred.implied_under:.1%} = {pred.value_under:+.1%}")
        if pred.best_bet:
            print(f"   🎯 BET: {pred.best_bet} ({pred.confidence})")
    
    # Scan multiple props
    sample_props = [
        {"player": "LeBron James", "opponent": "Phoenix Suns", "prop_type": "points", "line": 24.5, "odds_over": 1.90, "odds_under": 1.90},
        {"player": "Stephen Curry", "opponent": "Portland Trail Blazers", "prop_type": "points", "line": 25.5, "odds_over": 1.85, "odds_under": 1.95},
        {"player": "Nikola Jokic", "opponent": "Golden State Warriors", "prop_type": "rebounds", "line": 11.5, "odds_over": 1.88, "odds_under": 1.92},
        {"player": "Luka Doncic", "opponent": "Minnesota Timberwolves", "prop_type": "assists", "line": 8.5, "odds_over": 1.82, "odds_under": 1.98},
    ]
    
    value_props = model.scan_all_props(sample_props)
    
    print(f"\n🎯 VALUE PROPS FOUND: {len(value_props)}")
    for prop in value_props:
        print(f"   • {prop.player}: {prop.prop_type.upper()} {prop.best_bet} {prop.line}")
        print(f"     Proj={prop.projection}, Value={max(prop.value_over, prop.value_under):+.1%} ({prop.confidence})")

def test_live_betting():
    """Test Live Betting Model."""
    print_header("⚡ LIVE BETTING MODEL (LBM)")
    
    from app.ml.live_betting import LiveBettingModel, GameState, MomentumData
    
    model = LiveBettingModel()
    
    # Simulate a game scenario
    game = GameState(
        home_team="Boston Celtics",
        away_team="Los Angeles Lakers",
        home_score=52,
        away_score=61,
        quarter=2,
        minutes_remaining=2.5,
    )
    
    momentum = MomentumData(
        home_last_3min_points=4,
        away_last_3min_points=12,
    )
    
    pred = model.predict(
        game_state=game,
        pre_game_prob=0.65,  # Celtics were favored
        momentum=momentum,
        live_odds_home=2.50,  # Market shifted to Lakers
        live_odds_away=1.58,
    )
    
    print(f"\n🏀 LIVE: {pred.away_team} @ {pred.home_team}")
    print(f"   State: {pred.game_state} | Score: {game.away_score}-{game.home_score}")
    print(f"   Pre-game: {pred.pre_game_prob:.1%} home → Live: {pred.live_prob:.1%} home")
    print(f"   Momentum: {pred.momentum_score:+.2f}")
    print(f"   Expected Final: {pred.expected_final_away:.0f}-{pred.expected_final_home:.0f}")
    print(f"   HOME: {pred.live_prob:.1%} vs {pred.implied_home:.1%} = {pred.value_home:+.1%}")
    print(f"   AWAY: {1-pred.live_prob:.1%} vs {pred.implied_away:.1%} = {pred.value_away:+.1%}")
    if pred.signal_type:
        print(f"   ⚡ Signal: {pred.signal_type}")
    if pred.best_bet:
        print(f"   🎯 BET: {pred.best_bet} ({pred.confidence})")

def test_sharp_money():
    """Test Sharp Money Detection."""
    print_header("🔍 SHARP MONEY DETECTION (SMDE)")
    
    from app.ml.sharp_money import SharpMoneyDetector, BettingDistribution, OddsSnapshot
    from datetime import timedelta
    
    detector = SharpMoneyDetector()
    now = datetime.now()
    
    # Add historical odds
    detector.add_odds_snapshot("bos_lal", OddsSnapshot(
        timestamp=now - timedelta(hours=6),
        home_odds=1.55,
        away_odds=2.45,
    ))
    detector.add_odds_snapshot("bos_lal", OddsSnapshot(
        timestamp=now,
        home_odds=1.62,
        away_odds=2.35,
    ))
    
    # Analyze with betting distribution
    signal = detector.analyze(
        game_id="bos_lal",
        home_team="Boston Celtics",
        away_team="Los Angeles Lakers",
        opening_home_odds=1.55,
        current_home_odds=1.62,
        opening_away_odds=2.45,
        current_away_odds=2.35,
        distribution=BettingDistribution(
            bet_percent_home=0.72,  # 72% public on home
            money_percent_home=0.52,  # But only 52% of money
        ),
    )
    
    print(f"\n🔍 {signal.away_team} @ {signal.home_team}")
    print(f"   Signal Strength: {signal.signal_strength:.1%}")
    print(f"   Alert Type: {signal.alert_type}")
    print(f"   RLM: {'✅' if signal.reverse_line_movement else '❌'}")
    print(f"   Steam: {'✅' if signal.steam_move else '❌'}")
    print(f"   Public Side: {signal.public_side}")
    print(f"   Sharp Side: {signal.smart_money_side or 'Unknown'}")
    print(f"   Line Movement: {signal.line_movement:+.2%}")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Reasoning: {signal.reasoning}")
    print(f"   📌 {signal.recommendation}")
    
    # Test multiple games
    games = [
        {
            "game_id": "mia_mil",
            "home_team": "Miami Heat",
            "away_team": "Milwaukee Bucks",
            "opening_home_odds": 2.10,
            "current_home_odds": 2.25,
            "opening_away_odds": 1.75,
            "current_away_odds": 1.68,
            "distribution": BettingDistribution(bet_percent_home=0.42, money_percent_home=0.58),
        },
        {
            "game_id": "okc_dal",
            "home_team": "Oklahoma City Thunder",
            "away_team": "Dallas Mavericks",
            "opening_home_odds": 1.65,
            "current_home_odds": 1.58,
            "opening_away_odds": 2.30,
            "current_away_odds": 2.42,
            "distribution": BettingDistribution(bet_percent_home=0.55, money_percent_home=0.72),
        },
    ]
    
    signals = detector.scan_all_games(games)
    
    if signals:
        print(f"\n🎯 SHARP SIGNALS: {len(signals)}")
        for s in signals:
            print(f"   • {s.away_team} @ {s.home_team}: {s.alert_type}")
            print(f"     {s.recommendation}")

def test_patsm():
    """Test PATSM model (existing)."""
    print_header("📊 PATSM MODEL (Pre-game)")
    
    from app.ml.advanced_model import AdvancedModel
    
    model = AdvancedModel(
        injuries={
            "Milwaukee Bucks": [("Khris Middleton", "out")],
            "Philadelphia 76ers": [("Joel Embiid", "questionable")],
        }
    )
    
    # Test a matchup
    result = model.predict(
        home_team="Boston Celtics",
        away_team="Los Angeles Lakers",
        home_odds=1.55,
        away_odds=2.45,
    )
    
    print(f"\n🏀 {result['away_team']} @ {result['home_team']}")
    print(f"   Model: {result['home_prob']:.1%} home | {result['away_prob']:.1%} away")
    print(f"   ELO: {result['elo_prob']:.1%} | Form: {result['form_score']:.2f}")
    print(f"   Efficiency: {result['efficiency_score']:.2f}")
    if result.get('value_bet'):
        print(f"   🎯 VALUE: {result['value_bet']} (+{result['value']:.1%} EV)")


def main():
    print("\n" + "🎰 "*20)
    print("   EDGEBET FULL MODEL TEST")
    print("🎰 "*20)
    
    try:
        test_patsm()
    except Exception as e:
        print(f"❌ PATSM test failed: {e}")
    
    try:
        test_player_props()
    except Exception as e:
        print(f"❌ Player Props test failed: {e}")
    
    try:
        test_live_betting()
    except Exception as e:
        print(f"❌ Live Betting test failed: {e}")
    
    try:
        test_sharp_money()
    except Exception as e:
        print(f"❌ Sharp Money test failed: {e}")
    
    print_header("✅ ALL TESTS COMPLETE")
    print("\n🚀 EdgeBet Full Stack:")
    print("   1. PATSM - Pre-game value bets (ELO + Form + Efficiency + Injuries)")
    print("   2. PPM - Player props (Points, Rebounds, Assists)")
    print("   3. LBM - Live betting (Momentum, Pace, Overreaction)")
    print("   4. SMDE - Sharp money detection (RLM, Steam, Money Mismatch)")
    print("\n📱 Frontend: http://localhost:8081")
    print("🔌 Backend: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
