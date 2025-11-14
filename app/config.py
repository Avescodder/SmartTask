from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-3.5-turbo", alias="OPENAI_MODEL")
    embedding_model: str = Field("text-embedding-3-small", alias="EMBEDDING_MODEL")
    
    # PostgreSQL
    postgres_user: str = Field(..., alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_host: str = Field("postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    
    # Redis
    redis_host: str = Field("redis", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_ttl: int = Field(3600, alias="REDIS_TTL")
    
    # App
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    # RAG
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 3
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()