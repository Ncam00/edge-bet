"""
Advanced Betting Model (PATSM)
==============================
Player-Adjusted Team Strength Model

Combines:
1. ELO ratings (core strength) - 50%
2. Recent form (momentum) - 20%
3. Efficiency matchup - 20%
4. Player/injury adjustments - 10%

+ Home court advantage boost
"""
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import json

from app.ml.elo_system import get_elo_system, get_win_probability
from app.ml.player_model import get_player_model, InjuryStatus
from app.ml.form_efficiency import get_form_tracker, get_efficiency_tracker


# Model weights
WEIGHT_ELO = 0.50
WEIGHT_FORM = 0.20
WEIGHT_EFFICIENCY = 0.20
WEIGHT_PLAYER = 0.10

# Home court advantage (NBA average ~60% home win rate historically)
HOME_BOOST = 0.08  # 8% boost to home team probability

# Value bet thresholds
MIN_VALUE_THRESHOLD = 0.05  # 5% edge minimum
MIN_PROBABILITY = 0.35      # Don't bet on very unlikely outcomes
MAX_PROBABILITY = 0.90      # Don't bet on heavy favorites (low EV)


@dataclass
class MatchPrediction:
    """Complete prediction for a matchup."""
    home_team: str
    away_team: str
    
    # Component probabilities (home team win)
    elo_probability: float
    form_score_home: float
    form_score_away: float
    efficiency_matchup: float
    player_adjustment: float
    
    # Final combined probability
    raw_probability: float
    final_probability: float  # After home boost
    
    # Betting info
    fair_odds: float
    
    def to_dict(self) -> Dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "elo_prob": round(self.elo_probability, 4),
            "form_home": round(self.form_score_home, 4),
            "form_away": round(self.form_score_away, 4),
            "efficiency": round(self.efficiency_matchup, 4),
            "player_adj": round(self.player_adjustment, 4),
            "raw_prob": round(self.raw_probability, 4),
            "final_prob": round(self.final_probability, 4),
            "fair_odds": round(self.fair_odds, 2),
        }


class AdvancedModel:
    """
    The main betting model combining all components.
    """
    
    def __init__(self):
        self.elo = get_elo_system()
        self.player_model = get_player_model()
        self.form = get_form_tracker()
        self.efficiency = get_efficiency_tracker()
    
    def set_injury(self, team: str, player: str, status: str) -> None:
        """Set injury status for a player."""
        status_enum = InjuryStatus(status.lower())
        self.player_model.set_injury(team, player, status_enum)
    
    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        """
        Generate full prediction for a matchup.
        
        Returns probability of HOME TEAM winning.
        """
        # 1. ELO probability (core)
        elo_prob = self.elo.expected_score(home_team, away_team)
        
        # 2. Form scores
        form_home = self.form.get_weighted_form(home_team)
        form_away = self.form.get_weighted_form(away_team)
        
        # Convert to home win probability contribution
        # If home form > away form, probability increases
        form_diff = form_home - form_away
        form_prob = 0.5 + (form_diff / 2)  # Scale to 0-1
        
        # 3. Efficiency matchup
        # Home team attack vs away defense, and vice versa
        home_matchup = self.efficiency.get_matchup_score(home_team, away_team)
        away_matchup = self.efficiency.get_matchup_score(away_team, home_team)
        
        # Normalize to probability
        matchup_ratio = home_matchup / (home_matchup + away_matchup)
        
        # 4. Player/injury adjustment
        home_strength = self.player_model.get_adjusted_strength(home_team)
        away_strength = self.player_model.get_adjusted_strength(away_team)
        
        # Convert to probability contribution
        strength_diff = home_strength - away_strength
        player_prob = 0.5 + (strength_diff * 0.5)  # Scale: ±0.3 strength = ±15% prob
        player_prob = max(0.1, min(0.9, player_prob))  # Clamp
        
        # 5. Combine all components
        raw_probability = (
            (elo_prob * WEIGHT_ELO) +
            (form_prob * WEIGHT_FORM) +
            (matchup_ratio * WEIGHT_EFFICIENCY) +
            (player_prob * WEIGHT_PLAYER)
        )
        
        # 6. Apply home court advantage
        final_probability = raw_probability + HOME_BOOST
        
        # Clamp between 0.05 and 0.95
        final_probability = max(0.05, min(0.95, final_probability))
        
        # 7. Calculate fair odds
        fair_odds = 1 / final_probability if final_probability > 0 else 999
        
        return MatchPrediction(
            home_team=home_team,
            away_team=away_team,
            elo_probability=elo_prob,
            form_score_home=form_home,
            form_score_away=form_away,
            efficiency_matchup=matchup_ratio,
            player_adjustment=player_prob,
            raw_probability=raw_probability,
            final_probability=final_probability,
            fair_odds=fair_odds,
        )
    
    def get_value_bet(
        self, 
        home_team: str, 
        away_team: str, 
        home_odds: float, 
        away_odds: float
    ) -> Dict:
        """
        Analyze a matchup for value betting opportunities.
        
        Returns value analysis for both sides.
        """
        prediction = self.predict_match(home_team, away_team)
        
        # Calculate implied probabilities from bookmaker odds
        home_implied = 1 / home_odds
        away_implied = 1 / away_odds
        
        # Calculate model probabilities for both sides
        home_model_prob = prediction.final_probability
        away_model_prob = 1 - prediction.final_probability
        
        # Calculate value (edge)
        home_value = home_model_prob - home_implied
        away_value = away_model_prob - away_implied
        
        # Calculate expected value
        home_ev = (home_model_prob * home_odds) - 1
        away_ev = (away_model_prob * away_odds) - 1
        
        # Determine best bet
        bets = []
        
        # Check home team value
        if home_value >= MIN_VALUE_THRESHOLD:
            if MIN_PROBABILITY <= home_model_prob <= MAX_PROBABILITY:
                bets.append({
                    "selection": home_team,
                    "side": "home",
                    "odds": home_odds,
                    "model_prob": round(home_model_prob, 4),
                    "implied_prob": round(home_implied, 4),
                    "value": round(home_value, 4),
                    "ev": round(home_ev, 4),
                    "confidence": self._get_confidence(home_value, home_model_prob),
                    "reasoning": prediction.to_dict()
                })
        
        # Check away team value
        if away_value >= MIN_VALUE_THRESHOLD:
            if MIN_PROBABILITY <= away_model_prob <= MAX_PROBABILITY:
                bets.append({
                    "selection": away_team,
                    "side": "away",
                    "odds": away_odds,
                    "model_prob": round(away_model_prob, 4),
                    "implied_prob": round(away_implied, 4),
                    "value": round(away_value, 4),
                    "ev": round(away_ev, 4),
                    "confidence": self._get_confidence(away_value, away_model_prob),
                    "reasoning": prediction.to_dict()
                })
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_odds": home_odds,
            "away_odds": away_odds,
            "prediction": prediction.to_dict(),
            "value_bets": sorted(bets, key=lambda x: x["ev"], reverse=True),
            "has_value": len(bets) > 0
        }
    
    def _get_confidence(self, value: float, probability: float) -> str:
        """
        Determine confidence level based on edge and probability.
        """
        # Strong value + good probability = high confidence
        if value >= 0.10 and probability >= 0.55:
            return "high"
        elif value >= 0.07 or (value >= 0.05 and probability >= 0.60):
            return "medium"
        else:
            return "low"
    
    def get_kelly_stake(
        self, 
        probability: float, 
        odds: float, 
        bankroll: float,
        kelly_fraction: float = 0.25  # Quarter Kelly for safety
    ) -> float:
        """
        Calculate optimal stake using Kelly Criterion.
        
        Kelly % = (bp - q) / b
        where:
          b = decimal odds - 1
          p = win probability
          q = 1 - p
        """
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly = (b * p - q) / b if b > 0 else 0
        
        # Apply fractional Kelly and clamp
        stake_percent = max(0, kelly * kelly_fraction)
        stake_percent = min(stake_percent, 0.10)  # Max 10% of bankroll
        
        return round(bankroll * stake_percent, 2)


# Singleton instance
_advanced_model: Optional[AdvancedModel] = None


def get_advanced_model() -> AdvancedModel:
    """Get or create the global advanced model."""
    global _advanced_model
    if _advanced_model is None:
        _advanced_model = AdvancedModel()
    return _advanced_model


if __name__ == "__main__":
    # Test the advanced model
    model = AdvancedModel()
    
    print("=" * 60)
    print("🏀 Advanced Betting Model Test")
    print("=" * 60)
    
    # Test match prediction
    print("\n📊 Celtics vs Lakers Prediction:")
    pred = model.predict_match("Boston Celtics", "Los Angeles Lakers")
    print(f"  ELO probability: {pred.elo_probability:.1%}")
    print(f"  Form (home/away): {pred.form_score_home:.2f} / {pred.form_score_away:.2f}")
    print(f"  Efficiency matchup: {pred.efficiency_matchup:.2f}")
    print(f"  Player adjustment: {pred.player_adjustment:.2f}")
    print(f"  Raw probability: {pred.raw_probability:.1%}")
    print(f"  Final probability: {pred.final_probability:.1%}")
    print(f"  Fair odds: {pred.fair_odds:.2f}")
    
    # Test with injury
    print("\n🤕 Adding injury: Jayson Tatum OUT")
    model.set_injury("Boston Celtics", "Jayson Tatum", "out")
    
    pred2 = model.predict_match("Boston Celtics", "Los Angeles Lakers")
    print(f"  Adjusted probability: {pred2.final_probability:.1%} (was {pred.final_probability:.1%})")
    
    # Test value bet
    print("\n💰 Value Bet Analysis:")
    print("  Odds: Celtics @ 1.65, Lakers @ 2.30")
    
    analysis = model.get_value_bet(
        "Boston Celtics", "Los Angeles Lakers",
        home_odds=1.65, away_odds=2.30
    )
    
    if analysis["value_bets"]:
        for bet in analysis["value_bets"]:
            print(f"\n  ✅ VALUE: {bet['selection']}")
            print(f"     Odds: {bet['odds']} | Model: {bet['model_prob']:.1%} | Implied: {bet['implied_prob']:.1%}")
            print(f"     Value: {bet['value']:.1%} | EV: {bet['ev']:.1%}")
            print(f"     Confidence: {bet['confidence']}")
            
            # Kelly stake
            stake = model.get_kelly_stake(bet['model_prob'], bet['odds'], 1000)
            print(f"     Kelly stake ($1000 bankroll): ${stake}")
    else:
        print("  No value bets found at these odds")
