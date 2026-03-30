"""
NBA stats ingestion using the nba_api package.
Pulls team game logs for feature engineering.
No API key required.
"""
import logging
import pandas as pd
from nba_api.stats.endpoints import teamgamelog, leaguegamefinder
from nba_api.stats.static import teams

logger = logging.getLogger(__name__)

NBA_SEASON = "2023-24"


def get_all_team_ids() -> list[dict]:
    """Return list of all NBA teams with id and full_name."""
    return teams.get_teams()


def get_team_game_log(team_id: int, season: str = NBA_SEASON) -> pd.DataFrame:
    """
    Fetch full season game log for a team.
    Returns DataFrame with columns: GAME_DATE, MATCHUP, WL, PTS, OPP_PTS, etc.
    """
    try:
        log = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        df = log.get_data_frames()[0]
        df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
        df = df.sort_values("GAME_DATE").reset_index(drop=True)
        return df
    except Exception as e:
        logger.error(f"Failed to fetch game log for team {team_id}: {e}")
        return pd.DataFrame()


def get_team_id_by_name(name: str) -> int | None:
    """Fuzzy match a team name to an NBA team ID."""
    name_lower = name.lower()
    for team in get_all_team_ids():
        if name_lower in team["full_name"].lower() or name_lower in team["nickname"].lower():
            return team["id"]
    return None


def get_recent_form(team_id: int, n_games: int = 10) -> dict:
    """
    Returns recent form stats for a team over last n_games.
    Used as input features for the ML model.
    """
    df = get_team_game_log(team_id)
    if df.empty:
        return {}

    recent = df.tail(n_games).copy()
    recent["WIN"] = (recent["WL"] == "W").astype(int)

    # Home/away split from MATCHUP string (e.g. "BOS vs. LAL" = home, "BOS @ LAL" = away)
    recent["IS_HOME"] = recent["MATCHUP"].apply(lambda m: "vs." in m)

    return {
        "win_pct_last_n": round(recent["WIN"].mean(), 4),
        "avg_pts_scored": round(recent["PTS"].mean(), 2),
        "avg_pts_allowed": round(recent["OPP_PTS"].mean(), 2) if "OPP_PTS" in recent else None,
        "home_win_pct": round(recent[recent["IS_HOME"]]["WIN"].mean(), 4) if recent["IS_HOME"].any() else None,
        "away_win_pct": round(recent[~recent["IS_HOME"]]["WIN"].mean(), 4) if (~recent["IS_HOME"]).any() else None,
        "games_sampled": len(recent),
    }
