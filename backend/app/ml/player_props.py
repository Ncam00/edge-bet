"""
Player Props Model (PPM) - Points / Assists / Rebounds Predictions
Calculates expected stat lines and identifies value vs bookmaker lines.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Literal
from enum import Enum
import math

PropType = Literal["points", "rebounds", "assists", "threes", "pra"]


@dataclass
class PlayerStats:
    """Player statistical profile."""
    name: str
    team: str
    season_avg: float
    last_5_avg: float
    vs_opponent_avg: float  # vs this specific opponent
    avg_minutes: float
    expected_minutes: float
    usage_rate: float  # 0-1


@dataclass
class OpponentDefense:
    """Opponent defensive profile for a stat type."""
    team: str
    stat_allowed_per_game: float
    league_average: float
    pace: float
    league_avg_pace: float


@dataclass
class PropPrediction:
    """Player prop prediction output."""
    player: str
    team: str
    opponent: str
    prop_type: str
    projection: float
    std_dev: float
    line: float
    odds_over: float
    odds_under: float
    prob_over: float
    prob_under: float
    implied_over: float
    implied_under: float
    value_over: float
    value_under: float
    best_bet: Optional[str]  # "OVER", "UNDER", or None
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    reasoning: str


class PlayerPropsModel:
    """
    Player Props Engine - Predicts player stat lines and identifies value.
    
    Formula:
    1. Base = (Season * 0.5) + (Last5 * 0.3) + (VsOpp * 0.2)
    2. Minutes Adj = Base * (Expected Min / Avg Min)
    3. Usage Boost = 1 + (Missing Usage * 0.5)
    4. Defense Factor = Opp Allowed / League Avg
    5. Pace Factor = Game Pace / League Avg Pace
    6. Final = Base * All Adjustments
    7. Prob(Over) = 1 - CDF(line, mean=Final, std=0.25*Final)
    """
    
    # Weights for base projection
    WEIGHT_SEASON = 0.50
    WEIGHT_LAST5 = 0.30
    WEIGHT_MATCHUP = 0.20
    
    # Std dev as percentage of projection
    STD_DEV_FACTOR = 0.25
    
    # Value thresholds
    MIN_VALUE = 0.05        # 5% edge minimum
    MIN_PROBABILITY = 0.55  # 55% win probability minimum
    HIGH_VALUE = 0.12       # 12%+ = HIGH confidence
    
    # Example player database (would come from API in production)
    PLAYER_DATA: Dict[str, Dict[str, float]] = {
        # Lakers
        "LeBron James": {"team": "Los Angeles Lakers", "points": 25.2, "rebounds": 7.1, "assists": 8.3, "minutes": 35.2, "usage": 0.28},
        "Anthony Davis": {"team": "Los Angeles Lakers", "points": 24.8, "rebounds": 12.1, "assists": 3.2, "minutes": 35.8, "usage": 0.29},
        
        # Celtics
        "Jayson Tatum": {"team": "Boston Celtics", "points": 27.1, "rebounds": 8.4, "assists": 4.6, "minutes": 36.1, "usage": 0.30},
        "Jaylen Brown": {"team": "Boston Celtics", "points": 23.2, "rebounds": 5.8, "assists": 3.5, "minutes": 34.2, "usage": 0.26},
        
        # Nuggets  
        "Nikola Jokic": {"team": "Denver Nuggets", "points": 26.4, "rebounds": 12.3, "assists": 9.1, "minutes": 34.8, "usage": 0.30},
        "Jamal Murray": {"team": "Denver Nuggets", "points": 21.3, "rebounds": 4.0, "assists": 6.8, "minutes": 33.5, "usage": 0.24},
        
        # Bucks
        "Giannis Antetokounmpo": {"team": "Milwaukee Bucks", "points": 30.8, "rebounds": 11.5, "assists": 6.3, "minutes": 35.5, "usage": 0.35},
        "Damian Lillard": {"team": "Milwaukee Bucks", "points": 25.1, "rebounds": 4.2, "assists": 7.1, "minutes": 35.0, "usage": 0.28},
        
        # Thunder
        "Shai Gilgeous-Alexander": {"team": "Oklahoma City Thunder", "points": 31.5, "rebounds": 5.4, "assists": 6.2, "minutes": 34.0, "usage": 0.32},
        "Jalen Williams": {"team": "Oklahoma City Thunder", "points": 20.1, "rebounds": 5.3, "assists": 5.1, "minutes": 32.5, "usage": 0.22},
        
        # Cavaliers
        "Donovan Mitchell": {"team": "Cleveland Cavaliers", "points": 26.1, "rebounds": 4.7, "assists": 5.4, "minutes": 34.5, "usage": 0.29},
        "Evan Mobley": {"team": "Cleveland Cavaliers", "points": 18.2, "rebounds": 9.2, "assists": 3.1, "minutes": 33.0, "usage": 0.20},
        
        # Mavericks
        "Luka Doncic": {"team": "Dallas Mavericks", "points": 33.2, "rebounds": 9.1, "assists": 9.5, "minutes": 37.5, "usage": 0.36},
        "Kyrie Irving": {"team": "Dallas Mavericks", "points": 25.8, "rebounds": 4.8, "assists": 5.0, "minutes": 35.0, "usage": 0.27},
        
        # Suns
        "Kevin Durant": {"team": "Phoenix Suns", "points": 27.1, "rebounds": 6.5, "assists": 5.2, "minutes": 36.0, "usage": 0.29},
        "Devin Booker": {"team": "Phoenix Suns", "points": 27.0, "rebounds": 4.4, "assists": 6.8, "minutes": 35.5, "usage": 0.28},
        
        # Warriors
        "Stephen Curry": {"team": "Golden State Warriors", "points": 26.8, "rebounds": 4.5, "assists": 5.1, "minutes": 32.5, "usage": 0.29},
        "Draymond Green": {"team": "Golden State Warriors", "points": 8.5, "rebounds": 7.1, "assists": 6.0, "minutes": 28.0, "usage": 0.14},
        
        # Heat
        "Jimmy Butler": {"team": "Miami Heat", "points": 21.5, "rebounds": 5.8, "assists": 5.0, "minutes": 33.5, "usage": 0.26},
        "Bam Adebayo": {"team": "Miami Heat", "points": 19.2, "rebounds": 10.5, "assists": 3.8, "minutes": 34.0, "usage": 0.22},
        
        # Timberwolves
        "Anthony Edwards": {"team": "Minnesota Timberwolves", "points": 25.8, "rebounds": 5.3, "assists": 5.0, "minutes": 35.0, "usage": 0.29},
        "Karl-Anthony Towns": {"team": "Minnesota Timberwolves", "points": 21.5, "rebounds": 8.5, "assists": 3.0, "minutes": 33.0, "usage": 0.25},
    }
    
    # Team defensive ratings (points allowed per game adjusted)
    DEFENSE_RATINGS: Dict[str, Dict[str, float]] = {
        # Format: {stat_type: allowed_per_game}
        "Oklahoma City Thunder": {"points": 105.2, "rebounds": 42.1, "assists": 23.5, "pace": 99.5},
        "Cleveland Cavaliers": {"points": 106.8, "rebounds": 43.2, "assists": 24.1, "pace": 97.8},
        "Boston Celtics": {"points": 108.5, "rebounds": 42.8, "assists": 24.5, "pace": 100.2},
        "Denver Nuggets": {"points": 112.1, "rebounds": 44.5, "assists": 26.2, "pace": 101.5},
        "Houston Rockets": {"points": 109.8, "rebounds": 43.8, "assists": 24.8, "pace": 100.8},
        "Dallas Mavericks": {"points": 114.2, "rebounds": 45.1, "assists": 26.8, "pace": 102.5},
        "Minnesota Timberwolves": {"points": 107.5, "rebounds": 42.5, "assists": 23.8, "pace": 98.2},
        "Milwaukee Bucks": {"points": 113.5, "rebounds": 44.8, "assists": 25.5, "pace": 101.2},
        "Memphis Grizzlies": {"points": 111.2, "rebounds": 44.2, "assists": 25.2, "pace": 102.8},
        "LA Clippers": {"points": 110.5, "rebounds": 43.5, "assists": 24.8, "pace": 99.8},
        "Phoenix Suns": {"points": 114.8, "rebounds": 45.5, "assists": 26.5, "pace": 101.8},
        "Golden State Warriors": {"points": 113.2, "rebounds": 44.5, "assists": 26.2, "pace": 101.5},
        "Miami Heat": {"points": 108.2, "rebounds": 42.8, "assists": 23.8, "pace": 97.5},
        "Los Angeles Lakers": {"points": 112.8, "rebounds": 44.8, "assists": 26.0, "pace": 100.5},
        "Indiana Pacers": {"points": 118.5, "rebounds": 46.2, "assists": 28.5, "pace": 105.2},
        "Detroit Pistons": {"points": 115.2, "rebounds": 45.8, "assists": 27.2, "pace": 100.2},
        "Sacramento Kings": {"points": 116.8, "rebounds": 46.0, "assists": 27.8, "pace": 102.8},
        "New York Knicks": {"points": 109.5, "rebounds": 43.2, "assists": 24.2, "pace": 98.5},
        "Atlanta Hawks": {"points": 117.2, "rebounds": 46.5, "assists": 28.2, "pace": 102.5},
        "San Antonio Spurs": {"points": 116.2, "rebounds": 46.2, "assists": 27.5, "pace": 100.8},
        "Chicago Bulls": {"points": 114.5, "rebounds": 45.2, "assists": 26.8, "pace": 99.8},
        "Toronto Raptors": {"points": 118.2, "rebounds": 47.0, "assists": 28.8, "pace": 101.5},
        "Brooklyn Nets": {"points": 117.8, "rebounds": 46.8, "assists": 28.5, "pace": 100.5},
        "Portland Trail Blazers": {"points": 119.5, "rebounds": 47.5, "assists": 29.2, "pace": 102.2},
        "Orlando Magic": {"points": 108.8, "rebounds": 43.5, "assists": 24.5, "pace": 97.2},
        "Charlotte Hornets": {"points": 120.2, "rebounds": 48.0, "assists": 29.8, "pace": 103.5},
        "Utah Jazz": {"points": 119.8, "rebounds": 47.8, "assists": 29.5, "pace": 102.8},
        "New Orleans Pelicans": {"points": 115.5, "rebounds": 45.8, "assists": 27.2, "pace": 100.2},
        "Philadelphia 76ers": {"points": 116.5, "rebounds": 46.2, "assists": 27.8, "pace": 100.8},
        "Washington Wizards": {"points": 122.5, "rebounds": 48.5, "assists": 30.2, "pace": 104.5},
    }
    
    # League averages for normalization
    LEAGUE_AVG = {
        "points": 114.5,
        "rebounds": 45.0,
        "assists": 26.5,
        "pace": 100.5,
    }
    
    def __init__(self, missing_players: Optional[Dict[str, List[str]]] = None):
        """
        Initialize with optional missing players info.
        missing_players: {team: [player_names]} for usage boost calculation
        """
        self.missing_players = missing_players or {}
    
    def _cdf(self, x: float, mean: float, std: float) -> float:
        """Standard normal CDF approximation."""
        z = (x - mean) / std
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    def _calculate_missing_usage(self, team: str) -> float:
        """Calculate total usage of missing players."""
        missing = self.missing_players.get(team, [])
        total_usage = 0.0
        for player_name in missing:
            if player_name in self.PLAYER_DATA:
                total_usage += self.PLAYER_DATA[player_name].get("usage", 0)
        return total_usage
    
    def calculate_projection(
        self,
        player_name: str,
        opponent: str,
        prop_type: PropType,
        expected_minutes: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate projected stat for a player.
        
        Returns: Projected value or None if player not found
        """
        if player_name not in self.PLAYER_DATA:
            return None
        
        player = self.PLAYER_DATA[player_name]
        team = player["team"]
        
        # Get base stats
        season_avg = player.get(prop_type, 0)
        if season_avg == 0:
            return None
        
        # Simulate last 5 and vs opponent (would come from real data)
        # Using season avg with small variance for MVP
        last_5_avg = season_avg * 1.05  # Slightly hot
        vs_opponent_avg = season_avg * 0.98  # Slightly worse vs this opponent
        
        avg_minutes = player["minutes"]
        exp_min = expected_minutes or avg_minutes
        
        # Step 1: Base projection
        base = (
            season_avg * self.WEIGHT_SEASON +
            last_5_avg * self.WEIGHT_LAST5 +
            vs_opponent_avg * self.WEIGHT_MATCHUP
        )
        
        # Step 2: Minutes adjustment
        minutes_adj = base * (exp_min / avg_minutes)
        
        # Step 3: Usage boost from missing players
        missing_usage = self._calculate_missing_usage(team)
        usage_boost = 1 + (missing_usage * 0.5)
        boosted = minutes_adj * usage_boost
        
        # Step 4: Defense factor
        opp_defense = self.DEFENSE_RATINGS.get(opponent, {})
        opp_allowed = opp_defense.get(prop_type, self.LEAGUE_AVG[prop_type])
        defense_factor = opp_allowed / self.LEAGUE_AVG[prop_type]
        defense_adj = boosted * defense_factor
        
        # Step 5: Pace factor
        opp_pace = opp_defense.get("pace", self.LEAGUE_AVG["pace"])
        pace_factor = opp_pace / self.LEAGUE_AVG["pace"]
        final = defense_adj * pace_factor
        
        return round(final, 1)
    
    def predict_prop(
        self,
        player_name: str,
        opponent: str,
        prop_type: PropType,
        line: float,
        odds_over: float,
        odds_under: float,
        expected_minutes: Optional[float] = None,
    ) -> Optional[PropPrediction]:
        """
        Generate full prop prediction with value analysis.
        
        Returns: PropPrediction or None if player not found
        """
        projection = self.calculate_projection(
            player_name, opponent, prop_type, expected_minutes
        )
        if projection is None:
            return None
        
        player = self.PLAYER_DATA[player_name]
        team = player["team"]
        
        # Calculate standard deviation
        std_dev = projection * self.STD_DEV_FACTOR
        
        # Calculate probabilities
        prob_under = self._cdf(line, projection, std_dev)
        prob_over = 1 - prob_under
        
        # Calculate implied probabilities
        implied_over = 1 / odds_over if odds_over > 0 else 0
        implied_under = 1 / odds_under if odds_under > 0 else 0
        
        # Calculate value
        value_over = prob_over - implied_over
        value_under = prob_under - implied_under
        
        # Determine best bet
        best_bet = None
        confidence = "LOW"
        
        if value_over >= self.MIN_VALUE and prob_over >= self.MIN_PROBABILITY:
            best_bet = "OVER"
            if value_over >= self.HIGH_VALUE:
                confidence = "HIGH"
            else:
                confidence = "MEDIUM"
        elif value_under >= self.MIN_VALUE and prob_under >= self.MIN_PROBABILITY:
            best_bet = "UNDER"
            if value_under >= self.HIGH_VALUE:
                confidence = "HIGH"
            else:
                confidence = "MEDIUM"
        
        # Build reasoning
        opp_defense = self.DEFENSE_RATINGS.get(opponent, {})
        opp_allowed = opp_defense.get(prop_type, self.LEAGUE_AVG[prop_type])
        defense_factor = opp_allowed / self.LEAGUE_AVG[prop_type]
        opp_pace = opp_defense.get("pace", self.LEAGUE_AVG["pace"])
        
        reasoning = (
            f"Proj={projection:.1f}, Line={line}, "
            f"DefFactor={defense_factor:.2f}, Pace={opp_pace:.1f}"
        )
        
        return PropPrediction(
            player=player_name,
            team=team,
            opponent=opponent,
            prop_type=prop_type,
            projection=projection,
            std_dev=round(std_dev, 2),
            line=line,
            odds_over=odds_over,
            odds_under=odds_under,
            prob_over=round(prob_over, 3),
            prob_under=round(prob_under, 3),
            implied_over=round(implied_over, 3),
            implied_under=round(implied_under, 3),
            value_over=round(value_over, 3),
            value_under=round(value_under, 3),
            best_bet=best_bet,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def scan_all_props(
        self,
        props_data: List[Dict],
    ) -> List[PropPrediction]:
        """
        Scan a list of props for value bets.
        
        props_data: List of dicts with keys:
            - player, opponent, prop_type, line, odds_over, odds_under
        
        Returns: List of PropPredictions with value, sorted by value
        """
        results = []
        
        for prop in props_data:
            prediction = self.predict_prop(
                player_name=prop["player"],
                opponent=prop["opponent"],
                prop_type=prop["prop_type"],
                line=prop["line"],
                odds_over=prop.get("odds_over", 1.90),
                odds_under=prop.get("odds_under", 1.90),
                expected_minutes=prop.get("expected_minutes"),
            )
            
            if prediction and prediction.best_bet:
                results.append(prediction)
        
        # Sort by best value
        results.sort(
            key=lambda p: max(p.value_over, p.value_under),
            reverse=True
        )
        
        return results


# Example usage
if __name__ == "__main__":
    model = PlayerPropsModel(
        missing_players={
            "Milwaukee Bucks": ["Khris Middleton"],  # OUT
            "Phoenix Suns": ["Bradley Beal"],  # DOUBTFUL
        }
    )
    
    # Test single prediction
    pred = model.predict_prop(
        player_name="Giannis Antetokounmpo",
        opponent="Miami Heat",
        prop_type="points",
        line=28.5,
        odds_over=1.87,
        odds_under=1.93,
    )
    
    if pred:
        print(f"\n🏀 {pred.player} ({pred.team}) @ {pred.opponent}")
        print(f"   Prop: {pred.prop_type.upper()} {pred.line}")
        print(f"   Projection: {pred.projection} (±{pred.std_dev})")
        print(f"   OVER: {pred.prob_over:.1%} vs {pred.implied_over:.1%} = {pred.value_over:+.1%}")
        print(f"   UNDER: {pred.prob_under:.1%} vs {pred.implied_under:.1%} = {pred.value_under:+.1%}")
        if pred.best_bet:
            print(f"   🎯 BET: {pred.best_bet} ({pred.confidence})")
