"""
Race Replays Service
Provides access to past race video replays for form research.

Free replay sources:
- Racing.com (Australia) - Free replays
- At The Races (UK/Ireland) - Some free replays
- YouTube Racing Channels - Historical race uploads
- HKJC (Hong Kong) - Free replays
"""
import httpx
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class RaceReplay:
    """A race replay video"""
    replay_id: str
    race_id: str
    track: str
    race_number: int
    race_name: str
    race_date: datetime
    distance: str
    race_type: str  # 'horse' or 'greyhound'
    country: str
    
    # Video info
    video_url: str
    embed_url: str
    thumbnail_url: str
    source: str
    duration_seconds: int
    
    # Race result
    winner: str
    winner_odds: float
    runner_up: str
    runner_up_odds: float
    third: Optional[str] = None
    third_odds: Optional[float] = None
    
    # Metadata
    going: str = ""
    total_runners: int = 0
    prize_money: float = 0
    
    # Analysis
    key_moments: List[str] = field(default_factory=list)
    form_insights: List[str] = field(default_factory=list)


class RaceReplayService:
    """
    Service for fetching past race replays.
    Aggregates from multiple free sources.
    """
    
    # Free replay sources
    REPLAY_SOURCES = {
        "racing_com": {
            "name": "Racing.com",
            "base_url": "https://www.racing.com/replays",
            "embed_base": "https://www.racing.com/embed/replay",
            "region": "AU",
            "free": True
        },
        "atr": {
            "name": "At The Races",
            "base_url": "https://www.attheraces.com/replays",
            "embed_base": "https://www.attheraces.com/embed/replay",
            "region": "UK",
            "free": True
        },
        "youtube": {
            "name": "YouTube Racing",
            "base_url": "https://www.youtube.com",
            "region": "global",
            "free": True
        },
        "hkjc": {
            "name": "HKJC Replays",
            "base_url": "https://racing.hkjc.com/racing/video/english/replays",
            "region": "HK",
            "free": True
        },
        "tvg": {
            "name": "TVG Replays",
            "base_url": "https://www.tvg.com/replays",
            "region": "US",
            "free": True
        }
    }
    
    # YouTube channels with race replays
    YOUTUBE_REPLAY_CHANNELS = {
        "racing_com_au": {
            "channel_id": "UCT5vCPP7kq6b3FfS5pLiHkQ",
            "name": "Racing.com Replays",
            "region": "AU"
        },
        "atr_uk": {
            "channel_id": "UCkHSzRAcBvYqrRRN3DrHHmA",
            "name": "At The Races",
            "region": "UK"
        },
        "tvg_us": {
            "channel_id": "UCWR-2F4mZGePLwNvEuOvRLA",
            "name": "TVG",
            "region": "US"
        }
    }
    
    # Demo replay data for when APIs unavailable
    DEMO_REPLAYS = [
        {
            "track": "Cheltenham",
            "race_number": 3,
            "race_name": "Champion Hurdle",
            "race_date": "2026-03-15",
            "distance": "2m",
            "country": "UK",
            "winner": "Constitution Hill",
            "winner_odds": 1.30,
            "runner_up": "State Man",
            "runner_up_odds": 4.50,
            "third": "Honeysuckle",
            "third_odds": 8.00,
            "going": "Soft",
            "total_runners": 8,
            "key_moments": [
                "Constitution Hill jumped fluently throughout",
                "State Man made ground from 2 out",
                "Decisive move at the last fence"
            ],
            "form_insights": [
                "Winner showed class on soft going",
                "Second horse ran career best",
                "Pace was genuine throughout"
            ]
        },
        {
            "track": "Flemington",
            "race_number": 7,
            "race_name": "Melbourne Cup",
            "race_date": "2025-11-04",
            "distance": "3200m",
            "country": "AU",
            "winner": "Without A Fight",
            "winner_odds": 11.00,
            "runner_up": "Vauban",
            "runner_up_odds": 6.50,
            "third": "Soulcombe",
            "third_odds": 15.00,
            "going": "Good",
            "total_runners": 24,
            "key_moments": [
                "Settled midfield early",
                "Made move at 600m mark",
                "Strong finish in final 200m"
            ],
            "form_insights": [
                "Stayer profile suited the 3200m",
                "Handled the firm track well",
                "Jockey timed run perfectly"
            ]
        },
        {
            "track": "Ascot",
            "race_number": 4,
            "race_name": "Gold Cup",
            "race_date": "2025-06-19",
            "distance": "2m4f",
            "country": "UK",
            "winner": "Kyprios",
            "winner_odds": 2.20,
            "runner_up": "Trawlerman",
            "runner_up_odds": 7.00,
            "third": "Coltrane",
            "third_odds": 12.00,
            "going": "Good to Firm",
            "total_runners": 12,
            "key_moments": [
                "Tracked leaders throughout",
                "Launched challenge 2f out",
                "Drew clear in final furlong"
            ],
            "form_insights": [
                "Dominant stayer at his peak",
                "Handles any ground conditions",
                "Tactically versatile"
            ]
        },
        {
            "track": "Churchill Downs",
            "race_number": 11,
            "race_name": "Kentucky Derby",
            "race_date": "2025-05-03",
            "distance": "1m2f",
            "country": "US",
            "winner": "Mystik Dan",
            "winner_odds": 18.00,
            "runner_up": "Sierra Leone",
            "runner_up_odds": 3.50,
            "third": "Forever Young",
            "third_odds": 5.00,
            "going": "Fast",
            "total_runners": 20,
            "key_moments": [
                "Broke well from the gate",
                "Saved ground on the rail",
                "Three-way photo finish"
            ],
            "form_insights": [
                "Showed grit in tight finish",
                "Handled traffic well",
                "Improved for the distance"
            ]
        },
        {
            "track": "Sha Tin",
            "race_number": 8,
            "race_name": "Hong Kong Cup",
            "race_date": "2025-12-08",
            "distance": "2000m",
            "country": "HK",
            "winner": "Romantic Warrior",
            "winner_odds": 2.80,
            "runner_up": "Prognosis",
            "runner_up_odds": 4.20,
            "third": "Titleholder",
            "third_odds": 8.00,
            "going": "Good",
            "total_runners": 12,
            "key_moments": [
                "Settled in midfield",
                "Quickened approaching turn",
                "Held on gamely in final 50m"
            ],
            "form_insights": [
                "Champion quality confirmed",
                "Japanese raiders ran well",
                "Track speed bias present"
            ]
        }
    ]
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(hours=1)
    
    async def get_replays(
        self,
        track: Optional[str] = None,
        country: Optional[str] = None,
        race_type: str = "horse",
        days_back: int = 30,
        limit: int = 20
    ) -> List[RaceReplay]:
        """
        Get race replays with optional filters.
        
        Args:
            track: Filter by track name
            country: Filter by country code (UK, AU, US, HK)
            race_type: 'horse' or 'greyhound'
            days_back: How many days back to search
            limit: Maximum replays to return
        """
        # For now, use demo data - in production would call actual APIs
        replays = self._generate_demo_replays(race_type)
        
        # Apply filters
        if track:
            replays = [r for r in replays if track.lower() in r.track.lower()]
        if country:
            replays = [r for r in replays if r.country == country]
        
        # Sort by date descending
        replays.sort(key=lambda r: r.race_date, reverse=True)
        
        return replays[:limit]
    
    async def get_replay_by_id(self, replay_id: str) -> Optional[RaceReplay]:
        """Get a specific replay by ID."""
        replays = await self.get_replays(limit=100)
        for replay in replays:
            if replay.replay_id == replay_id:
                return replay
        return None
    
    async def get_runner_replays(
        self,
        runner_name: str,
        limit: int = 5
    ) -> List[RaceReplay]:
        """
        Get replays featuring a specific runner.
        Useful for form research.
        """
        # In production, would search API for runner's past races
        # For now, return demo replays
        all_replays = await self.get_replays(limit=100)
        
        # Filter for runner (demo: just return subset)
        return all_replays[:limit]
    
    async def get_track_replays(
        self,
        track: str,
        limit: int = 10
    ) -> List[RaceReplay]:
        """Get recent replays from a specific track."""
        return await self.get_replays(track=track, limit=limit)
    
    def _generate_demo_replays(self, race_type: str = "horse") -> List[RaceReplay]:
        """Generate demo replay data."""
        import random
        
        replays = []
        base_date = datetime.now(timezone.utc)
        
        for i, demo in enumerate(self.DEMO_REPLAYS):
            # Parse demo date
            try:
                race_date = datetime.strptime(demo["race_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                race_date = base_date - timedelta(days=i * 7)
            
            # Generate video URLs based on source
            source = random.choice(["racing_com", "youtube", "atr"])
            
            if source == "youtube":
                video_id = f"demo_{demo['track']}_{demo['race_number']}"
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                embed_url = f"https://www.youtube.com/embed/{video_id}"
            else:
                source_info = self.REPLAY_SOURCES.get(source, self.REPLAY_SOURCES["racing_com"])
                video_url = f"{source_info['base_url']}/{demo['track'].lower()}/{demo['race_date']}/race-{demo['race_number']}"
                embed_url = f"{source_info['embed_base']}/{demo['track'].lower()}/{demo['race_number']}"
            
            replay = RaceReplay(
                replay_id=f"replay_{demo['track'].lower()}_{demo['race_date']}_{demo['race_number']}",
                race_id=f"{demo['track'].lower()}_{demo['race_number']}_{demo['race_date']}",
                track=demo["track"],
                race_number=demo["race_number"],
                race_name=demo["race_name"],
                race_date=race_date,
                distance=demo["distance"],
                race_type=race_type,
                country=demo["country"],
                video_url=video_url,
                embed_url=embed_url,
                thumbnail_url=f"https://via.placeholder.com/640x360?text={demo['track'].replace(' ', '+')}+R{demo['race_number']}",
                source=self.REPLAY_SOURCES.get(source, {}).get("name", "YouTube"),
                duration_seconds=random.randint(90, 240),
                winner=demo["winner"],
                winner_odds=demo["winner_odds"],
                runner_up=demo["runner_up"],
                runner_up_odds=demo["runner_up_odds"],
                third=demo.get("third"),
                third_odds=demo.get("third_odds"),
                going=demo.get("going", "Good"),
                total_runners=demo.get("total_runners", 12),
                prize_money=random.choice([50000, 100000, 250000, 500000, 1000000]),
                key_moments=demo.get("key_moments", []),
                form_insights=demo.get("form_insights", [])
            )
            
            replays.append(replay)
        
        # Add some random additional replays
        tracks_by_country = {
            "UK": ["Cheltenham", "Ascot", "Newmarket", "York", "Aintree"],
            "AU": ["Flemington", "Randwick", "Moonee Valley", "Caulfield"],
            "US": ["Churchill Downs", "Santa Anita", "Belmont", "Saratoga"],
            "HK": ["Sha Tin", "Happy Valley"]
        }
        
        for _ in range(10):
            country = random.choice(list(tracks_by_country.keys()))
            track = random.choice(tracks_by_country[country])
            days_ago = random.randint(1, 60)
            race_date = base_date - timedelta(days=days_ago)
            race_num = random.randint(1, 10)
            
            winners = ["Storm Chaser", "Golden Arrow", "Night Fury", "Swift Spirit", "Thunder Road"]
            runner_ups = ["Silver Lining", "Dark Horse", "Lucky Strike", "Rapid Fire", "Flash Point"]
            
            replay = RaceReplay(
                replay_id=f"replay_{track.lower()}_{race_date.strftime('%Y%m%d')}_{race_num}",
                race_id=f"{track.lower()}_{race_num}_{race_date.strftime('%Y%m%d')}",
                track=track,
                race_number=race_num,
                race_name=f"Race {race_num}",
                race_date=race_date,
                distance=random.choice(["1200m", "1600m", "2000m", "2400m"]),
                race_type=race_type,
                country=country,
                video_url=f"https://www.youtube.com/watch?v=demo_{track}_{race_num}",
                embed_url=f"https://www.youtube.com/embed/demo_{track}_{race_num}",
                thumbnail_url=f"https://via.placeholder.com/640x360?text={track.replace(' ', '+')}+R{race_num}",
                source="YouTube Racing",
                duration_seconds=random.randint(60, 180),
                winner=random.choice(winners),
                winner_odds=round(random.uniform(1.5, 15.0), 2),
                runner_up=random.choice(runner_ups),
                runner_up_odds=round(random.uniform(3.0, 20.0), 2),
                going=random.choice(["Good", "Soft", "Firm", "Heavy"]),
                total_runners=random.randint(6, 16),
                prize_money=random.choice([10000, 25000, 50000, 75000]),
                key_moments=[
                    "Strong start from the gate",
                    "Made move at the turn",
                    "Held on in the final stretch"
                ],
                form_insights=[
                    "Winner showed good form",
                    "Track conditions suited",
                    "Pace scenario worked out"
                ]
            )
            replays.append(replay)
        
        return replays
    
    def get_youtube_embed(self, video_id: str) -> str:
        """Generate YouTube embed URL."""
        return f"https://www.youtube.com/embed/{video_id}?rel=0&showinfo=0"


# Singleton instance
_replay_service: Optional[RaceReplayService] = None


def get_replay_service() -> RaceReplayService:
    """Get the replay service singleton."""
    global _replay_service
    if _replay_service is None:
        _replay_service = RaceReplayService()
    return _replay_service
