from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    generation_api_key: str = ""
    generation_api_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    generation_model_name: str = ""
    host: str = "127.0.0.1"
    port: int = 8000


def get_settings() -> Settings:
    return Settings()
