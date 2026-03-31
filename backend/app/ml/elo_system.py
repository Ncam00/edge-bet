"""
ELO Rating System for NBA Teams
================================
Core backbone of the betting model.
Tracks team strength over time with match-by-match updates.
"""
import json
from typing import Dict, Optional
from pathlib import Path

# Starting ELO for all teams
DEFAULT_ELO = 1500
K_FACTOR = 20  # How quickly ratings change


# NBA Team mappings
NBA_TEAMS = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
}


class EloSystem:
    """
    Manages ELO ratings for all NBA teams.
    Persists to JSON for continuity across runs.
    """
    
    def __init__(self, ratings_file: str = "data/elo_ratings.json"):
        self.ratings_file = Path(ratings_file)
        self.ratings: Dict[str, float] = {}
        self.load_ratings()
    
    def load_ratings(self) -> None:
        """Load ratings from file or initialize defaults."""
        if self.ratings_file.exists():
            with open(self.ratings_file, "r") as f:
                self.ratings = json.load(f)
        else:
            # Initialize all teams with default ELO
            self.ratings = {team: DEFAULT_ELO for team in NBA_TEAMS.keys()}
            self.save_ratings()
    
    def save_ratings(self) -> None:
        """Persist ratings to JSON file."""
        self.ratings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ratings_file, "w") as f:
            json.dump(self.ratings, f, indent=2)
    
    def get_rating(self, team: str) -> float:
        """Get current ELO rating for a team."""
        return self.ratings.get(team, DEFAULT_ELO)
    
    def expected_score(self, team_a: str, team_b: str) -> float:
        """
        Calculate expected win probability for team_a vs team_b.
        
        Formula: P(A) = 1 / (1 + 10^((Eb - Ea) / 400))
        """
        elo_a = self.get_rating(team_a)
        elo_b = self.get_rating(team_b)
        
        exponent = (elo_b - elo_a) / 400
        return 1 / (1 + (10 ** exponent))
    
    def update_ratings(self, team_a: str, team_b: str, 
                       result: float, margin: Optional[int] = None) -> tuple:
        """
        Update ELO ratings after a match.
        
        Args:
            team_a: First team name
            team_b: Second team name
            result: 1.0 = team_a win, 0.0 = team_b win, 0.5 = draw
            margin: Point difference (optional, for margin-adjusted K)
        
        Returns:
            Tuple of (new_elo_a, new_elo_b)
        """
        expected_a = self.expected_score(team_a, team_b)
        expected_b = 1 - expected_a
        
        result_b = 1 - result
        
        # Optionally adjust K based on margin of victory
        k = K_FACTOR
        if margin is not None:
            # Bigger wins = larger rating adjustments
            k = K_FACTOR * (1 + (margin / 20))
            k = min(k, K_FACTOR * 2)  # Cap at 2x
        
        # Update ratings
        new_elo_a = self.ratings.get(team_a, DEFAULT_ELO) + k * (result - expected_a)
        new_elo_b = self.ratings.get(team_b, DEFAULT_ELO) + k * (result_b - expected_b)
        
        self.ratings[team_a] = new_elo_a
        self.ratings[team_b] = new_elo_b
        self.save_ratings()
        
        return (new_elo_a, new_elo_b)
    
    def get_top_teams(self, n: int = 10) -> list:
        """Get top N teams by ELO rating."""
        sorted_teams = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return sorted_teams[:n]
    
    def get_all_ratings(self) -> Dict[str, float]:
        """Get all current ratings."""
        return dict(sorted(self.ratings.items(), key=lambda x: x[1], reverse=True))


# Singleton instance
_elo_system: Optional[EloSystem] = None


def get_elo_system() -> EloSystem:
    """Get or create the global ELO system instance."""
    global _elo_system
    if _elo_system is None:
        _elo_system = EloSystem()
    return _elo_system


def get_win_probability(team_a: str, team_b: str) -> float:
    """Convenience function to get win probability."""
    return get_elo_system().expected_score(team_a, team_b)


if __name__ == "__main__":
    # Test the ELO system
    elo = EloSystem()
    
    print("NBA Team ELO Ratings (Initial):")
    print("-" * 40)
    for team, rating in elo.get_top_teams(10):
        print(f"{team}: {rating:.0f}")
    
    # Simulate a game
    print("\nSimulating: Celtics beat Lakers by 15")
    elo.update_ratings("Boston Celtics", "Los Angeles Lakers", 1.0, margin=15)
    
    print("\nUpdated Ratings:")
    print(f"Celtics: {elo.get_rating('Boston Celtics'):.0f}")
    print(f"Lakers: {elo.get_rating('Los Angeles Lakers'):.0f}")
    
    print(f"\nCeltics vs Lakers win prob: {elo.expected_score('Boston Celtics', 'Los Angeles Lakers'):.1%}")
