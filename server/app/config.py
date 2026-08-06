from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GITHUB_TOKEN: str = ""  # Optional: GitHub PAT for 5,000 req/hr limit

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()