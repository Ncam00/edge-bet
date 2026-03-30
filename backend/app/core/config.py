from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "EdgeBet API"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # Odds API
    odds_api_key: str = ""
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"

    # ML
    model_min_ev_threshold: float = 0.03  # 3% minimum EV to show bet
    model_min_confidence: float = 0.52    # minimum model probability

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
