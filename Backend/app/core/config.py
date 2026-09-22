from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SmartSearch API"
    app_version: str = "0.1.0"
    debug: bool = True


settings = Settings()