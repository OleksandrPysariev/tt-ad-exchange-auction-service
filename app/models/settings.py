from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, BaseModel, PostgresDsn
from pydantic_settings import SettingsConfigDict, BaseSettings


class GeneralSettings(BaseModel):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    env: Literal["local", "dev", "pytest", "stg", "prod"] = "local"
    api_v1_str: str = "/api/v1"
    allow_credentials: bool = True
    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    data_file_path: Path = Field(default=Path.cwd() / "data.json", description="Path to the auction data JSON file")


class FastAPISettings(BaseModel):
    title: str = "Ad Exchange Auction"
    version: str = "0.0.0"
    docs_url: str | None = "/api/docs"
    openapi_url: str | None = "/openapi.json"
    redoc_url: str | None = "/api/redoc"
    root_path: str = ""


class DBSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "aea_user"
    password: str = "123"
    name: str = "aea_db"
    max_overflow: int = 25
    echo: bool = False

    @property
    def async_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            path=self.name,
        )


class RedisSettings(BaseModel):
    startup_nodes: list[dict[str, str | int]] = [{"host": "localhost", "port": 6379}]
    default_ttl: int = 3600


class Settings(BaseSettings):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    fastapi: FastAPISettings = Field(default_factory=FastAPISettings)
    db: DBSettings = DBSettings()
    redis: RedisSettings = RedisSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
