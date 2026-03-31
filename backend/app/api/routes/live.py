"""
API routes for Live Betting and Sharp Money Detection.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.ml.live_betting import LiveBettingModel, GameState, MomentumData
from app.ml.sharp_money import SharpMoneyDetector, BettingDistribution, OddsSnapshot

router = APIRouter()


# ─── Live Betting ───────────────────────────────────────────────────

class LiveGameRequest(BaseModel):
    """Request for live game analysis."""
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: int
    minutes_remaining: float
    pre_game_prob: float  # Pre-game home win probability
    live_odds_home: float = 2.0
    live_odds_away: float = 2.0
    home_last_3min_points: int = 0
    away_last_3min_points: int = 0


class LivePredictionResponse(BaseModel):
    """Live betting prediction response."""
    home_team: str
    away_team: str
    game_state: str
    pre_game_prob: float
    live_prob: float
    momentum_score: float
    expected_final_home: float
    expected_final_away: float
    implied_home: float
    implied_away: float
    value_home: float
    value_away: float
    best_bet: Optional[str]
    signal_type: Optional[str]
    confidence: str
    reasoning: str


@router.post("/analyze", response_model=LivePredictionResponse)
async def analyze_live_game(request: LiveGameRequest):
    """Analyze a live game for betting value."""
    model = LiveBettingModel()
    
    game_state = GameState(
        home_team=request.home_team,
        away_team=request.away_team,
        home_score=request.home_score,
        away_score=request.away_score,
        quarter=request.quarter,
        minutes_remaining=request.minutes_remaining,
    )
    
    momentum = MomentumData(
        home_last_3min_points=request.home_last_3min_points,
        away_last_3min_points=request.away_last_3min_points,
    )
    
    prediction = model.predict(
        game_state=game_state,
        pre_game_prob=request.pre_game_prob,
        momentum=momentum,
        live_odds_home=request.live_odds_home,
        live_odds_away=request.live_odds_away,
    )
    
    return LivePredictionResponse(
        home_team=prediction.home_team,
        away_team=prediction.away_team,
        game_state=prediction.game_state,
        pre_game_prob=prediction.pre_game_prob,
        live_prob=prediction.live_prob,
        momentum_score=prediction.momentum_score,
        expected_final_home=prediction.expected_final_home,
        expected_final_away=prediction.expected_final_away,
        implied_home=prediction.implied_home,
        implied_away=prediction.implied_away,
        value_home=prediction.value_home,
        value_away=prediction.value_away,
        best_bet=prediction.best_bet,
        signal_type=prediction.signal_type,
        confidence=prediction.confidence,
        reasoning=prediction.reasoning,
    )


# ─── Sharp Money Detection ──────────────────────────────────────────

class SharpAnalysisRequest(BaseModel):
    """Request for sharp money analysis."""
    game_id: str
    home_team: str
    away_team: str
    opening_home_odds: float
    current_home_odds: float
    opening_away_odds: float
    current_away_odds: float
    bet_percent_home: float = 0.5
    money_percent_home: float = 0.5


class SharpSignalResponse(BaseModel):
    """Sharp money signal response."""
    game_id: str
    home_team: str
    away_team: str
    signal_strength: float
    reverse_line_movement: bool
    steam_move: bool
    smart_money_side: Optional[str]
    public_side: str
    line_movement: float
    velocity: float
    confidence: str
    alert_type: str
    reasoning: str
    recommendation: str


# Global detector to maintain odds history
sharp_detector = SharpMoneyDetector()


@router.post("/sharp/analyze", response_model=SharpSignalResponse)
async def analyze_sharp_money(request: SharpAnalysisRequest):
    """Analyze a game for sharp money signals."""
    # Add current odds to history
    sharp_detector.add_odds_snapshot(
        request.game_id,
        OddsSnapshot(
            timestamp=datetime.now(),
            home_odds=request.current_home_odds,
            away_odds=request.current_away_odds,
        )
    )
    
    distribution = BettingDistribution(
        bet_percent_home=request.bet_percent_home,
        money_percent_home=request.money_percent_home,
    )
    
    signal = sharp_detector.analyze(
        game_id=request.game_id,
        home_team=request.home_team,
        away_team=request.away_team,
        opening_home_odds=request.opening_home_odds,
        current_home_odds=request.current_home_odds,
        opening_away_odds=request.opening_away_odds,
        current_away_odds=request.current_away_odds,
        distribution=distribution,
    )
    
    return SharpSignalResponse(
        game_id=signal.game_id,
        home_team=signal.home_team,
        away_team=signal.away_team,
        signal_strength=signal.signal_strength,
        reverse_line_movement=signal.reverse_line_movement,
        steam_move=signal.steam_move,
        smart_money_side=signal.smart_money_side,
        public_side=signal.public_side,
        line_movement=signal.line_movement,
        velocity=signal.velocity,
        confidence=signal.confidence,
        alert_type=signal.alert_type,
        reasoning=signal.reasoning,
        recommendation=signal.recommendation,
    )


class SharpBatchRequest(BaseModel):
    """Request to scan multiple games."""
    games: List[SharpAnalysisRequest]


@router.post("/sharp/scan", response_model=List[SharpSignalResponse])
async def scan_sharp_signals(request: SharpBatchRequest):
    """Scan multiple games for sharp money signals."""
    games_data = []
    
    for game in request.games:
        # Add to history
        sharp_detector.add_odds_snapshot(
            game.game_id,
            OddsSnapshot(
                timestamp=datetime.now(),
                home_odds=game.current_home_odds,
                away_odds=game.current_away_odds,
            )
        )
        
        games_data.append({
            "game_id": game.game_id,
            "home_team": game.home_team,
            "away_team": game.away_team,
            "opening_home_odds": game.opening_home_odds,
            "current_home_odds": game.current_home_odds,
            "opening_away_odds": game.opening_away_odds,
            "current_away_odds": game.current_away_odds,
            "distribution": BettingDistribution(
                bet_percent_home=game.bet_percent_home,
                money_percent_home=game.money_percent_home,
            ),
        })
    
    signals = sharp_detector.scan_all_games(games_data)
    
    return [
        SharpSignalResponse(
            game_id=s.game_id,
            home_team=s.home_team,
            away_team=s.away_team,
            signal_strength=s.signal_strength,
            reverse_line_movement=s.reverse_line_movement,
            steam_move=s.steam_move,
            smart_money_side=s.smart_money_side,
            public_side=s.public_side,
            line_movement=s.line_movement,
            velocity=s.velocity,
            confidence=s.confidence,
            alert_type=s.alert_type,
            reasoning=s.reasoning,
            recommendation=s.recommendation,
        )
        for s in signals
    ]


@router.get("/signals/today")
async def get_todays_signals():
    """
    Get today's sharp money signals.
    Combines live game analysis with sharp detection.
    """
    # Sample data (would come from live APIs)
    sample_games = [
        {
            "game_id": "bos_lal",
            "home_team": "Boston Celtics",
            "away_team": "Los Angeles Lakers",
            "opening_home_odds": 1.55,
            "current_home_odds": 1.62,
            "opening_away_odds": 2.45,
            "current_away_odds": 2.35,
            "bet_percent_home": 0.68,
            "money_percent_home": 0.52,
        },
        {
            "game_id": "mia_mil",
            "home_team": "Miami Heat",
            "away_team": "Milwaukee Bucks",
            "opening_home_odds": 2.10,
            "current_home_odds": 2.25,
            "opening_away_odds": 1.75,
            "current_away_odds": 1.68,
            "bet_percent_home": 0.42,
            "money_percent_home": 0.55,
        },
        {
            "game_id": "okc_dal",
            "home_team": "Oklahoma City Thunder", 
            "away_team": "Dallas Mavericks",
            "opening_home_odds": 1.65,
            "current_home_odds": 1.58,
            "opening_away_odds": 2.30,
            "current_away_odds": 2.42,
            "bet_percent_home": 0.55,
            "money_percent_home": 0.70,
        },
    ]
    
    signals = []
    for game in sample_games:
        sharp_detector.add_odds_snapshot(
            game["game_id"],
            OddsSnapshot(
                timestamp=datetime.now(),
                home_odds=game["current_home_odds"],
                away_odds=game["current_away_odds"],
            )
        )
        
        signal = sharp_detector.analyze(
            game_id=game["game_id"],
            home_team=game["home_team"],
            away_team=game["away_team"],
            opening_home_odds=game["opening_home_odds"],
            current_home_odds=game["current_home_odds"],
            opening_away_odds=game["opening_away_odds"],
            current_away_odds=game["current_away_odds"],
            distribution=BettingDistribution(
                bet_percent_home=game["bet_percent_home"],
                money_percent_home=game["money_percent_home"],
            ),
        )
        
        if signal.signal_strength > 0.3:
            signals.append({
                "game": f"{game['away_team']} @ {game['home_team']}",
                "signal_strength": signal.signal_strength,
                "alert_type": signal.alert_type,
                "smart_side": signal.smart_money_side,
                "public_side": signal.public_side,
                "recommendation": signal.recommendation,
                "confidence": signal.confidence,
            })
    
    return {
        "count": len(signals),
        "signals": sorted(signals, key=lambda x: x["signal_strength"], reverse=True),
    }
