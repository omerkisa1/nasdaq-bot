from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    finnhub_api_key: str = ""
    gemini_api_key: str = ""
    redis_url: str = "redis://redis:6379/0"

    scan_interval_sec: int = 300
    monitor_interval_sec: int = 10
    gemini_max_calls_per_scan: int = 10
    gemini_symbol_cooldown_sec: int = 1800
    universe_price_min: float = 0.5
    universe_price_max: float = 20.0
    universe_min_vol: int = 100_000
    prefilter_min_rvol: float = 2.0

    default_account_size: float = 1000.0
    default_risk_percent: float = 1.0
    max_active_cards: int = 5
    liquidity_cap_pct: float = 2.0

    news_watch_interval_sec: int = 60
    news_watch_top_n: int = 30
    news_reaction_window_sec: int = 120
    news_reaction_min_pct: float = 2.0
    news_gemini_max_per_hour: int = 10
    manual_analysis_cooldown_sec: int = 300


settings = Settings()
