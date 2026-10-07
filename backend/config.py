from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    demo_mode: bool = True
    database_url: str = "sqlite:///./data/jalayatra.db"
    ai_provider: str = "local"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    stt_url: str = ""
    stt_api_key: str = ""
    stt_provider: str = "auto"
    provider_timeout_seconds: float = 8
    tracking_provider: str = "demo"
    tracking_url: str = ""
    tracking_api_key: str = ""
    weather_provider: str = "demo"
    weather_url: str = ""
    weather_api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    auth_secret: str = ""
    enforce_certificates: bool = True


settings = Settings()
