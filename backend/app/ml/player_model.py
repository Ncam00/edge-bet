"""
Player Impact Model
====================
Calculate player contributions and adjust team strength based on:
- Individual player ratings
- Minutes played
- Injury status
- Star player impact
"""
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class InjuryStatus(str, Enum):
    ACTIVE = "active"
    QUESTIONABLE = "questionable"
    DOUBTFUL = "doubtful"
    OUT = "out"
    SUSPENDED = "suspended"


@dataclass
class PlayerStats:
    """Player performance statistics."""
    name: str
    team: str
    points_per_game: float
    assists_per_game: float
    rebounds_per_game: float
    steals_per_game: float
    blocks_per_game: float
    minutes_per_game: float
    plus_minus: float = 0.0
    injury_status: InjuryStatus = InjuryStatus.ACTIVE
    
    @property
    def performance_rating(self) -> float:
        """
        Calculate Performance Rating (PR)
        PR = (Points * 0.4) + (Assists * 0.2) + (Rebounds * 0.2) + (Defensive * 0.2)
        """
        defensive = (self.steals_per_game * 2) + (self.blocks_per_game * 2)
        
        pr = (
            (self.points_per_game * 0.4) +
            (self.assists_per_game * 0.2) +
            (self.rebounds_per_game * 0.2) +
            (defensive * 0.2)
        )
        return pr
    
    @property
    def weighted_impact(self) -> float:
        """
        Minutes-weighted impact score.
        Weighted Impact = PR * (Minutes / 36)
        """
        return self.performance_rating * (self.minutes_per_game / 36)
    
    @property
    def adjusted_impact(self) -> float:
        """
        Impact adjusted for injury status.
        """
        impact = self.weighted_impact
        
        if self.injury_status == InjuryStatus.OUT:
            return 0.0
        elif self.injury_status == InjuryStatus.DOUBTFUL:
            return impact * 0.25
        elif self.injury_status == InjuryStatus.QUESTIONABLE:
            return impact * 0.5
        elif self.injury_status == InjuryStatus.SUSPENDED:
            return 0.0
        
        return impact


class PlayerImpactModel:
    """
    Calculates team strength adjustments based on player availability.
    """
    
    # Star players (top 20% impact) - simplified list for MVP
    STAR_PLAYERS = {
        "Boston Celtics": ["Jayson Tatum", "Jaylen Brown", "Derrick White"],
        "Denver Nuggets": ["Nikola Jokic", "Jamal Murray", "Michael Porter Jr."],
        "Milwaukee Bucks": ["Giannis Antetokounmpo", "Damian Lillard", "Khris Middleton"],
        "Philadelphia 76ers": ["Joel Embiid", "Tyrese Maxey", "Paul George"],
        "Phoenix Suns": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
        "LA Clippers": ["Kawhi Leonard", "James Harden", "Paul George"],
        "Los Angeles Lakers": ["LeBron James", "Anthony Davis", "Austin Reaves"],
        "Golden State Warriors": ["Stephen Curry", "Draymond Green", "Andrew Wiggins"],
        "Dallas Mavericks": ["Luka Doncic", "Kyrie Irving", "PJ Washington"],
        "Miami Heat": ["Jimmy Butler", "Bam Adebayo", "Tyler Herro"],
        "Cleveland Cavaliers": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
        "Oklahoma City Thunder": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
        "Minnesota Timberwolves": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
        "New York Knicks": ["Jalen Brunson", "Julius Randle", "OG Anunoby"],
        "Sacramento Kings": ["De'Aaron Fox", "Domantas Sabonis", "Keegan Murray"],
    }
    
    # Base team strength (normalized, 1.0 = league average)
    BASE_TEAM_STRENGTH = {
        "Boston Celtics": 1.15, "Denver Nuggets": 1.12, "Oklahoma City Thunder": 1.14,
        "Cleveland Cavaliers": 1.10, "Milwaukee Bucks": 1.08, "Phoenix Suns": 1.06,
        "Dallas Mavericks": 1.05, "Minnesota Timberwolves": 1.05, "Golden State Warriors": 1.03,
        "Miami Heat": 1.02, "Philadelphia 76ers": 1.02, "LA Clippers": 1.02,
        "Los Angeles Lakers": 1.00, "Indiana Pacers": 1.00, "New York Knicks": 1.02,
        "Sacramento Kings": 0.98, "New Orleans Pelicans": 0.97, "Houston Rockets": 0.96,
        "Orlando Magic": 0.95, "Toronto Raptors": 0.93, "Memphis Grizzlies": 0.92,
        "Brooklyn Nets": 0.90, "Atlanta Hawks": 0.90, "Chicago Bulls": 0.88,
        "Portland Trail Blazers": 0.85, "San Antonio Spurs": 0.82, "Charlotte Hornets": 0.80,
        "Utah Jazz": 0.78, "Detroit Pistons": 0.75, "Washington Wizards": 0.72,
    }
    
    # Star player impact value (0-1 scale)
    STAR_IMPACT = 0.08  # 8% team strength per star player
    
    def __init__(self):
        self.injury_cache: Dict[str, Dict[str, InjuryStatus]] = {}
    
    def get_base_strength(self, team: str) -> float:
        """Get base team strength (1.0 = league average)."""
        return self.BASE_TEAM_STRENGTH.get(team, 1.0)
    
    def get_star_players(self, team: str) -> List[str]:
        """Get list of star players for a team."""
        return self.STAR_PLAYERS.get(team, [])
    
    def set_injury(self, team: str, player: str, status: InjuryStatus) -> None:
        """Set injury status for a player."""
        if team not in self.injury_cache:
            self.injury_cache[team] = {}
        self.injury_cache[team][player] = status
    
    def get_injury_status(self, team: str, player: str) -> InjuryStatus:
        """Get injury status for a player."""
        if team in self.injury_cache and player in self.injury_cache[team]:
            return self.injury_cache[team][player]
        return InjuryStatus.ACTIVE
    
    def calculate_injury_adjustment(self, team: str) -> float:
        """
        Calculate team strength adjustment based on injuries.
        
        Returns:
            Adjustment factor (negative = weaker due to injuries)
        """
        if team not in self.injury_cache:
            return 0.0
        
        adjustment = 0.0
        star_players = self.get_star_players(team)
        
        for player, status in self.injury_cache[team].items():
            is_star = player in star_players
            
            if status == InjuryStatus.OUT or status == InjuryStatus.SUSPENDED:
                # Full penalty
                penalty = self.STAR_IMPACT if is_star else self.STAR_IMPACT * 0.3
                adjustment -= penalty
                
            elif status == InjuryStatus.DOUBTFUL:
                # 75% penalty
                penalty = self.STAR_IMPACT * 0.75 if is_star else self.STAR_IMPACT * 0.2
                adjustment -= penalty
                
            elif status == InjuryStatus.QUESTIONABLE:
                # 50% penalty
                penalty = self.STAR_IMPACT * 0.5 if is_star else self.STAR_IMPACT * 0.15
                adjustment -= penalty
        
        return adjustment
    
    def get_adjusted_strength(self, team: str) -> float:
        """
        Get team strength adjusted for injuries.
        
        Returns:
            Adjusted strength factor (1.0 = league average)
        """
        base = self.get_base_strength(team)
        injury_adj = self.calculate_injury_adjustment(team)
        
        adjusted = base + injury_adj
        
        # Clamp between 0.5 and 1.5
        return max(0.5, min(1.5, adjusted))
    
    def get_matchup_strength_diff(self, home_team: str, away_team: str) -> float:
        """
        Get strength differential between two teams.
        Positive = home team stronger, Negative = away team stronger.
        """
        home_strength = self.get_adjusted_strength(home_team)
        away_strength = self.get_adjusted_strength(away_team)
        
        return home_strength - away_strength


async def fetch_nba_injuries() -> Dict[str, Dict[str, InjuryStatus]]:
    """
    Fetch current NBA injury report.
    Returns dict: {team: {player: status}}
    
    Note: In production, use official NBA API or balldontlie.io
    """
    # For MVP, return sample injury data
    # In production, integrate with real injury API
    return {
        "Philadelphia 76ers": {
            "Joel Embiid": InjuryStatus.QUESTIONABLE,
        },
        "Milwaukee Bucks": {
            "Khris Middleton": InjuryStatus.OUT,
        },
        "Phoenix Suns": {
            "Bradley Beal": InjuryStatus.DOUBTFUL,
        },
        "LA Clippers": {
            "Kawhi Leonard": InjuryStatus.QUESTIONABLE,
        },
    }


# Singleton instance
_player_model: Optional[PlayerImpactModel] = None


def get_player_model() -> PlayerImpactModel:
    """Get or create the global player impact model."""
    global _player_model
    if _player_model is None:
        _player_model = PlayerImpactModel()
    return _player_model


if __name__ == "__main__":
    # Test player impact model
    model = PlayerImpactModel()
    
    print("Base Team Strengths (Top 10):")
    print("-" * 40)
    sorted_teams = sorted(model.BASE_TEAM_STRENGTH.items(), key=lambda x: x[1], reverse=True)
    for team, strength in sorted_teams[:10]:
        print(f"{team}: {strength:.2f}")
    
    # Test injury adjustment
    print("\nTesting Injury Adjustment:")
    model.set_injury("Boston Celtics", "Jayson Tatum", InjuryStatus.OUT)
    
    print(f"Celtics base: {model.get_base_strength('Boston Celtics'):.2f}")
    print(f"Celtics adjusted: {model.get_adjusted_strength('Boston Celtics'):.2f}")
    
    # Matchup test
    print(f"\nCeltics vs Lakers strength diff: {model.get_matchup_strength_diff('Boston Celtics', 'Los Angeles Lakers'):.2f}")
