from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI-compatible API
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_verify_ssl: bool = True

    # JWT
    jwt_secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    # Database
    database_url: str = "sqlite+aiosqlite:///./medical_chatbot.db"

    # WHO ICD-11
    icd_client_id: str = ""
    icd_client_secret: str = ""

    # PubMed
    pubmed_api_key: str = ""

    # App
    app_name: str = "Medical Chatbot"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

