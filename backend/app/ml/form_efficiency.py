"""
Form & Efficiency Module
========================
Tracks team momentum and offensive/defensive efficiency.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class GameResult:
    """Single game result."""
    opponent: str
    home: bool
    team_score: int
    opponent_score: int
    
    @property
    def win(self) -> bool:
        return self.team_score > self.opponent_score
    
    @property
    def margin(self) -> int:
        return self.team_score - self.opponent_score


class FormTracker:
    """
    Tracks recent form (last N games) for all teams.
    Form Score = (Wins*3 + Draws*1) / Max Points
    """
    
    def __init__(self, form_window: int = 5):
        self.form_window = form_window
        self.game_history: Dict[str, List[GameResult]] = {}
        
        # Initialize with estimated current form (can be updated with real data)
        self._initialize_estimated_form()
    
    def _initialize_estimated_form(self) -> None:
        """Initialize form estimates based on current standings."""
        # Strong form teams (4-5 wins in last 5)
        strong_form = [
            "Oklahoma City Thunder", "Cleveland Cavaliers", "Boston Celtics",
            "Denver Nuggets", "Houston Rockets"
        ]
        
        # Medium form teams (2-3 wins in last 5)
        medium_form = [
            "Dallas Mavericks", "Milwaukee Bucks", "Phoenix Suns",
            "Golden State Warriors", "LA Clippers", "Minnesota Timberwolves",
            "Miami Heat", "Philadelphia 76ers", "New York Knicks",
            "Sacramento Kings", "Los Angeles Lakers", "Indiana Pacers"
        ]
        
        # Weak form teams (0-2 wins in last 5)
        weak_form = [
            "Chicago Bulls", "Brooklyn Nets", "Charlotte Hornets",
            "Portland Trail Blazers", "San Antonio Spurs", "Utah Jazz",
            "Detroit Pistons", "Washington Wizards", "Toronto Raptors",
            "Atlanta Hawks", "Orlando Magic", "Memphis Grizzlies",
            "New Orleans Pelicans"
        ]
        
        # Create dummy game history based on form category
        for team in strong_form:
            self.game_history[team] = self._create_form_history(wins=4)
        
        for team in medium_form:
            self.game_history[team] = self._create_form_history(wins=3)
        
        for team in weak_form:
            self.game_history[team] = self._create_form_history(wins=1)
    
    def _create_form_history(self, wins: int) -> List[GameResult]:
        """Create dummy game history based on wins count."""
        results = []
        for i in range(self.form_window):
            is_win = i < wins
            results.append(GameResult(
                opponent="Unknown",
                home=i % 2 == 0,
                team_score=110 if is_win else 100,
                opponent_score=100 if is_win else 110
            ))
        return results
    
    def add_game(self, team: str, result: GameResult) -> None:
        """Add a new game result for a team."""
        if team not in self.game_history:
            self.game_history[team] = []
        
        self.game_history[team].append(result)
        
        # Keep only last N games
        if len(self.game_history[team]) > self.form_window:
            self.game_history[team] = self.game_history[team][-self.form_window:]
    
    def get_form_score(self, team: str) -> float:
        """
        Calculate form score (0-1 scale).
        Form Score = Wins / Total Games
        """
        if team not in self.game_history:
            return 0.5  # Default (neutral form)
        
        games = self.game_history[team]
        if not games:
            return 0.5
        
        wins = sum(1 for g in games if g.win)
        return wins / len(games)
    
    def get_weighted_form(self, team: str) -> float:
        """
        Weighted form (recent games matter more).
        More recent games get higher weight.
        """
        if team not in self.game_history:
            return 0.5
        
        games = self.game_history[team]
        if not games:
            return 0.5
        
        total_weight = 0
        weighted_score = 0
        
        for i, game in enumerate(games):
            weight = i + 1  # More recent = higher weight
            total_weight += weight
            if game.win:
                weighted_score += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.5
    
    def get_point_differential(self, team: str) -> float:
        """Average point differential in recent games."""
        if team not in self.game_history:
            return 0.0
        
        games = self.game_history[team]
        if not games:
            return 0.0
        
        total_margin = sum(g.margin for g in games)
        return total_margin / len(games)


class EfficiencyTracker:
    """
    Tracks offensive and defensive efficiency.
    Attack Strength = Team Goals Scored / League Avg
    Defense Strength = Team Goals Conceded / League Avg
    """
    
    # League averages (2024-25 season estimates)
    LEAGUE_AVG_POINTS_SCORED = 114.5
    LEAGUE_AVG_POINTS_ALLOWED = 114.5  # Same by definition
    
    # Team offensive/defensive ratings (estimated, can update with real data)
    TEAM_RATINGS = {
        # Format: (Offensive Rating, Defensive Rating)
        # Higher offensive = better, Lower defensive = better
        "Boston Celtics": (120.5, 108.5),
        "Oklahoma City Thunder": (118.5, 106.5),
        "Cleveland Cavaliers": (117.5, 107.5),
        "Denver Nuggets": (117.0, 110.5),
        "Dallas Mavericks": (116.5, 113.0),
        "Milwaukee Bucks": (116.0, 112.0),
        "Phoenix Suns": (115.5, 113.5),
        "Golden State Warriors": (115.0, 110.0),
        "Minnesota Timberwolves": (114.5, 108.0),
        "LA Clippers": (114.5, 111.0),
        "Miami Heat": (113.5, 111.5),
        "Philadelphia 76ers": (113.0, 112.0),
        "Indiana Pacers": (118.0, 115.0),
        "New York Knicks": (113.0, 109.5),
        "Los Angeles Lakers": (115.0, 113.0),
        "Sacramento Kings": (116.0, 115.0),
        "Houston Rockets": (110.5, 110.0),
        "New Orleans Pelicans": (112.0, 113.0),
        "Orlando Magic": (107.5, 109.5),
        "Memphis Grizzlies": (108.0, 112.0),
        "Toronto Raptors": (109.0, 117.0),
        "Atlanta Hawks": (114.5, 118.0),
        "Brooklyn Nets": (110.5, 118.0),
        "Chicago Bulls": (109.0, 117.0),
        "Portland Trail Blazers": (107.0, 118.5),
        "San Antonio Spurs": (107.5, 117.5),
        "Charlotte Hornets": (105.5, 119.0),
        "Utah Jazz": (108.0, 120.0),
        "Detroit Pistons": (107.0, 118.5),
        "Washington Wizards": (106.0, 122.0),
    }
    
    def get_offensive_rating(self, team: str) -> float:
        """Get team's offensive rating."""
        ratings = self.TEAM_RATINGS.get(team, (114.5, 114.5))
        return ratings[0]
    
    def get_defensive_rating(self, team: str) -> float:
        """Get team's defensive rating."""
        ratings = self.TEAM_RATINGS.get(team, (114.5, 114.5))
        return ratings[1]
    
    def get_attack_strength(self, team: str) -> float:
        """
        Attack strength relative to league average.
        > 1.0 = above average offense
        """
        return self.get_offensive_rating(team) / self.LEAGUE_AVG_POINTS_SCORED
    
    def get_defense_strength(self, team: str) -> float:
        """
        Defense strength relative to league average.
        < 1.0 = above average defense (allows fewer points)
        """
        return self.get_defensive_rating(team) / self.LEAGUE_AVG_POINTS_ALLOWED
    
    def get_matchup_score(self, team_a: str, team_b: str) -> float:
        """
        Calculate matchup advantage for team_a vs team_b.
        Matchup = Attack_A / Defense_B
        > 1.0 = team_a has offensive advantage
        """
        attack_a = self.get_attack_strength(team_a)
        defense_b = self.get_defense_strength(team_b)
        
        # Invert defense (higher is worse, so flip it)
        defense_factor = 2 - defense_b  # Transforms: 0.9 -> 1.1, 1.1 -> 0.9
        
        return attack_a * defense_factor
    
    def get_net_rating(self, team: str) -> float:
        """Net rating = Offensive - Defensive rating."""
        ratings = self.TEAM_RATINGS.get(team, (114.5, 114.5))
        return ratings[0] - ratings[1]
    
    def get_efficiency_score(self, team: str) -> float:
        """
        Combined efficiency score (0-1 scale).
        Based on net rating, normalized.
        """
        net = self.get_net_rating(team)
        
        # Net ratings typically range from -15 to +15
        # Normalize to 0-1 scale
        normalized = (net + 15) / 30
        return max(0, min(1, normalized))


# Singleton instances
_form_tracker: Optional[FormTracker] = None
_efficiency_tracker: Optional[EfficiencyTracker] = None


def get_form_tracker() -> FormTracker:
    """Get or create the global form tracker."""
    global _form_tracker
    if _form_tracker is None:
        _form_tracker = FormTracker()
    return _form_tracker


def get_efficiency_tracker() -> EfficiencyTracker:
    """Get or create the global efficiency tracker."""
    global _efficiency_tracker
    if _efficiency_tracker is None:
        _efficiency_tracker = EfficiencyTracker()
    return _efficiency_tracker


if __name__ == "__main__":
    # Test form tracker
    form = FormTracker()
    print("Team Form Scores (Last 5 Games):")
    print("-" * 40)
    
    teams = ["Boston Celtics", "Oklahoma City Thunder", "Chicago Bulls", "Washington Wizards"]
    for team in teams:
        score = form.get_form_score(team)
        weighted = form.get_weighted_form(team)
        print(f"{team}: {score:.2f} (weighted: {weighted:.2f})")
    
    # Test efficiency tracker
    print("\n" + "=" * 40)
    eff = EfficiencyTracker()
    print("Team Efficiency Ratings:")
    print("-" * 40)
    
    for team in teams:
        off = eff.get_offensive_rating(team)
        deff = eff.get_defensive_rating(team)
        net = eff.get_net_rating(team)
        print(f"{team}: Off={off:.1f}, Def={deff:.1f}, Net={net:+.1f}")
    
    print("\nMatchup Score (Celtics vs Lakers):")
    matchup = eff.get_matchup_score("Boston Celtics", "Los Angeles Lakers")
    print(f"Celtics attack vs Lakers defense: {matchup:.2f}")
