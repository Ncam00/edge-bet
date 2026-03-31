"""
Live Betting Model (LBM) - Real-time win probability and value detection.
Combines pre-game probability with live game state, momentum, and pace.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Literal
import math
from datetime import datetime


@dataclass
class GameState:
    """Current live game state."""
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: int  # 1-4 for NBA, 0 = not started, 5+ = overtime
    minutes_remaining: float  # in current quarter
    home_fouls: int = 0
    away_fouls: int = 0
    home_timeouts: int = 4
    away_timeouts: int = 4


@dataclass 
class MomentumData:
    """Recent momentum indicators."""
    home_last_3min_points: int = 0
    away_last_3min_points: int = 0
    home_last_5min_points: int = 0
    away_last_5min_points: int = 0
    possession: str = "unknown"  # "home", "away", "unknown"


@dataclass
class LivePrediction:
    """Live betting prediction output."""
    home_team: str
    away_team: str
    game_state: str  # "Q1 8:32" etc
    pre_game_prob: float  # Pre-game home win probability
    live_prob: float  # Current live probability
    momentum_score: float  # -1 to 1 (away to home)
    expected_final_home: float
    expected_final_away: float
    live_odds_home: float
    live_odds_away: float
    implied_home: float
    implied_away: float
    value_home: float
    value_away: float
    best_bet: Optional[str]  # "HOME", "AWAY", or None
    signal_type: Optional[str]  # "OVERREACTION", "COMEBACK", "MOMENTUM", etc
    confidence: str
    reasoning: str


class LiveBettingModel:
    """
    Live Betting Engine - Detects mispriced live odds.
    
    Core Signals:
    1. Overreaction: Market swings too far after a run
    2. Undervalued Comebacks: Strong team behind early
    3. Pace Mismatch: Game faster/slower than expected
    4. Momentum Shifts: Detect run continuations
    """
    
    # Quarter lengths (minutes)
    NBA_QUARTER_LENGTH = 12.0
    NBA_TOTAL_MINUTES = 48.0
    
    # Model weights
    WEIGHT_PREGAME = 0.40
    WEIGHT_SCORE = 0.30
    WEIGHT_MOMENTUM = 0.20
    WEIGHT_TIME = 0.10
    
    # Average points per minute (NBA)
    AVG_POINTS_PER_MINUTE = 2.4  # ~115 points per team per game
    
    # Betting thresholds
    MIN_VALUE = 0.08  # 8% edge for live (higher than pre-game due to variance)
    MIN_PROBABILITY = 0.52
    HIGH_VALUE = 0.15
    
    # Momentum thresholds
    MOMENTUM_RUN_THRESHOLD = 8  # 8+ point swing in 3 min = significant
    OVERREACTION_THRESHOLD = 0.15  # 15% odds swing = potential overreaction
    
    def __init__(self):
        self.avg_3min_points = 7.2  # Average points per team per 3 minutes
    
    def _calculate_time_remaining(self, quarter: int, minutes_in_quarter: float) -> float:
        """Calculate total minutes remaining in game."""
        if quarter == 0:
            return self.NBA_TOTAL_MINUTES
        if quarter > 4:  # Overtime
            return 5.0 - minutes_in_quarter + (5.0 * (quarter - 5))  # 5 min OT periods
        
        remaining_quarters = 4 - quarter
        return (remaining_quarters * self.NBA_QUARTER_LENGTH) + minutes_in_quarter
    
    def _calculate_momentum(self, momentum: MomentumData) -> float:
        """
        Calculate momentum score from -1 (strong away) to +1 (strong home).
        """
        home_3min = momentum.home_last_3min_points
        away_3min = momentum.away_last_3min_points
        
        diff = home_3min - away_3min
        normalized = diff / max(self.avg_3min_points, 1)
        
        # Clamp to [-1, 1]
        return max(-1, min(1, normalized / 2))
    
    def _calculate_expected_final_score(
        self,
        current_score: int,
        minutes_played: float,
        total_minutes: float = 48.0,
    ) -> float:
        """Project final score based on current pace."""
        if minutes_played == 0:
            return 114.5  # League average
        
        points_per_minute = current_score / minutes_played
        return points_per_minute * total_minutes
    
    def _score_impact(self, score_diff: int, time_remaining: float) -> float:
        """
        Calculate how much score difference matters given time remaining.
        Small leads late = big impact. Big leads early = small impact.
        
        Returns: Probability adjustment from -0.5 to +0.5
        """
        # Normalize score difference (20 points = max reasonable lead)
        normalized_diff = score_diff / 20.0
        
        # Time factor: more time = less impact
        time_factor = 1.0 - (time_remaining / self.NBA_TOTAL_MINUTES)
        time_factor = max(0.3, time_factor)  # Always some impact
        
        # Combine: bigger lead + less time = more impact
        impact = normalized_diff * time_factor
        
        # Clamp to reasonable range
        return max(-0.5, min(0.5, impact))
    
    def _detect_overreaction(
        self,
        pre_game_prob: float,
        current_implied: float,
        score_diff: int,
        time_remaining: float,
    ) -> bool:
        """Detect if market has overreacted to recent events."""
        expected_shift = abs(score_diff) * (1 - time_remaining / self.NBA_TOTAL_MINUTES) * 0.02
        actual_shift = abs(pre_game_prob - current_implied)
        
        return actual_shift > expected_shift + self.OVERREACTION_THRESHOLD
    
    def _detect_momentum_run(self, momentum: MomentumData) -> Optional[str]:
        """Detect if there's a significant scoring run."""
        diff_3min = momentum.home_last_3min_points - momentum.away_last_3min_points
        
        if diff_3min >= self.MOMENTUM_RUN_THRESHOLD:
            return "HOME_RUN"
        elif diff_3min <= -self.MOMENTUM_RUN_THRESHOLD:
            return "AWAY_RUN"
        return None
    
    def predict(
        self,
        game_state: GameState,
        pre_game_prob: float,
        momentum: Optional[MomentumData] = None,
        live_odds_home: float = 2.0,
        live_odds_away: float = 2.0,
    ) -> LivePrediction:
        """
        Generate live prediction with value analysis.
        
        Args:
            game_state: Current game state
            pre_game_prob: Pre-game home win probability (0-1)
            momentum: Optional momentum data
            live_odds_home: Current live odds for home team
            live_odds_away: Current live odds for away team
        
        Returns: LivePrediction
        """
        momentum = momentum or MomentumData()
        
        # Calculate time
        time_remaining = self._calculate_time_remaining(
            game_state.quarter, game_state.minutes_remaining
        )
        minutes_played = self.NBA_TOTAL_MINUTES - time_remaining
        
        # Calculate score impact
        score_diff = game_state.home_score - game_state.away_score
        score_impact = self._score_impact(score_diff, time_remaining)
        
        # Calculate momentum
        momentum_score = self._calculate_momentum(momentum)
        
        # Time factor (how much time matters)
        time_factor = time_remaining / self.NBA_TOTAL_MINUTES
        
        # Combine into live probability
        # Early game: weight pre-game more
        # Late game: weight current state more
        
        adjusted_pregame_weight = self.WEIGHT_PREGAME * (0.5 + time_factor * 0.5)
        adjusted_score_weight = self.WEIGHT_SCORE * (1.5 - time_factor * 0.5)
        
        live_prob = (
            pre_game_prob * adjusted_pregame_weight +
            (0.5 + score_impact) * adjusted_score_weight +
            (0.5 + momentum_score * 0.2) * self.WEIGHT_MOMENTUM +
            0.5 * self.WEIGHT_TIME  # Baseline
        )
        
        # Normalize
        live_prob = max(0.05, min(0.95, live_prob))
        
        # Calculate expected final scores
        expected_home = self._calculate_expected_final_score(
            game_state.home_score, minutes_played
        )
        expected_away = self._calculate_expected_final_score(
            game_state.away_score, minutes_played
        )
        
        # Calculate implied probabilities
        implied_home = 1 / live_odds_home if live_odds_home > 0 else 0.5
        implied_away = 1 / live_odds_away if live_odds_away > 0 else 0.5
        
        # Calculate value
        value_home = live_prob - implied_home
        value_away = (1 - live_prob) - implied_away
        
        # Detect signal type
        signal_type = None
        is_overreaction = self._detect_overreaction(
            pre_game_prob, implied_home, score_diff, time_remaining
        )
        momentum_run = self._detect_momentum_run(momentum)
        
        if is_overreaction:
            signal_type = "OVERREACTION"
        elif momentum_run:
            signal_type = f"MOMENTUM_{momentum_run}"
        elif abs(pre_game_prob - 0.5) > 0.15 and abs(live_prob - 0.5) < 0.1:
            signal_type = "COMEBACK"
        elif time_factor < 0.3 and abs(score_diff) < 6:
            signal_type = "CLUTCH"
        
        # Determine best bet
        best_bet = None
        confidence = "LOW"
        
        if value_home >= self.MIN_VALUE and live_prob >= self.MIN_PROBABILITY:
            best_bet = "HOME"
            if value_home >= self.HIGH_VALUE:
                confidence = "HIGH"
            else:
                confidence = "MEDIUM"
        elif value_away >= self.MIN_VALUE and (1 - live_prob) >= self.MIN_PROBABILITY:
            best_bet = "AWAY"
            if value_away >= self.HIGH_VALUE:
                confidence = "HIGH"
            else:
                confidence = "MEDIUM"
        
        # Game state string
        if game_state.quarter == 0:
            game_state_str = "Pre-game"
        elif game_state.quarter > 4:
            game_state_str = f"OT{game_state.quarter - 4} {game_state.minutes_remaining:.1f}"
        else:
            game_state_str = f"Q{game_state.quarter} {game_state.minutes_remaining:.1f}"
        
        # Build reasoning
        reasoning = (
            f"PreGame={pre_game_prob:.1%}, Live={live_prob:.1%}, "
            f"Score={game_state.home_score}-{game_state.away_score}, "
            f"Momentum={momentum_score:+.2f}"
        )
        
        return LivePrediction(
            home_team=game_state.home_team,
            away_team=game_state.away_team,
            game_state=game_state_str,
            pre_game_prob=round(pre_game_prob, 3),
            live_prob=round(live_prob, 3),
            momentum_score=round(momentum_score, 3),
            expected_final_home=round(expected_home, 1),
            expected_final_away=round(expected_away, 1),
            live_odds_home=live_odds_home,
            live_odds_away=live_odds_away,
            implied_home=round(implied_home, 3),
            implied_away=round(implied_away, 3),
            value_home=round(value_home, 3),
            value_away=round(value_away, 3),
            best_bet=best_bet,
            signal_type=signal_type,
            confidence=confidence,
            reasoning=reasoning,
        )


# Example usage
if __name__ == "__main__":
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
