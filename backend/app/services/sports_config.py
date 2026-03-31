"""
Sports Configuration Module
Defines all supported sports with their API keys and display info.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class SportCategory(str, Enum):
    BASKETBALL = "basketball"
    FOOTBALL = "football"
    BASEBALL = "baseball"
    HOCKEY = "hockey"
    SOCCER = "soccer"
    TENNIS = "tennis"
    MMA = "mma"
    BOXING = "boxing"
    GOLF = "golf"
    RACING = "racing"
    ESPORTS = "esports"
    OTHER = "other"


@dataclass
class SportConfig:
    """Configuration for a single sport."""
    key: str                    # The Odds API sport key
    name: str                   # Display name
    category: SportCategory     # Category for grouping
    emoji: str                  # Emoji icon
    active: bool = True         # Whether to fetch odds
    markets: list[str] = None   # Supported markets
    
    def __post_init__(self):
        if self.markets is None:
            self.markets = ["h2h", "spreads", "totals"]


# All sports supported by The Odds API
SPORTS_CONFIG: dict[str, SportConfig] = {
    # ═══════════════════════════════════════════════════════════════
    # BASKETBALL
    # ═══════════════════════════════════════════════════════════════
    "basketball_nba": SportConfig(
        key="basketball_nba",
        name="NBA",
        category=SportCategory.BASKETBALL,
        emoji="🏀",
    ),
    "basketball_ncaab": SportConfig(
        key="basketball_ncaab",
        name="NCAA Basketball",
        category=SportCategory.BASKETBALL,
        emoji="🏀",
    ),
    "basketball_euroleague": SportConfig(
        key="basketball_euroleague",
        name="EuroLeague",
        category=SportCategory.BASKETBALL,
        emoji="🏀",
    ),
    "basketball_nbl": SportConfig(
        key="basketball_nbl",
        name="NBL Australia",
        category=SportCategory.BASKETBALL,
        emoji="🏀",
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # AMERICAN FOOTBALL
    # ═══════════════════════════════════════════════════════════════
    "americanfootball_nfl": SportConfig(
        key="americanfootball_nfl",
        name="NFL",
        category=SportCategory.FOOTBALL,
        emoji="🏈",
    ),
    "americanfootball_ncaaf": SportConfig(
        key="americanfootball_ncaaf",
        name="NCAA Football",
        category=SportCategory.FOOTBALL,
        emoji="🏈",
    ),
    "americanfootball_cfl": SportConfig(
        key="americanfootball_cfl",
        name="CFL",
        category=SportCategory.FOOTBALL,
        emoji="🏈",
    ),
    "americanfootball_xfl": SportConfig(
        key="americanfootball_xfl",
        name="XFL",
        category=SportCategory.FOOTBALL,
        emoji="🏈",
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # BASEBALL
    # ═══════════════════════════════════════════════════════════════
    "baseball_mlb": SportConfig(
        key="baseball_mlb",
        name="MLB",
        category=SportCategory.BASEBALL,
        emoji="⚾",
    ),
    "baseball_ncaa": SportConfig(
        key="baseball_ncaa",
        name="NCAA Baseball",
        category=SportCategory.BASEBALL,
        emoji="⚾",
    ),
    "baseball_kbo": SportConfig(
        key="baseball_kbo",
        name="KBO (Korea)",
        category=SportCategory.BASEBALL,
        emoji="⚾",
    ),
    "baseball_npb": SportConfig(
        key="baseball_npb",
        name="NPB (Japan)",
        category=SportCategory.BASEBALL,
        emoji="⚾",
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # HOCKEY
    # ═══════════════════════════════════════════════════════════════
    "icehockey_nhl": SportConfig(
        key="icehockey_nhl",
        name="NHL",
        category=SportCategory.HOCKEY,
        emoji="🏒",
    ),
    "icehockey_sweden_hockey_league": SportConfig(
        key="icehockey_sweden_hockey_league",
        name="SHL (Sweden)",
        category=SportCategory.HOCKEY,
        emoji="🏒",
    ),
    "icehockey_finland_liiga": SportConfig(
        key="icehockey_finland_liiga",
        name="Liiga (Finland)",
        category=SportCategory.HOCKEY,
        emoji="🏒",
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # SOCCER
    # ═══════════════════════════════════════════════════════════════
    "soccer_epl": SportConfig(
        key="soccer_epl",
        name="English Premier League",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_spain_la_liga": SportConfig(
        key="soccer_spain_la_liga",
        name="La Liga",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_germany_bundesliga": SportConfig(
        key="soccer_germany_bundesliga",
        name="Bundesliga",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_italy_serie_a": SportConfig(
        key="soccer_italy_serie_a",
        name="Serie A",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_france_ligue_one": SportConfig(
        key="soccer_france_ligue_one",
        name="Ligue 1",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_uefa_champs_league": SportConfig(
        key="soccer_uefa_champs_league",
        name="Champions League",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_uefa_europa_league": SportConfig(
        key="soccer_uefa_europa_league",
        name="Europa League",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_usa_mls": SportConfig(
        key="soccer_usa_mls",
        name="MLS",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_australia_aleague": SportConfig(
        key="soccer_australia_aleague",
        name="A-League",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_brazil_campeonato": SportConfig(
        key="soccer_brazil_campeonato",
        name="Brasileirão",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    "soccer_mexico_ligamx": SportConfig(
        key="soccer_mexico_ligamx",
        name="Liga MX",
        category=SportCategory.SOCCER,
        emoji="⚽",
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # TENNIS
    # ═══════════════════════════════════════════════════════════════
    "tennis_atp_french_open": SportConfig(
        key="tennis_atp_french_open",
        name="ATP French Open",
        category=SportCategory.TENNIS,
        emoji="🎾",
        markets=["h2h"],
    ),
    "tennis_atp_wimbledon": SportConfig(
        key="tennis_atp_wimbledon",
        name="ATP Wimbledon",
        category=SportCategory.TENNIS,
        emoji="🎾",
        markets=["h2h"],
    ),
    "tennis_atp_us_open": SportConfig(
        key="tennis_atp_us_open",
        name="ATP US Open",
        category=SportCategory.TENNIS,
        emoji="🎾",
        markets=["h2h"],
    ),
    "tennis_atp_aus_open": SportConfig(
        key="tennis_atp_aus_open",
        name="ATP Australian Open",
        category=SportCategory.TENNIS,
        emoji="🎾",
        markets=["h2h"],
    ),
    "tennis_wta_french_open": SportConfig(
        key="tennis_wta_french_open",
        name="WTA French Open",
        category=SportCategory.TENNIS,
        emoji="🎾",
        markets=["h2h"],
    ),
    "tennis_wta_wimbledon": SportConfig(
        key="tennis_wta_wimbledon",
        name="WTA Wimbledon",
        category=SportCategory.TENNIS,
        emoji="🎾",
        markets=["h2h"],
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # MMA / BOXING
    # ═══════════════════════════════════════════════════════════════
    "mma_mixed_martial_arts": SportConfig(
        key="mma_mixed_martial_arts",
        name="UFC / MMA",
        category=SportCategory.MMA,
        emoji="🥊",
        markets=["h2h"],
    ),
    "boxing_boxing": SportConfig(
        key="boxing_boxing",
        name="Boxing",
        category=SportCategory.BOXING,
        emoji="🥊",
        markets=["h2h"],
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # GOLF
    # ═══════════════════════════════════════════════════════════════
    "golf_pga_championship": SportConfig(
        key="golf_pga_championship",
        name="PGA Championship",
        category=SportCategory.GOLF,
        emoji="⛳",
        markets=["outrights"],
    ),
    "golf_masters_tournament": SportConfig(
        key="golf_masters_tournament",
        name="Masters Tournament",
        category=SportCategory.GOLF,
        emoji="⛳",
        markets=["outrights"],
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # RUGBY / AFL / CRICKET
    # ═══════════════════════════════════════════════════════════════
    "rugbyleague_nrl": SportConfig(
        key="rugbyleague_nrl",
        name="NRL",
        category=SportCategory.OTHER,
        emoji="🏉",
    ),
    "aussierules_afl": SportConfig(
        key="aussierules_afl",
        name="AFL",
        category=SportCategory.OTHER,
        emoji="🏉",
    ),
    "cricket_ipl": SportConfig(
        key="cricket_ipl",
        name="IPL Cricket",
        category=SportCategory.OTHER,
        emoji="🏏",
    ),
    "cricket_test_match": SportConfig(
        key="cricket_test_match",
        name="Test Cricket",
        category=SportCategory.OTHER,
        emoji="🏏",
    ),
}


# Horse Racing Configuration (separate API)
HORSE_RACING_CONFIG = {
    "uk_horse_racing": {
        "name": "UK Horse Racing",
        "emoji": "🏇",
        "tracks": ["Cheltenham", "Ascot", "Epsom", "Newmarket", "York", "Aintree"],
    },
    "us_horse_racing": {
        "name": "US Horse Racing",
        "emoji": "🏇",
        "tracks": ["Churchill Downs", "Belmont Park", "Santa Anita", "Saratoga", "Del Mar"],
    },
    "aus_horse_racing": {
        "name": "Australian Horse Racing",
        "emoji": "🏇",
        "tracks": ["Flemington", "Randwick", "Moonee Valley", "Caulfield"],
    },
}


# Greyhound Racing Configuration
GREYHOUND_RACING_CONFIG = {
    "uk_greyhounds": {
        "name": "UK Greyhounds",
        "emoji": "🐕",
        "tracks": ["Romford", "Monmore", "Towcester", "Nottingham", "Crayford"],
    },
    "aus_greyhounds": {
        "name": "Australian Greyhounds",
        "emoji": "🐕",
        "tracks": ["Wentworth Park", "The Meadows", "Sandown", "Cannington"],
    },
}


def get_active_sports() -> list[SportConfig]:
    """Get all active sports for odds fetching."""
    return [s for s in SPORTS_CONFIG.values() if s.active]


def get_sports_by_category(category: SportCategory) -> list[SportConfig]:
    """Get all sports in a category."""
    return [s for s in SPORTS_CONFIG.values() if s.category == category and s.active]


def get_sport_config(sport_key: str) -> Optional[SportConfig]:
    """Get config for a specific sport."""
    return SPORTS_CONFIG.get(sport_key)


def get_all_categories() -> list[dict]:
    """Get all categories with their sports."""
    categories = {}
    for sport in get_active_sports():
        if sport.category not in categories:
            categories[sport.category] = {
                "key": sport.category.value,
                "name": sport.category.value.title(),
                "sports": [],
            }
        categories[sport.category]["sports"].append({
            "key": sport.key,
            "name": sport.name,
            "emoji": sport.emoji,
        })
    return list(categories.values())
