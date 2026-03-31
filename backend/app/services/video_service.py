"""
Live Racing Video Service
Provides free live video streams from various racing sources.
"""
import httpx
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


class VideoSource:
    """Represents a video streaming source"""
    def __init__(
        self,
        source_id: str,
        name: str,
        url: str,
        embed_url: Optional[str] = None,
        stream_type: str = "iframe",  # iframe, hls, youtube, direct
        is_live: bool = True,
        thumbnail: Optional[str] = None,
        region: str = "global"
    ):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.embed_url = embed_url or url
        self.stream_type = stream_type
        self.is_live = is_live
        self.thumbnail = thumbnail
        self.region = region


class RacingVideoService:
    """
    Service to provide live racing video streams.
    Aggregates free streams from multiple sources.
    """
    
    # Free racing video sources
    VIDEO_SOURCES = {
        # Australian Racing - Racing.com (completely free)
        "racing_com": {
            "name": "Racing.com",
            "base_url": "https://www.racing.com",
            "embed_base": "https://www.racing.com/embed/vision",
            "stream_type": "iframe",
            "region": "AU",
            "tracks": [
                "flemington", "moonee_valley", "caulfield", "randwick", 
                "rosehill", "eagle_farm", "doomben", "morphettville",
                "sandown", "cranbourne", "pakenham", "ballarat"
            ]
        },
        # UK Racing - At The Races (some free content)
        "atr": {
            "name": "At The Races",
            "base_url": "https://www.attheraces.com",
            "embed_base": "https://www.attheraces.com/embed/live",
            "stream_type": "iframe",
            "region": "UK",
            "tracks": [
                "ascot", "cheltenham", "aintree", "epsom", "goodwood",
                "newmarket", "york", "doncaster", "sandown", "kempton"
            ]
        },
        # Sky Racing (Australia) - Via free streams
        "sky_racing": {
            "name": "Sky Racing",
            "base_url": "https://www.skyracing.com.au",
            "embed_base": "https://www.skyracing.com.au/live",
            "stream_type": "iframe",
            "region": "AU"
        },
        # YouTube Racing Streams (various channels)
        "youtube_racing": {
            "name": "YouTube Racing",
            "base_url": "https://www.youtube.com",
            "stream_type": "youtube",
            "region": "global",
            "channels": {
                "uk": "UCkHSzRAcBvYqrRRN3DrHHmA",  # Racing UK
                "au": "UCT5vCPP7kq6b3FfS5pLiHkQ",  # Racing.com
                "us": "UCWR-2F4mZGePLwNvEuOvRLA",  # TVG
                "hk": "UCL8NcJkH1CBfeMJggY7cPVQ",  # HKJC
            }
        },
        # RPGTV (UK - Free)
        "rpgtv": {
            "name": "RPGTV",
            "base_url": "https://www.rpgtv.com",
            "embed_base": "https://www.rpgtv.com/embed/live",
            "stream_type": "iframe",
            "region": "UK"
        },
        # Hong Kong Jockey Club (free live)
        "hkjc": {
            "name": "HKJC",
            "base_url": "https://racing.hkjc.com",
            "embed_base": "https://racing.hkjc.com/racing/video/english/live",
            "stream_type": "iframe",
            "region": "HK"
        },
        # TVG (US - some free)
        "tvg": {
            "name": "TVG",
            "base_url": "https://www.tvg.com",
            "embed_base": "https://www.tvg.com/live",
            "stream_type": "iframe",
            "region": "US"
        }
    }
    
    # YouTube Live Racing Streams (free, embeddable)
    YOUTUBE_LIVE_STREAMS = {
        "uk_racing": {
            "channel_id": "UCkHSzRAcBvYqrRRN3DrHHmA",
            "name": "UK Racing Live",
            "region": "UK"
        },
        "racing_com_au": {
            "channel_id": "UCT5vCPP7kq6b3FfS5pLiHkQ",
            "name": "Racing.com Australia",
            "region": "AU"
        },
        "tvg_us": {
            "channel_id": "UCWR-2F4mZGePLwNvEuOvRLA",
            "name": "TVG Horse Racing",
            "region": "US"
        },
        "thoroughbred_daily": {
            "channel_id": "UCQGaXxaV0KH8WdPFUfZBQYw",
            "name": "Thoroughbred Daily News",
            "region": "US"
        },
        "hk_jockey_club": {
            "channel_id": "UCL8NcJkH1CBfeMJggY7cPVQ",
            "name": "Hong Kong Jockey Club",
            "region": "HK"
        }
    }
    
    def __init__(self):
        self._cached_streams: Dict[str, Any] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
    
    async def get_live_streams(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all available live racing streams"""
        streams = []
        
        # Add regional streams
        for source_id, source in self.VIDEO_SOURCES.items():
            if region and source.get("region") != region and source.get("region") != "global":
                continue
            
            stream = {
                "id": source_id,
                "name": source["name"],
                "url": source["base_url"],
                "embed_url": source.get("embed_base", source["base_url"]),
                "stream_type": source.get("stream_type", "iframe"),
                "region": source.get("region", "global"),
                "is_live": True,
                "thumbnail": f"https://via.placeholder.com/320x180?text={source['name'].replace(' ', '+')}"
            }
            streams.append(stream)
        
        # Add YouTube streams (always available)
        for yt_id, yt_source in self.YOUTUBE_LIVE_STREAMS.items():
            if region and yt_source.get("region") != region:
                continue
                
            stream = {
                "id": f"youtube_{yt_id}",
                "name": yt_source["name"],
                "url": f"https://www.youtube.com/channel/{yt_source['channel_id']}/live",
                "embed_url": f"https://www.youtube.com/embed/live_stream?channel={yt_source['channel_id']}",
                "stream_type": "youtube",
                "region": yt_source.get("region", "global"),
                "is_live": True,
                "thumbnail": f"https://img.youtube.com/vi/default/hqdefault.jpg"
            }
            streams.append(stream)
        
        return streams
    
    def get_race_video_url(
        self, 
        track: str, 
        race_number: int,
        region: str = "AU"
    ) -> Dict[str, Any]:
        """
        Get video URL for a specific race.
        Returns embed URL and metadata.
        """
        track_lower = track.lower().replace(" ", "_")
        
        # Determine best source for region
        if region == "AU":
            source = self.VIDEO_SOURCES["racing_com"]
            embed_url = f"{source['embed_base']}/{track_lower}/race/{race_number}"
            backup_url = f"https://www.youtube.com/embed/live_stream?channel=UCT5vCPP7kq6b3FfS5pLiHkQ"
        elif region == "UK":
            source = self.VIDEO_SOURCES["atr"]
            embed_url = f"{source['embed_base']}/{track_lower}"
            backup_url = f"https://www.youtube.com/embed/live_stream?channel=UCkHSzRAcBvYqrRRN3DrHHmA"
        elif region == "US":
            source = self.VIDEO_SOURCES["tvg"]
            embed_url = f"{source['embed_base']}/{track_lower}"
            backup_url = f"https://www.youtube.com/embed/live_stream?channel=UCWR-2F4mZGePLwNvEuOvRLA"
        elif region == "HK":
            source = self.VIDEO_SOURCES["hkjc"]
            embed_url = source["embed_base"]
            backup_url = f"https://www.youtube.com/embed/live_stream?channel=UCL8NcJkH1CBfeMJggY7cPVQ"
        else:
            # Default to YouTube
            embed_url = f"https://www.youtube.com/embed/live_stream?channel=UCT5vCPP7kq6b3FfS5pLiHkQ"
            backup_url = embed_url
            source = {"name": "YouTube Racing", "stream_type": "youtube"}
        
        return {
            "embed_url": embed_url,
            "backup_url": backup_url,
            "source": source.get("name", "Unknown"),
            "stream_type": source.get("stream_type", "iframe"),
            "is_live": True,
            "track": track,
            "race_number": race_number,
            "region": region
        }
    
    def get_youtube_embed(self, video_id: str = None, channel_id: str = None) -> str:
        """Generate YouTube embed URL"""
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1"
        elif channel_id:
            return f"https://www.youtube.com/embed/live_stream?channel={channel_id}&autoplay=1&mute=1"
        return ""
    
    async def check_stream_availability(self, url: str) -> bool:
        """Check if a stream URL is currently available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Stream check failed for {url}: {e}")
            return False
    
    def get_greyhound_video_url(
        self,
        track: str,
        race_number: int,
        region: str = "AU"
    ) -> Dict[str, Any]:
        """Get video URL for greyhound racing"""
        track_lower = track.lower().replace(" ", "_")
        
        if region == "AU":
            # Sky Racing handles greyhounds in Australia
            embed_url = f"https://www.skyracing.com.au/live/greyhounds/{track_lower}"
            backup_url = "https://www.youtube.com/embed/live_stream?channel=UCT5vCPP7kq6b3FfS5pLiHkQ"
        elif region == "UK":
            # RPGTV for UK greyhounds
            embed_url = f"https://www.rpgtv.com/embed/live"
            backup_url = "https://www.youtube.com/embed/live_stream?channel=UCkHSzRAcBvYqrRRN3DrHHmA"
        else:
            embed_url = "https://www.youtube.com/embed/live_stream?channel=UCT5vCPP7kq6b3FfS5pLiHkQ"
            backup_url = embed_url
        
        return {
            "embed_url": embed_url,
            "backup_url": backup_url,
            "source": "Sky Racing" if region == "AU" else "RPGTV",
            "stream_type": "iframe",
            "is_live": True,
            "track": track,
            "race_number": race_number,
            "region": region,
            "race_type": "greyhound"
        }


# Global instance
video_service = RacingVideoService()
