"""
API routes for Player Props predictions.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.ml.player_props import PlayerPropsModel, PropPrediction

router = APIRouter()


class PropRequest(BaseModel):
    """Request to analyze a single prop."""
    player: str
    opponent: str
    prop_type: str  # "points", "rebounds", "assists", "threes", "pra"
    line: float
    odds_over: float = 1.90
    odds_under: float = 1.90
    expected_minutes: Optional[float] = None


class PropBatchRequest(BaseModel):
    """Request to analyze multiple props."""
    props: List[PropRequest]
    missing_players: Optional[dict] = None  # {team: [player_names]}


class PropResponse(BaseModel):
    """Single prop prediction response."""
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
    best_bet: Optional[str]
    confidence: str
    reasoning: str


@router.post("/analyze", response_model=PropResponse)
async def analyze_prop(request: PropRequest):
    """Analyze a single player prop for value."""
    model = PlayerPropsModel()
    
    prediction = model.predict_prop(
        player_name=request.player,
        opponent=request.opponent,
        prop_type=request.prop_type,
        line=request.line,
        odds_over=request.odds_over,
        odds_under=request.odds_under,
        expected_minutes=request.expected_minutes,
    )
    
    if not prediction:
        raise HTTPException(status_code=404, detail=f"Player '{request.player}' not found")
    
    return PropResponse(
        player=prediction.player,
        team=prediction.team,
        opponent=prediction.opponent,
        prop_type=prediction.prop_type,
        projection=prediction.projection,
        std_dev=prediction.std_dev,
        line=prediction.line,
        odds_over=prediction.odds_over,
        odds_under=prediction.odds_under,
        prob_over=prediction.prob_over,
        prob_under=prediction.prob_under,
        implied_over=prediction.implied_over,
        implied_under=prediction.implied_under,
        value_over=prediction.value_over,
        value_under=prediction.value_under,
        best_bet=prediction.best_bet,
        confidence=prediction.confidence,
        reasoning=prediction.reasoning,
    )


@router.post("/scan", response_model=List[PropResponse])
async def scan_props(request: PropBatchRequest):
    """Scan multiple props for value bets."""
    model = PlayerPropsModel(missing_players=request.missing_players)
    
    props_data = [
        {
            "player": p.player,
            "opponent": p.opponent,
            "prop_type": p.prop_type,
            "line": p.line,
            "odds_over": p.odds_over,
            "odds_under": p.odds_under,
            "expected_minutes": p.expected_minutes,
        }
        for p in request.props
    ]
    
    predictions = model.scan_all_props(props_data)
    
    return [
        PropResponse(
            player=p.player,
            team=p.team,
            opponent=p.opponent,
            prop_type=p.prop_type,
            projection=p.projection,
            std_dev=p.std_dev,
            line=p.line,
            odds_over=p.odds_over,
            odds_under=p.odds_under,
            prob_over=p.prob_over,
            prob_under=p.prob_under,
            implied_over=p.implied_over,
            implied_under=p.implied_under,
            value_over=p.value_over,
            value_under=p.value_under,
            best_bet=p.best_bet,
            confidence=p.confidence,
            reasoning=p.reasoning,
        )
        for p in predictions
    ]


@router.get("/players")
async def get_supported_players():
    """Get list of players supported by the model."""
    model = PlayerPropsModel()
    players = []
    
    for name, data in model.PLAYER_DATA.items():
        players.append({
            "name": name,
            "team": data["team"],
            "points_avg": data.get("points", 0),
            "rebounds_avg": data.get("rebounds", 0),
            "assists_avg": data.get("assists", 0),
            "minutes_avg": data.get("minutes", 0),
        })
    
    return {"players": players}


@router.get("/top-props")
async def get_top_props():
    """
    Get today's top prop value bets.
    In production, this would fetch live props from The Odds API.
    """
    model = PlayerPropsModel(
        missing_players={
            "Milwaukee Bucks": ["Khris Middleton"],
            "Phoenix Suns": ["Bradley Beal"],
            "Philadelphia 76ers": ["Joel Embiid"],
        }
    )
    
    # Sample props (would come from API)
    sample_props = [
        {"player": "Giannis Antetokounmpo", "opponent": "Miami Heat", "prop_type": "points", "line": 28.5, "odds_over": 1.87, "odds_under": 1.93},
        {"player": "LeBron James", "opponent": "Phoenix Suns", "prop_type": "points", "line": 24.5, "odds_over": 1.90, "odds_under": 1.90},
        {"player": "Shai Gilgeous-Alexander", "opponent": "Dallas Mavericks", "prop_type": "points", "line": 30.5, "odds_over": 1.85, "odds_under": 1.95},
        {"player": "Nikola Jokic", "opponent": "Golden State Warriors", "prop_type": "rebounds", "line": 11.5, "odds_over": 1.88, "odds_under": 1.92},
        {"player": "Jayson Tatum", "opponent": "Brooklyn Nets", "prop_type": "points", "line": 26.5, "odds_over": 1.90, "odds_under": 1.90},
        {"player": "Stephen Curry", "opponent": "Portland Trail Blazers", "prop_type": "points", "line": 25.5, "odds_over": 1.85, "odds_under": 1.95},
        {"player": "Luka Doncic", "opponent": "Oklahoma City Thunder", "prop_type": "assists", "line": 8.5, "odds_over": 1.82, "odds_under": 1.98},
        {"player": "Anthony Edwards", "opponent": "Los Angeles Lakers", "prop_type": "points", "line": 24.5, "odds_over": 1.90, "odds_under": 1.90},
    ]
    
    predictions = model.scan_all_props(sample_props)
    
    return {
        "count": len(predictions),
        "props": [
            {
                "player": p.player,
                "team": p.team,
                "opponent": p.opponent,
                "prop_type": p.prop_type,
                "projection": p.projection,
                "line": p.line,
                "best_bet": p.best_bet,
                "value": max(p.value_over, p.value_under),
                "probability": p.prob_over if p.best_bet == "OVER" else p.prob_under,
                "confidence": p.confidence,
            }
            for p in predictions
        ],
    }
