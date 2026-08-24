"""
Central application settings.

Everything configurable lives here and is sourced from environment
variables (.env in dev). Nothing secret is hardcoded — this module
is the single place the rest of the app reads config from.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "shipora"

    # JWT
    jwt_secret: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "notifications@shipora.app"

    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    # cached so we parse the .env file once per process
    return Settings()
