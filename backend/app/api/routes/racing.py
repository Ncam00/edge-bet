"""
Racing API Routes
Provides endpoints for horse and greyhound racing data with live video integration.
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone
from app.services.racing_service import (
    get_racing_service,
    RaceType,
)
from app.services.video_service import video_service
from app.services.betfair_service import get_betfair_service
from app.services.replay_service import get_replay_service

router = APIRouter(tags=["racing"])


@router.get("/today")
def get_todays_races(
    race_type: Optional[str] = Query(None, description="Filter by 'horse' or 'greyhound'"),
    country: Optional[str] = Query(None, description="Filter by country: UK, US, AUS"),
):
    """Get all races for today."""
    service = get_racing_service()
    
    rt = None
    if race_type:
        try:
            rt = RaceType(race_type)
        except ValueError:
            return {"error": f"Invalid race_type: {race_type}. Use 'horse' or 'greyhound'"}
    
    races = service.get_todays_races(race_type=rt, country=country)
    
    return {
        "count": len(races),
        "races": [
            {
                "id": r.id,
                "race_type": r.race_type.value,
                "track": r.track,
                "race_number": r.race_number,
                "race_name": r.race_name,
                "distance": r.distance,
                "race_class": r.race_class,
                "going": r.going.value,
                "post_time": r.post_time.isoformat(),
                "prize_money": r.prize_money,
                "country": r.country,
                "runners_count": len(r.runners),
                # Add video URL for each race
                "video": video_service.get_race_video_url(r.track, r.race_number, r.country)
                    if r.race_type == RaceType.HORSE
                    else video_service.get_greyhound_video_url(r.track, r.race_number, r.country),
            }
            for r in races
        ],
    }


@router.get("/value-bets")
def get_racing_value_bets(
    race_type: Optional[str] = Query(None, description="Filter by 'horse' or 'greyhound'"),
    min_ev: float = Query(0.05, description="Minimum expected value"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get value bets across all races."""
    service = get_racing_service()
    
    rt = None
    if race_type:
        try:
            rt = RaceType(race_type)
        except ValueError:
            return {"error": f"Invalid race_type: {race_type}"}
    
    value_bets = service.get_value_bets(min_ev=min_ev, race_type=rt)
    
    # Apply limit
    value_bets = value_bets[:limit]
    
    # Count by confidence
    high = sum(1 for b in value_bets if b["confidence"] == "HIGH")
    medium = sum(1 for b in value_bets if b["confidence"] == "MEDIUM")
    
    return {
        "count": len(value_bets),
        "high_confidence": high,
        "medium_confidence": medium,
        "bets": value_bets,
    }


@router.get("/race/{race_id}")
def get_race_details(race_id: str):
    """Get full details for a specific race including all runners with analysis."""
    service = get_racing_service()
    
    # Search through today's races
    races = service.get_todays_races()
    
    for race in races:
        if race.id == race_id:
            runners_data = []
            for r in race.runners:
                form = service.analyze_form(r, race)
                rec = service.get_bet_recommendation(r, race, form)
                
                runners_data.append({
                    "number": r.number,
                    "name": r.name,
                    "odds": r.odds,
                    "morning_line": r.morning_line,
                    "trainer": r.trainer,
                    "jockey": r.jockey,
                    "form": r.form,
                    "weight": r.weight,
                    "box": r.box,
                    "age": r.age,
                    "our_probability": r.our_probability,
                    "implied_probability": r.implied_probability,
                    "expected_value": r.expected_value,
                    "is_value": r.expected_value >= 0.05,
                    "form_analysis": {
                        "rating": form.form_rating,
                        "trend": form.trend,
                        "fitness": form.fitness_score,
                        "going_suited": form.going_suitability,
                        "wins": form.wins_last_10,
                        "places": form.places_last_10,
                        "key_positives": form.key_positives[:2],
                        "key_negatives": form.key_negatives[:1],
                    },
                    "recommendation": {
                        "bet_type": rec.bet_type.value if rec else None,
                        "confidence": rec.confidence if rec else None,
                        "stake_pct": rec.stake_percentage if rec else None,
                        "reasoning": rec.reasoning[:2] if rec else [],
                    } if rec else None,
                })
            
            return {
                "id": race.id,
                "race_type": race.race_type.value,
                "track": race.track,
                "race_number": race.race_number,
                "race_name": race.race_name,
                "distance": race.distance,
                "race_class": race.race_class,
                "going": race.going.value,
                "post_time": race.post_time.isoformat(),
                "prize_money": race.prize_money,
                "country": race.country,
                "runners": runners_data,
                # Add video for the race
                "video": video_service.get_race_video_url(race.track, race.race_number, race.country)
                    if race.race_type == RaceType.HORSE
                    else video_service.get_greyhound_video_url(race.track, race.race_number, race.country),
            }
    
    return {"error": "Race not found"}


@router.get("/runner/{race_id}/{runner_number}")
def get_runner_analysis(race_id: str, runner_number: int):
    """Get detailed analysis and betting recommendation for a runner."""
    service = get_racing_service()
    result = service.get_runner_analysis(race_id, runner_number)
    
    if result:
        return result
    return {"error": "Runner not found"}


@router.get("/tips")
def get_top_tips(
    limit: int = Query(10, ge=1, le=50, description="Number of tips to return"),
    race_type: Optional[str] = Query(None, description="Filter by 'horse' or 'greyhound'"),
):
    """Get top betting tips with full analysis and recommendations."""
    service = get_racing_service()
    tips = service.get_top_tips(limit=limit * 2)  # Get more for filtering
    
    if race_type:
        tips = [t for t in tips if t["race_type"] == race_type]
    
    tips = tips[:limit]
    
    # Group by confidence
    high = [t for t in tips if t["confidence"] == "HIGH"]
    medium = [t for t in tips if t["confidence"] == "MEDIUM"]
    
    return {
        "total": len(tips),
        "high_confidence": len(high),
        "medium_confidence": len(medium),
        "tips": tips,
    }


@router.get("/horses/tracks")
def get_horse_tracks():
    """Get all supported horse racing tracks."""
    from app.services.racing_service import (
        UK_HORSE_TRACKS, US_HORSE_TRACKS, AUS_HORSE_TRACKS
    )
    
    return {
        "UK": [{"name": t[0], "surface": t[1]} for t in UK_HORSE_TRACKS],
        "US": [{"name": t[0], "surface": t[1]} for t in US_HORSE_TRACKS],
        "AUS": [{"name": t[0], "surface": t[1]} for t in AUS_HORSE_TRACKS],
    }


@router.get("/greyhounds/tracks")
def get_greyhound_tracks():
    """Get all supported greyhound tracks."""
    from app.services.racing_service import UK_GREY_TRACKS, AUS_GREY_TRACKS
    
    return {
        "UK": UK_GREY_TRACKS,
        "AUS": AUS_GREY_TRACKS,
    }


@router.get("/summary")
def get_racing_summary():
    """Get summary of today's racing card."""
    service = get_racing_service()
    
    horse_races = service.get_todays_races(race_type=RaceType.HORSE)
    grey_races = service.get_todays_races(race_type=RaceType.GREYHOUND)
    
    horse_bets = service.get_value_bets(race_type=RaceType.HORSE)
    grey_bets = service.get_value_bets(race_type=RaceType.GREYHOUND)
    
    # Get unique tracks
    horse_tracks = list(set(r.track for r in horse_races))
    grey_tracks = list(set(r.track for r in grey_races))
    
    return {
        "horses": {
            "races": len(horse_races),
            "tracks": horse_tracks,
            "value_bets": len(horse_bets),
            "high_confidence": sum(1 for b in horse_bets if b["confidence"] == "HIGH"),
        },
        "greyhounds": {
            "races": len(grey_races),
            "tracks": grey_tracks,
            "value_bets": len(grey_bets),
            "high_confidence": sum(1 for b in grey_bets if b["confidence"] == "HIGH"),
        },
        "total_value_bets": len(horse_bets) + len(grey_bets),
    }


# =============================================================================
# VIDEO STREAMING ENDPOINTS
# =============================================================================

@router.get("/video/streams")
async def get_live_streams(
    region: Optional[str] = Query(None, description="Filter by region: UK, AU, US, HK")
):
    """
    Get all available live racing video streams.
    Returns embed URLs for free live racing video from multiple sources.
    """
    streams = await video_service.get_live_streams(region=region)
    
    return {
        "count": len(streams),
        "streams": streams,
        "sources": [
            {
                "name": "Racing.com",
                "region": "AU",
                "description": "Free live Australian horse racing",
                "type": "iframe"
            },
            {
                "name": "At The Races",
                "region": "UK",
                "description": "UK & Irish racing coverage",
                "type": "iframe"
            },
            {
                "name": "Sky Racing",
                "region": "AU",
                "description": "Australian horse & greyhound racing",
                "type": "iframe"
            },
            {
                "name": "YouTube Racing",
                "region": "Global",
                "description": "Free live streams from racing channels",
                "type": "youtube"
            },
            {
                "name": "RPGTV",
                "region": "UK",
                "description": "Free UK racing channel",
                "type": "iframe"
            },
            {
                "name": "HKJC",
                "region": "HK",
                "description": "Hong Kong Jockey Club racing",
                "type": "iframe"
            },
            {
                "name": "TVG",
                "region": "US",
                "description": "US horse racing coverage",
                "type": "iframe"
            }
        ]
    }


@router.get("/video/race/{race_id}")
def get_race_video(race_id: str):
    """
    Get live video stream URL for a specific race.
    Returns embed URL that can be embedded in an iframe or video player.
    """
    service = get_racing_service()
    races = service.get_todays_races()
    
    for race in races:
        if race.id == race_id:
            if race.race_type == RaceType.HORSE:
                video_info = video_service.get_race_video_url(
                    race.track, race.race_number, race.country
                )
            else:
                video_info = video_service.get_greyhound_video_url(
                    race.track, race.race_number, race.country
                )
            
            return {
                "race_id": race.id,
                "track": race.track,
                "race_number": race.race_number,
                "post_time": race.post_time.isoformat(),
                "video": video_info,
                "instructions": {
                    "iframe": "Embed the embed_url in an iframe with allow='autoplay'",
                    "youtube": "For YouTube streams, use the YouTube iframe API",
                    "fallback": "If primary stream unavailable, use backup_url"
                }
            }
    
    return {"error": "Race not found"}


@router.get("/video/youtube")
def get_youtube_racing_streams():
    """
    Get all YouTube racing live streams.
    These are always free and embeddable.
    """
    streams = []
    
    for key, source in video_service.YOUTUBE_LIVE_STREAMS.items():
        streams.append({
            "id": key,
            "name": source["name"],
            "region": source["region"],
            "channel_id": source["channel_id"],
            "live_url": f"https://www.youtube.com/channel/{source['channel_id']}/live",
            "embed_url": video_service.get_youtube_embed(channel_id=source["channel_id"]),
        })
    
    return {
        "count": len(streams),
        "streams": streams,
        "usage": {
            "embed": "Use embed_url in an iframe: <iframe src='embed_url' allow='autoplay' />",
            "watch": "Or open live_url in browser to watch directly on YouTube"
        }
    }


@router.get("/video/regional/{region}")
def get_regional_streams(region: str):
    """
    Get best live video streams for a specific region.
    Regions: UK, AU, US, HK
    """
    region = region.upper()
    
    regional_sources = {
        "UK": [
            {
                "name": "At The Races",
                "embed_url": "https://www.attheraces.com/embed/live",
                "type": "iframe",
                "description": "UK & Irish horse racing"
            },
            {
                "name": "RPGTV",
                "embed_url": "https://www.rpgtv.com/embed/live",
                "type": "iframe",
                "description": "Free UK racing channel"
            },
            {
                "name": "YouTube UK Racing",
                "embed_url": video_service.get_youtube_embed(channel_id="UCkHSzRAcBvYqrRRN3DrHHmA"),
                "type": "youtube",
                "description": "UK Racing YouTube channel"
            }
        ],
        "AU": [
            {
                "name": "Racing.com",
                "embed_url": "https://www.racing.com/embed/vision/live",
                "type": "iframe",
                "description": "Free Australian racing"
            },
            {
                "name": "Sky Racing AU",
                "embed_url": "https://www.skyracing.com.au/live",
                "type": "iframe",
                "description": "Australian thoroughbred & greyhound"
            },
            {
                "name": "YouTube Racing.com",
                "embed_url": video_service.get_youtube_embed(channel_id="UCT5vCPP7kq6b3FfS5pLiHkQ"),
                "type": "youtube",
                "description": "Racing.com YouTube live"
            }
        ],
        "US": [
            {
                "name": "TVG",
                "embed_url": "https://www.tvg.com/live",
                "type": "iframe",
                "description": "US horse racing"
            },
            {
                "name": "YouTube TVG",
                "embed_url": video_service.get_youtube_embed(channel_id="UCWR-2F4mZGePLwNvEuOvRLA"),
                "type": "youtube",
                "description": "TVG Horse Racing YouTube"
            }
        ],
        "HK": [
            {
                "name": "HKJC Live",
                "embed_url": "https://racing.hkjc.com/racing/video/english/live",
                "type": "iframe",
                "description": "Hong Kong Jockey Club"
            },
            {
                "name": "YouTube HKJC",
                "embed_url": video_service.get_youtube_embed(channel_id="UCL8NcJkH1CBfeMJggY7cPVQ"),
                "type": "youtube",
                "description": "HKJC YouTube channel"
            }
        ]
    }
    
    streams = regional_sources.get(region, [])
    
    if not streams:
        return {"error": f"Invalid region: {region}. Use UK, AU, US, or HK"}
    
    return {
        "region": region,
        "streams": streams,
        "recommended": streams[0] if streams else None
    }


# =============================================================================
# BETFAIR EXCHANGE LIVE ODDS
# =============================================================================

@router.get("/betfair/markets")
async def get_betfair_markets(
    race_type: str = Query("horse", description="'horse' or 'greyhound'"),
    country: Optional[str] = Query(None, description="Country code: GB, IE, AU"),
    hours_ahead: int = Query(4, ge=1, le=24, description="Hours ahead to look")
):
    """
    Get live racing odds from Betfair Exchange.
    Provides real-time back/lay prices and market liquidity.
    
    Falls back to demo data if Betfair credentials not configured.
    """
    service = get_betfair_service()
    
    country_codes = [country] if country else None
    
    markets = await service.get_racing_markets(
        event_type=race_type,
        country_codes=country_codes,
        hours_ahead=hours_ahead
    )
    
    now = datetime.now(timezone.utc)
    
    return {
        "source": "Betfair Exchange" if hasattr(service, 'session_token') else "Demo Mode",
        "count": len(markets),
        "markets": [
            {
                "market_id": m.market_id,
                "market_name": m.market_name,
                "track": m.event_venue,
                "race_number": m.race_number,
                "start_time": m.market_start_time.isoformat(),
                "countdown_seconds": max(0, int((m.market_start_time - now).total_seconds())),
                "status": m.status.value,
                "total_matched": m.total_matched,
                "country": m.country_code,
                "race_type": m.race_type,
                "runners": [
                    {
                        "selection_id": r.selection_id,
                        "name": r.runner_name,
                        "sort_priority": r.sort_priority,
                        "back_price": r.back_price,
                        "back_size": r.back_size,
                        "lay_price": r.lay_price,
                        "lay_size": r.lay_size,
                        "last_traded": r.last_traded_price,
                        "total_matched": r.total_matched,
                        "implied_probability": round(r.implied_probability * 100, 1),
                        "status": r.status
                    }
                    for r in m.runners
                ]
            }
            for m in markets
        ]
    }


@router.get("/betfair/market/{market_id}")
async def get_betfair_market_prices(market_id: str):
    """Get live prices for a specific Betfair market."""
    service = get_betfair_service()
    
    if hasattr(service, 'get_market_prices'):
        market = await service.get_market_prices(market_id)
        
        if market:
            return {
                "market_id": market.market_id,
                "status": market.status.value,
                "total_matched": market.total_matched,
                "runners": [
                    {
                        "selection_id": r.selection_id,
                        "name": r.runner_name,
                        "back_price": r.back_price,
                        "back_size": r.back_size,
                        "lay_price": r.lay_price,
                        "lay_size": r.lay_size,
                        "last_traded": r.last_traded_price,
                        "total_matched": r.total_matched
                    }
                    for r in market.runners
                ]
            }
    
    return {"error": "Market not found or service unavailable"}


# =============================================================================
# RACE REPLAYS
# =============================================================================

@router.get("/replays")
async def get_race_replays(
    track: Optional[str] = Query(None, description="Filter by track name"),
    country: Optional[str] = Query(None, description="Country code: UK, AU, US, HK"),
    race_type: str = Query("horse", description="'horse' or 'greyhound'"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get race replays for form research.
    Shows past race videos with results and analysis.
    """
    service = get_replay_service()
    
    replays = await service.get_replays(
        track=track,
        country=country,
        race_type=race_type,
        limit=limit
    )
    
    return {
        "count": len(replays),
        "replays": [
            {
                "replay_id": r.replay_id,
                "track": r.track,
                "race_number": r.race_number,
                "race_name": r.race_name,
                "race_date": r.race_date.isoformat(),
                "distance": r.distance,
                "race_type": r.race_type,
                "country": r.country,
                "video_url": r.video_url,
                "embed_url": r.embed_url,
                "thumbnail_url": r.thumbnail_url,
                "source": r.source,
                "duration_seconds": r.duration_seconds,
                "result": {
                    "winner": r.winner,
                    "winner_odds": r.winner_odds,
                    "runner_up": r.runner_up,
                    "runner_up_odds": r.runner_up_odds,
                    "third": r.third,
                    "third_odds": r.third_odds
                },
                "going": r.going,
                "total_runners": r.total_runners,
                "prize_money": r.prize_money,
                "key_moments": r.key_moments,
                "form_insights": r.form_insights
            }
            for r in replays
        ]
    }


@router.get("/replays/{replay_id}")
async def get_replay_detail(replay_id: str):
    """Get detailed information about a specific race replay."""
    service = get_replay_service()
    
    replay = await service.get_replay_by_id(replay_id)
    
    if replay:
        return {
            "replay_id": replay.replay_id,
            "track": replay.track,
            "race_number": replay.race_number,
            "race_name": replay.race_name,
            "race_date": replay.race_date.isoformat(),
            "distance": replay.distance,
            "race_type": replay.race_type,
            "country": replay.country,
            "video_url": replay.video_url,
            "embed_url": replay.embed_url,
            "thumbnail_url": replay.thumbnail_url,
            "source": replay.source,
            "duration_seconds": replay.duration_seconds,
            "result": {
                "winner": replay.winner,
                "winner_odds": replay.winner_odds,
                "runner_up": replay.runner_up,
                "runner_up_odds": replay.runner_up_odds,
                "third": replay.third,
                "third_odds": replay.third_odds
            },
            "going": replay.going,
            "total_runners": replay.total_runners,
            "prize_money": replay.prize_money,
            "key_moments": replay.key_moments,
            "form_insights": replay.form_insights
        }
    
    return {"error": "Replay not found"}


@router.get("/replays/runner/{runner_name}")
async def get_runner_replays(
    runner_name: str,
    limit: int = Query(5, ge=1, le=20)
):
    """Get replays featuring a specific runner for form analysis."""
    service = get_replay_service()
    
    replays = await service.get_runner_replays(runner_name, limit=limit)
    
    return {
        "runner": runner_name,
        "count": len(replays),
        "replays": [
            {
                "replay_id": r.replay_id,
                "track": r.track,
                "race_name": r.race_name,
                "race_date": r.race_date.isoformat(),
                "embed_url": r.embed_url,
                "thumbnail_url": r.thumbnail_url,
                "winner": r.winner,
                "winner_odds": r.winner_odds
            }
            for r in replays
        ]
    }


# =============================================================================
# RACE COUNTDOWN & ALERTS
# =============================================================================

@router.get("/countdown")
def get_race_countdown():
    """
    Get countdown timers for upcoming races.
    Returns races sorted by time with countdown in seconds.
    Useful for setting alerts.
    """
    service = get_racing_service()
    races = service.get_todays_races()
    
    now = datetime.now(timezone.utc)
    
    upcoming = []
    for race in races:
        seconds_until = int((race.post_time - now).total_seconds())
        
        if seconds_until > -300:  # Include races up to 5 mins after post time
            upcoming.append({
                "race_id": race.id,
                "track": race.track,
                "race_number": race.race_number,
                "race_name": race.race_name,
                "post_time": race.post_time.isoformat(),
                "seconds_until_post": max(0, seconds_until),
                "countdown_display": _format_countdown(seconds_until),
                "status": _get_race_status(seconds_until),
                "race_type": race.race_type.value,
                "country": race.country,
                "runners_count": len(race.runners),
                "video": video_service.get_race_video_url(race.track, race.race_number, race.country)
                    if race.race_type == RaceType.HORSE
                    else video_service.get_greyhound_video_url(race.track, race.race_number, race.country)
            })
    
    # Sort by time
    upcoming.sort(key=lambda x: x["seconds_until_post"])
    
    # Group by status
    about_to_start = [r for r in upcoming if r["status"] == "ABOUT_TO_START"]
    starting_soon = [r for r in upcoming if r["status"] == "STARTING_SOON"]
    upcoming_races = [r for r in upcoming if r["status"] == "UPCOMING"]
    
    return {
        "server_time": now.isoformat(),
        "about_to_start": about_to_start,
        "starting_soon": starting_soon,
        "upcoming": upcoming_races[:20],
        "all_races": len(upcoming)
    }


@router.get("/next-races")
def get_next_races(limit: int = Query(5, ge=1, le=20)):
    """
    Get the next N races about to start.
    Perfect for quick monitoring.
    """
    service = get_racing_service()
    races = service.get_todays_races()
    
    now = datetime.now(timezone.utc)
    
    # Filter to future races and sort by post time
    future_races = [
        r for r in races 
        if (r.post_time - now).total_seconds() > -60  # Allow 1 min after post
    ]
    future_races.sort(key=lambda r: r.post_time)
    
    results = []
    for race in future_races[:limit]:
        seconds_until = int((race.post_time - now).total_seconds())
        
        results.append({
            "race_id": race.id,
            "track": race.track,
            "race_number": race.race_number,
            "post_time": race.post_time.isoformat(),
            "countdown": _format_countdown(seconds_until),
            "seconds": max(0, seconds_until),
            "status": _get_race_status(seconds_until),
            "race_type": race.race_type.value,
            "country": race.country,
            "going": race.going.value,
            "distance": race.distance
        })
    
    return {
        "count": len(results),
        "races": results
    }


def _format_countdown(seconds: int) -> str:
    """Format seconds into human-readable countdown."""
    if seconds <= 0:
        return "LIVE NOW"
    elif seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"


def _get_race_status(seconds: int) -> str:
    """Get race status based on countdown."""
    if seconds <= 0:
        return "LIVE"
    elif seconds <= 60:
        return "ABOUT_TO_START"
    elif seconds <= 300:
        return "STARTING_SOON"
    else:
        return "UPCOMING"

