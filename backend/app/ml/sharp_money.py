"""
Sharp Money Detection Engine (SMDE) - Detects professional bettor activity.
Identifies when odds move in ways suggesting sharp action.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math


@dataclass
class OddsSnapshot:
    """A point-in-time odds reading."""
    timestamp: datetime
    home_odds: float
    away_odds: float
    over_odds: Optional[float] = None
    under_odds: Optional[float] = None
    total_line: Optional[float] = None


@dataclass
class BettingDistribution:
    """Public betting percentages."""
    bet_percent_home: float  # % of bets on home
    money_percent_home: float  # % of money on home
    bet_percent_over: float = 0.5
    money_percent_over: float = 0.5


@dataclass
class SharpSignal:
    """Sharp money detection output."""
    game_id: str
    home_team: str
    away_team: str
    signal_strength: float  # 0-1 composite score
    reverse_line_movement: bool
    steam_move: bool
    smart_money_side: Optional[str]  # "HOME", "AWAY", "OVER", "UNDER"
    public_side: str  # Where public is betting
    line_movement: float  # % change in odds
    velocity: float  # Movement speed
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    alert_type: str  # "SHARP", "STEAM", "RLM", "CONTRARIAN"
    reasoning: str
    recommendation: str


class SharpMoneyDetector:
    """
    Sharp Money Detection Engine.
    
    Core Signals:
    1. Reverse Line Movement (RLM): Odds move against public betting
    2. Steam Moves: Rapid odds movement across books
    3. Bet vs Money Mismatch: Large bets from few bettors
    4. Line Movement Velocity: Speed of odds changes
    """
    
    # Thresholds
    RLM_BET_THRESHOLD = 0.60  # 60%+ public bets
    STEAM_MOVE_THRESHOLD = 0.05  # 5% odds change = steam
    MONEY_MISMATCH_THRESHOLD = 0.15  # 15% gap between bet% and money%
    HIGH_VELOCITY_THRESHOLD = 0.03  # 3% move per hour
    
    # Signal weights
    WEIGHT_RLM = 0.40
    WEIGHT_MONEY_MISMATCH = 0.30
    WEIGHT_VELOCITY = 0.20
    WEIGHT_STEAM = 0.10
    
    # Confidence thresholds
    HIGH_SIGNAL = 0.70
    MEDIUM_SIGNAL = 0.50
    
    def __init__(self):
        self.odds_history: Dict[str, List[OddsSnapshot]] = {}
    
    def add_odds_snapshot(self, game_id: str, snapshot: OddsSnapshot):
        """Track odds over time for a game."""
        if game_id not in self.odds_history:
            self.odds_history[game_id] = []
        self.odds_history[game_id].append(snapshot)
    
    def _calculate_line_movement(
        self,
        opening_odds: float,
        current_odds: float,
    ) -> float:
        """Calculate percentage change in odds."""
        if opening_odds == 0:
            return 0
        return (current_odds - opening_odds) / opening_odds
    
    def _detect_reverse_line_movement(
        self,
        bet_percent: float,
        opening_odds: float,
        current_odds: float,
    ) -> Tuple[bool, str]:
        """
        Detect if line moved against public betting.
        
        Returns: (is_rlm, faded_side)
        """
        movement = self._calculate_line_movement(opening_odds, current_odds)
        
        # Heavy betting on one side, but odds got worse for that side
        if bet_percent >= self.RLM_BET_THRESHOLD and movement > 0:
            # Public betting this side, odds drifted higher (worse)
            return True, "AWAY"  # Sharps on opposite side
        elif bet_percent <= (1 - self.RLM_BET_THRESHOLD) and movement < 0:
            # Public on other side, this side got shorter
            return True, "HOME"
        
        return False, ""
    
    def _detect_steam_move(
        self,
        game_id: str,
        current_home_odds: float,
    ) -> bool:
        """Detect rapid odds movement (steam move)."""
        history = self.odds_history.get(game_id, [])
        if len(history) < 2:
            return False
        
        opening = history[0].home_odds
        movement = abs(self._calculate_line_movement(opening, current_home_odds))
        
        return movement >= self.STEAM_MOVE_THRESHOLD
    
    def _calculate_velocity(
        self,
        game_id: str,
        current_odds: float,
    ) -> float:
        """Calculate how fast odds are moving."""
        history = self.odds_history.get(game_id, [])
        if len(history) < 2:
            return 0
        
        # Use last hour of movement
        recent = history[-1]
        oldest = history[0]
        
        time_diff = (recent.timestamp - oldest.timestamp).total_seconds() / 3600
        if time_diff == 0:
            return 0
        
        odds_change = abs(recent.home_odds - oldest.home_odds) / oldest.home_odds
        return odds_change / time_diff
    
    def _calculate_money_mismatch(
        self,
        bet_percent: float,
        money_percent: float,
    ) -> float:
        """Calculate gap between bet count and money volume."""
        return money_percent - bet_percent
    
    def analyze(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        opening_home_odds: float,
        current_home_odds: float,
        opening_away_odds: float,
        current_away_odds: float,
        distribution: Optional[BettingDistribution] = None,
    ) -> SharpSignal:
        """
        Analyze a game for sharp money signals.
        
        Args:
            game_id: Unique game identifier
            home_team, away_team: Team names
            opening_*_odds: Opening odds
            current_*_odds: Current odds
            distribution: Betting distribution data (if available)
        
        Returns: SharpSignal
        """
        distribution = distribution or BettingDistribution(
            bet_percent_home=0.50,
            money_percent_home=0.50,
        )
        
        # Calculate movement
        home_movement = self._calculate_line_movement(
            opening_home_odds, current_home_odds
        )
        away_movement = self._calculate_line_movement(
            opening_away_odds, current_away_odds
        )
        
        # Detect signals
        is_rlm, rlm_side = self._detect_reverse_line_movement(
            distribution.bet_percent_home,
            opening_home_odds,
            current_home_odds,
        )
        
        is_steam = self._detect_steam_move(game_id, current_home_odds)
        velocity = self._calculate_velocity(game_id, current_home_odds)
        money_mismatch = self._calculate_money_mismatch(
            distribution.bet_percent_home,
            distribution.money_percent_home,
        )
        
        # Calculate composite score
        rlm_score = 1.0 if is_rlm else 0.0
        steam_score = 1.0 if is_steam else 0.0
        velocity_score = min(1.0, velocity / self.HIGH_VELOCITY_THRESHOLD)
        mismatch_score = min(1.0, abs(money_mismatch) / self.MONEY_MISMATCH_THRESHOLD)
        
        signal_strength = (
            rlm_score * self.WEIGHT_RLM +
            mismatch_score * self.WEIGHT_MONEY_MISMATCH +
            velocity_score * self.WEIGHT_VELOCITY +
            steam_score * self.WEIGHT_STEAM
        )
        
        # Determine sharp money side
        smart_money_side = None
        if is_rlm:
            smart_money_side = rlm_side
        elif money_mismatch > self.MONEY_MISMATCH_THRESHOLD:
            smart_money_side = "HOME"
        elif money_mismatch < -self.MONEY_MISMATCH_THRESHOLD:
            smart_money_side = "AWAY"
        elif home_movement < -0.03:  # Home odds shortened
            smart_money_side = "HOME"
        elif away_movement < -0.03:  # Away odds shortened
            smart_money_side = "AWAY"
        
        # Determine public side
        if distribution.bet_percent_home > 0.55:
            public_side = "HOME"
        elif distribution.bet_percent_home < 0.45:
            public_side = "AWAY"
        else:
            public_side = "SPLIT"
        
        # Determine confidence
        if signal_strength >= self.HIGH_SIGNAL:
            confidence = "HIGH"
        elif signal_strength >= self.MEDIUM_SIGNAL:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # Determine alert type
        if is_rlm and is_steam:
            alert_type = "SHARP + STEAM"
        elif is_rlm:
            alert_type = "RLM"
        elif is_steam:
            alert_type = "STEAM"
        elif abs(money_mismatch) > self.MONEY_MISMATCH_THRESHOLD:
            alert_type = "MONEY_MISMATCH"
        elif signal_strength > 0:
            alert_type = "CONTRARIAN"
        else:
            alert_type = "NONE"
        
        # Build reasoning
        reasoning_parts = []
        if is_rlm:
            reasoning_parts.append(f"RLM detected (public {distribution.bet_percent_home:.0%} on home)")
        if is_steam:
            reasoning_parts.append(f"Steam move ({abs(home_movement):.1%} shift)")
        if abs(money_mismatch) > 0.1:
            reasoning_parts.append(f"Money mismatch ({money_mismatch:+.0%})")
        if velocity > 0.01:
            reasoning_parts.append(f"High velocity ({velocity:.2%}/hr)")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No significant signals"
        
        # Recommendation
        if signal_strength >= self.HIGH_SIGNAL and smart_money_side:
            recommendation = f"🔥 FOLLOW SHARPS: {smart_money_side}"
        elif signal_strength >= self.MEDIUM_SIGNAL and smart_money_side:
            recommendation = f"⚠️ SHARP ACTIVITY: Consider {smart_money_side}"
        elif signal_strength < 0.3 and public_side != "SPLIT":
            recommendation = f"📉 Heavy public on {public_side} - no sharp resistance"
        else:
            recommendation = "👀 Monitor - no clear signal"
        
        return SharpSignal(
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            signal_strength=round(signal_strength, 3),
            reverse_line_movement=is_rlm,
            steam_move=is_steam,
            smart_money_side=smart_money_side,
            public_side=public_side,
            line_movement=round(home_movement, 4),
            velocity=round(velocity, 4),
            confidence=confidence,
            alert_type=alert_type,
            reasoning=reasoning,
            recommendation=recommendation,
        )
    
    def scan_all_games(
        self,
        games: List[Dict],
    ) -> List[SharpSignal]:
        """
        Scan multiple games for sharp signals.
        
        games: List of dicts with fields matching analyze() args
        
        Returns: List of SharpSignals, filtered to meaningful signals
        """
        signals = []
        
        for game in games:
            signal = self.analyze(
                game_id=game.get("game_id", ""),
                home_team=game.get("home_team", ""),
                away_team=game.get("away_team", ""),
                opening_home_odds=game.get("opening_home_odds", 2.0),
                current_home_odds=game.get("current_home_odds", 2.0),
                opening_away_odds=game.get("opening_away_odds", 2.0),
                current_away_odds=game.get("current_away_odds", 2.0),
                distribution=game.get("distribution"),
            )
            
            # Only include medium+ signals
            if signal.signal_strength >= self.MEDIUM_SIGNAL:
                signals.append(signal)
        
        # Sort by signal strength
        signals.sort(key=lambda s: s.signal_strength, reverse=True)
        
        return signals


# Example usage
if __name__ == "__main__":
    detector = SharpMoneyDetector()
    
    # Add historical odds
    from datetime import timedelta
    now = datetime.now()
    
    detector.add_odds_snapshot("lal_bos", OddsSnapshot(
        timestamp=now - timedelta(hours=6),
        home_odds=1.85,
        away_odds=2.05,
    ))
    detector.add_odds_snapshot("lal_bos", OddsSnapshot(
        timestamp=now,
        home_odds=1.95,
        away_odds=1.95,
    ))
    
    # Analyze with betting distribution
    signal = detector.analyze(
        game_id="lal_bos",
        home_team="Boston Celtics",
        away_team="Los Angeles Lakers",
        opening_home_odds=1.85,
        current_home_odds=1.95,
        opening_away_odds=2.05,
        current_away_odds=1.95,
        distribution=BettingDistribution(
            bet_percent_home=0.72,  # 72% public on home
            money_percent_home=0.55,  # But only 55% of money
        ),
    )
    
    print(f"\n🔍 {signal.away_team} @ {signal.home_team}")
    print(f"   Signal Strength: {signal.signal_strength:.1%}")
    print(f"   Alert Type: {signal.alert_type}")
    print(f"   RLM: {'✅' if signal.reverse_line_movement else '❌'}")
    print(f"   Steam: {'✅' if signal.steam_move else '❌'}")
    print(f"   Public: {signal.public_side}")
    print(f"   Sharp Side: {signal.smart_money_side or 'Unknown'}")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Reasoning: {signal.reasoning}")
    print(f"   📌 {signal.recommendation}")
