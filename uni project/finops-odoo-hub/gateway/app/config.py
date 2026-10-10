from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinOps Odoo Hub"
    environment: str = "development"
    database_url: str = "sqlite:///./finops.db"
    provider_mode: str = "mock"  # mock | opencost
    opencost_base_url: str = "http://localhost:9003"
    opencost_window: str = "30d"
    currency: str = "USD"
    api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FINOPS_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
