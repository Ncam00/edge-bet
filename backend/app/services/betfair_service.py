"""
Betfair Exchange API Integration
Provides real-time live racing odds from Betfair Exchange.

Betfair Exchange API is FREE for:
- UK Horse Racing
- Australian Horse Racing  
- Irish Racing
- Greyhound Racing

API Documentation: https://developer.betfair.com/

To use:
1. Register at https://developer.betfair.com/
2. Create an app key (free)
3. Set BETFAIR_USERNAME, BETFAIR_PASSWORD, BETFAIR_APP_KEY in .env
"""
import httpx
import asyncio
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class BetfairMarketStatus(str, Enum):
    INACTIVE = "INACTIVE"
    OPEN = "OPEN"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class BetfairEventType(str, Enum):
    HORSE_RACING = "7"
    GREYHOUND_RACING = "4339"


@dataclass
class BetfairRunner:
    """A runner in a Betfair market"""
    selection_id: int
    runner_name: str
    handicap: float
    sort_priority: int
    status: str
    # Exchange prices
    back_price: float  # Best price to back (bet on)
    back_size: float   # Amount available at back price
    lay_price: float   # Best price to lay (bet against)
    lay_size: float    # Amount available at lay price
    last_traded_price: Optional[float] = None
    total_matched: float = 0.0
    # Derived values
    implied_probability: float = 0.0
    
    def __post_init__(self):
        if self.back_price > 1:
            self.implied_probability = 1 / self.back_price


@dataclass
class BetfairMarket:
    """A Betfair racing market"""
    market_id: str
    market_name: str
    market_start_time: datetime
    total_matched: float
    status: BetfairMarketStatus
    event_name: str
    event_venue: str
    country_code: str
    runners: List[BetfairRunner] = field(default_factory=list)
    
    # Computed fields
    race_number: int = 0
    distance: str = ""
    race_type: str = "horse"


class BetfairService:
    """
    Service for fetching live racing odds from Betfair Exchange API.
    
    The Betfair API uses:
    - Login API for authentication
    - Betting API for market data (JSON-RPC)
    """
    
    # API Endpoints
    LOGIN_URL = "https://identitysso.betfair.com/api/login"
    BETTING_URL = "https://api.betfair.com/exchange/betting/rest/v1.0"
    
    # Racing event type IDs
    EVENT_TYPES = {
        "horse": "7",
        "greyhound": "4339"
    }
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        app_key: Optional[str] = None
    ):
        self.username = username
        self.password = password
        self.app_key = app_key
        self.session_token: Optional[str] = None
        self.session_expiry: Optional[datetime] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 30  # 30 seconds cache
        
    async def login(self) -> bool:
        """Authenticate with Betfair and get session token."""
        if not all([self.username, self.password, self.app_key]):
            logger.warning("Betfair credentials not configured")
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.LOGIN_URL,
                    headers={
                        "X-Application": self.app_key,
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "username": self.username,
                        "password": self.password
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "SUCCESS":
                        self.session_token = data.get("token")
                        self.session_expiry = datetime.now(timezone.utc) + timedelta(hours=4)
                        logger.info("Betfair login successful")
                        return True
                    else:
                        logger.error(f"Betfair login failed: {data.get('error')}")
                        
        except Exception as e:
            logger.error(f"Betfair login error: {e}")
            
        return False
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid session token."""
        if self.session_token and self.session_expiry:
            if datetime.now(timezone.utc) < self.session_expiry:
                return True
        return await self.login()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "X-Application": self.app_key or "",
            "X-Authentication": self.session_token or "",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _api_call(self, operation: str, params: Dict) -> Optional[Dict]:
        """Make a Betfair API call."""
        if not await self._ensure_authenticated():
            logger.warning("Not authenticated with Betfair")
            return None
            
        url = f"{self.BETTING_URL}/{operation}/"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json={"filter": params} if operation != "listMarketBook" else params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Betfair API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Betfair API call failed: {e}")
            
        return None
    
    async def get_racing_events(
        self,
        event_type: str = "horse",
        country_codes: List[str] = None
    ) -> List[Dict]:
        """
        Get upcoming racing events.
        
        Args:
            event_type: 'horse' or 'greyhound'
            country_codes: Filter by country (e.g., ['GB', 'IE', 'AU'])
        """
        event_type_id = self.EVENT_TYPES.get(event_type, "7")
        
        filter_params = {
            "eventTypeIds": [event_type_id],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": datetime.now(timezone.utc).isoformat(),
                "to": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            }
        }
        
        if country_codes:
            filter_params["marketCountries"] = country_codes
            
        result = await self._api_call("listEvents", filter_params)
        
        if result:
            return [e.get("event", {}) for e in result]
        return []
    
    async def get_racing_markets(
        self,
        event_type: str = "horse",
        country_codes: List[str] = None,
        hours_ahead: int = 4
    ) -> List[BetfairMarket]:
        """
        Get racing markets with runners.
        
        Args:
            event_type: 'horse' or 'greyhound'
            country_codes: Filter by country
            hours_ahead: How many hours ahead to look
        """
        cache_key = f"markets_{event_type}_{country_codes}_{hours_ahead}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cached_time).seconds < self._cache_ttl:
                return cached_data
        
        event_type_id = self.EVENT_TYPES.get(event_type, "7")
        
        filter_params = {
            "eventTypeIds": [event_type_id],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": datetime.now(timezone.utc).isoformat(),
                "to": (datetime.now(timezone.utc) + timedelta(hours=hours_ahead)).isoformat()
            }
        }
        
        if country_codes:
            filter_params["marketCountries"] = country_codes
        
        # Get market catalogue (list of markets with runners)
        catalogue_result = await self._api_call("listMarketCatalogue", {
            "filter": filter_params,
            "maxResults": "100",
            "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME", "COMPETITION"]
        })
        
        if not catalogue_result:
            return []
        
        markets = []
        market_ids = []
        market_info = {}
        
        for cat in catalogue_result:
            market_id = cat.get("marketId")
            market_ids.append(market_id)
            
            event = cat.get("event", {})
            
            # Parse venue from event name (e.g., "3:30 Cheltenham")
            event_name = event.get("name", "")
            venue = event.get("venue", event_name.split(" ")[-1] if " " in event_name else event_name)
            
            market_info[market_id] = {
                "name": cat.get("marketName", ""),
                "start_time": cat.get("marketStartTime", ""),
                "event_name": event_name,
                "venue": venue,
                "country": cat.get("event", {}).get("countryCode", "GB"),
                "runners": {
                    r.get("selectionId"): {
                        "name": r.get("runnerName", ""),
                        "handicap": r.get("handicap", 0),
                        "sort_priority": r.get("sortPriority", 0)
                    }
                    for r in cat.get("runners", [])
                }
            }
        
        if not market_ids:
            return []
        
        # Get live prices for all markets
        price_result = await self._api_call("listMarketBook", {
            "marketIds": market_ids[:20],  # Limit to 20 markets per call
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_TRADED"],
                "virtualise": True
            }
        })
        
        if not price_result:
            return []
        
        for book in price_result:
            market_id = book.get("marketId")
            info = market_info.get(market_id, {})
            
            try:
                start_time = datetime.fromisoformat(info.get("start_time", "").replace("Z", "+00:00"))
            except:
                start_time = datetime.now(timezone.utc)
            
            runners = []
            for runner_book in book.get("runners", []):
                selection_id = runner_book.get("selectionId")
                runner_info = info.get("runners", {}).get(selection_id, {})
                
                # Get best back and lay prices
                ex = runner_book.get("ex", {})
                back_prices = ex.get("availableToBack", [])
                lay_prices = ex.get("availableToLay", [])
                traded = ex.get("tradedVolume", [])
                
                back_price = back_prices[0].get("price", 0) if back_prices else 0
                back_size = back_prices[0].get("size", 0) if back_prices else 0
                lay_price = lay_prices[0].get("price", 0) if lay_prices else 0
                lay_size = lay_prices[0].get("size", 0) if lay_prices else 0
                
                last_traded = traded[0].get("price") if traded else None
                total_matched = sum(t.get("size", 0) for t in traded)
                
                runners.append(BetfairRunner(
                    selection_id=selection_id,
                    runner_name=runner_info.get("name", f"Runner {selection_id}"),
                    handicap=runner_info.get("handicap", 0),
                    sort_priority=runner_info.get("sort_priority", 0),
                    status=runner_book.get("status", "ACTIVE"),
                    back_price=back_price,
                    back_size=back_size,
                    lay_price=lay_price,
                    lay_size=lay_size,
                    last_traded_price=last_traded,
                    total_matched=total_matched
                ))
            
            # Sort runners by sort priority
            runners.sort(key=lambda r: r.sort_priority)
            
            # Parse race number from market name if possible
            market_name = info.get("name", "")
            race_num = 0
            for part in market_name.split():
                if part.startswith("R") and part[1:].isdigit():
                    race_num = int(part[1:])
                    break
            
            markets.append(BetfairMarket(
                market_id=market_id,
                market_name=market_name,
                market_start_time=start_time,
                total_matched=book.get("totalMatched", 0),
                status=BetfairMarketStatus(book.get("status", "OPEN")),
                event_name=info.get("event_name", ""),
                event_venue=info.get("venue", ""),
                country_code=info.get("country", "GB"),
                runners=runners,
                race_number=race_num,
                race_type=event_type
            ))
        
        # Sort by start time
        markets.sort(key=lambda m: m.market_start_time)
        
        # Cache results
        self._cache[cache_key] = (markets, datetime.now(timezone.utc))
        
        return markets
    
    async def get_market_prices(self, market_id: str) -> Optional[BetfairMarket]:
        """Get live prices for a specific market."""
        result = await self._api_call("listMarketBook", {
            "marketIds": [market_id],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_TRADED"],
                "virtualise": True
            }
        })
        
        if result and len(result) > 0:
            # Convert to BetfairMarket
            book = result[0]
            runners = []
            
            for rb in book.get("runners", []):
                ex = rb.get("ex", {})
                back = ex.get("availableToBack", [{}])[0] if ex.get("availableToBack") else {}
                lay = ex.get("availableToLay", [{}])[0] if ex.get("availableToLay") else {}
                traded = ex.get("tradedVolume", [])
                
                runners.append(BetfairRunner(
                    selection_id=rb.get("selectionId"),
                    runner_name=f"Selection {rb.get('selectionId')}",
                    handicap=rb.get("handicap", 0),
                    sort_priority=rb.get("sortPriority", 0),
                    status=rb.get("status", "ACTIVE"),
                    back_price=back.get("price", 0),
                    back_size=back.get("size", 0),
                    lay_price=lay.get("price", 0),
                    lay_size=lay.get("size", 0),
                    last_traded_price=traded[0].get("price") if traded else None,
                    total_matched=sum(t.get("size", 0) for t in traded)
                ))
            
            return BetfairMarket(
                market_id=market_id,
                market_name="",
                market_start_time=datetime.now(timezone.utc),
                total_matched=book.get("totalMatched", 0),
                status=BetfairMarketStatus(book.get("status", "OPEN")),
                event_name="",
                event_venue="",
                country_code="",
                runners=runners
            )
        
        return None


# =============================================================================
# Demo/Fallback Mode (when Betfair credentials not configured)
# =============================================================================

class BetfairDemoService:
    """
    Demo service that generates realistic Betfair-style odds data.
    Used when Betfair API credentials are not configured.
    """
    
    import random
    
    DEMO_TRACKS = {
        "GB": ["Cheltenham", "Ascot", "Newmarket", "York", "Aintree", "Epsom", "Goodwood", "Sandown"],
        "IE": ["Leopardstown", "The Curragh", "Fairyhouse", "Punchestown"],
        "AU": ["Flemington", "Randwick", "Moonee Valley", "Caulfield", "Eagle Farm"]
    }
    
    DEMO_RUNNERS = [
        "Thunder Bolt", "Swift Shadow", "Golden Star", "Desert Storm", "Blue Diamond",
        "Silver Arrow", "Red Phoenix", "Dark Knight", "Ocean Wave", "Fire Dragon",
        "Wind Dancer", "Storm Rider", "Lucky Charm", "Golden Eagle", "Black Beauty"
    ]
    
    def __init__(self):
        import random
        self.random = random
    
    async def get_racing_markets(
        self,
        event_type: str = "horse",
        country_codes: List[str] = None,
        hours_ahead: int = 4
    ) -> List[BetfairMarket]:
        """Generate demo racing markets."""
        import random
        
        markets = []
        countries = country_codes or ["GB", "IE", "AU"]
        base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        
        for country in countries:
            tracks = self.DEMO_TRACKS.get(country, ["Demo Track"])
            
            for track in tracks[:2]:  # 2 tracks per country
                for race_num in range(1, random.randint(6, 9)):
                    start_time = base_time + timedelta(minutes=30 * race_num + random.randint(0, 15))
                    
                    # Generate runners with realistic odds
                    num_runners = 6 if event_type == "greyhound" else random.randint(8, 14)
                    
                    # Generate raw probabilities that sum to ~100% (with overround for realism)
                    raw_probs = sorted([random.random() ** 1.5 for _ in range(num_runners)], reverse=True)
                    total = sum(raw_probs)
                    
                    runners = []
                    for i, prob in enumerate(raw_probs):
                        # Normalize and add overround (5-8%)
                        real_prob = prob / total
                        overround = 1.05 + random.uniform(0, 0.03)
                        back_prob = real_prob * overround
                        
                        back_price = round(max(1.01, min(1000, 1 / back_prob)), 2)
                        # Lay price is slightly higher (spread)
                        lay_price = round(back_price * (1 + random.uniform(0.01, 0.03)), 2)
                        
                        # Volume correlates with probability (favorites get more money)
                        base_volume = 50000 * real_prob
                        back_size = round(base_volume * random.uniform(0.8, 1.2), 0)
                        lay_size = round(back_size * random.uniform(0.3, 0.7), 0)
                        
                        runner_name = random.choice(self.DEMO_RUNNERS) + f" {i+1}"
                        
                        runners.append(BetfairRunner(
                            selection_id=1000000 + i,
                            runner_name=runner_name,
                            handicap=0,
                            sort_priority=i + 1,
                            status="ACTIVE",
                            back_price=back_price,
                            back_size=back_size,
                            lay_price=lay_price,
                            lay_size=lay_size,
                            last_traded_price=back_price,
                            total_matched=round(back_size * back_price * random.uniform(1, 5), 0)
                        ))
                    
                    markets.append(BetfairMarket(
                        market_id=f"demo_{country}_{track}_{race_num}",
                        market_name=f"R{race_num} {start_time.strftime('%H:%M')} {track}",
                        market_start_time=start_time,
                        total_matched=sum(r.total_matched for r in runners),
                        status=BetfairMarketStatus.OPEN,
                        event_name=f"{start_time.strftime('%H:%M')} {track}",
                        event_venue=track,
                        country_code=country,
                        runners=runners,
                        race_number=race_num,
                        race_type=event_type
                    ))
        
        markets.sort(key=lambda m: m.market_start_time)
        return markets


# =============================================================================
# Factory function
# =============================================================================

_betfair_service: Optional[BetfairService] = None
_demo_service: Optional[BetfairDemoService] = None


def get_betfair_service() -> BetfairService | BetfairDemoService:
    """
    Get the Betfair service instance.
    Returns demo service if credentials not configured.
    """
    global _betfair_service, _demo_service
    
    # Try to get credentials from settings
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        username = getattr(settings, 'betfair_username', None)
        password = getattr(settings, 'betfair_password', None)
        app_key = getattr(settings, 'betfair_app_key', None)
        
        if all([username, password, app_key]):
            if _betfair_service is None:
                _betfair_service = BetfairService(username, password, app_key)
            return _betfair_service
    except Exception as e:
        logger.warning(f"Could not load Betfair credentials: {e}")
    
    # Fall back to demo service
    if _demo_service is None:
        _demo_service = BetfairDemoService()
    
    logger.info("Using Betfair demo mode (set BETFAIR_* env vars for live data)")
    return _demo_service
