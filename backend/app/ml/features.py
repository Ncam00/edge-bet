"""
Feature engineering pipeline.
Transforms raw game + team stats into model-ready feature vectors.
"""
import pandas as pd
import numpy as np
import logging
from app.services.nba_service import get_team_id_by_name, get_recent_form, get_team_game_log

logger = logging.getLogger(__name__)

N_FORM_GAMES = 10
N_H2H_GAMES = 8


def build_game_features(home_team: str, away_team: str) -> dict | None:
    """
    Build a feature dict for an upcoming matchup.
    Returns None if data is unavailable.

    Features:
    - Rolling win%, pts scored/allowed (last 10) for home + away
    - Home/away splits
    - Head-to-head record (last 8 meetings)
    - Rest days (placeholder — requires schedule data)
    """
    home_id = get_team_id_by_name(home_team)
    away_id = get_team_id_by_name(away_team)

    if not home_id or not away_id:
        logger.warning(f"Could not resolve team IDs: {home_team}, {away_team}")
        return None

    home_form = get_recent_form(home_id, N_FORM_GAMES)
    away_form = get_recent_form(away_id, N_FORM_GAMES)

    if not home_form or not away_form:
        return None

    h2h = _get_h2h_stats(home_id, away_id)

    features = {
        # Home team
        "home_win_pct": home_form.get("win_pct_last_n", 0.5),
        "home_avg_pts": home_form.get("avg_pts_scored", 110),
        "home_avg_allowed": home_form.get("avg_pts_allowed", 110),
        "home_home_win_pct": home_form.get("home_win_pct", 0.5),
        "home_net_rating": _net_rating(home_form),

        # Away team
        "away_win_pct": away_form.get("win_pct_last_n", 0.5),
        "away_avg_pts": away_form.get("avg_pts_scored", 110),
        "away_avg_allowed": away_form.get("avg_pts_allowed", 110),
        "away_away_win_pct": away_form.get("away_win_pct", 0.5),
        "away_net_rating": _net_rating(away_form),

        # Matchup
        "win_pct_diff": home_form.get("win_pct_last_n", 0.5) - away_form.get("win_pct_last_n", 0.5),
        "net_rating_diff": _net_rating(home_form) - _net_rating(away_form),

        # H2H
        "h2h_home_win_pct": h2h.get("home_win_pct", 0.5),
        "h2h_games": h2h.get("games", 0),
    }

    return features


def _net_rating(form: dict) -> float:
    """Points scored minus points allowed per game."""
    scored = form.get("avg_pts_scored", 110)
    allowed = form.get("avg_pts_allowed", 110)
    if scored is None or allowed is None:
        return 0.0
    return round(scored - allowed, 2)


def _get_h2h_stats(home_id: int, away_id: int) -> dict:
    """
    Compute head-to-head record between two teams.
    Looks at home team's game log and finds matchups vs away team.
    """
    try:
        df = get_team_game_log(home_id)
        if df.empty:
            return {}

        # MATCHUP format: "TEAM vs. OPP" or "TEAM @ OPP"
        # We need to match opponent — nba_api uses abbreviations
        # This is a simplified match; production should use team abbreviation map
        h2h = df.tail(N_H2H_GAMES * 4)  # pull more games to find enough H2H
        # Filter where matchup contains the away team abbreviation
        # (placeholder — real impl maps full name to abbreviation)
        games = len(h2h)
        wins = int(h2h["WL"].eq("W").sum())
        return {
            "home_win_pct": round(wins / games, 4) if games > 0 else 0.5,
            "games": games,
        }
    except Exception as e:
        logger.error(f"H2H error: {e}")
        return {}


def features_to_array(features: dict) -> list[float]:
    """
    Convert feature dict to ordered list for model input.
    Order must match the training column order.
    """
    FEATURE_ORDER = [
        "home_win_pct", "home_avg_pts", "home_avg_allowed",
        "home_home_win_pct", "home_net_rating",
        "away_win_pct", "away_avg_pts", "away_avg_allowed",
        "away_away_win_pct", "away_net_rating",
        "win_pct_diff", "net_rating_diff",
        "h2h_home_win_pct", "h2h_games",
    ]
    return [features.get(f, 0.0) for f in FEATURE_ORDER]
