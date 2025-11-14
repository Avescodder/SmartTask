from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from pathlib import Path

def find_dotenv(filename=".env", max_levels=5) -> str | None:
    """
    Ищет файл .env в текущем каталоге и до max_levels уровней выше.
    Возвращает полный путь к файлу или None, если не найден.
    """
    current = Path(__file__).parent
    for _ in range(max_levels):
        candidate = current / filename
        if candidate.exists():
            return str(candidate)
        current = current.parent
    return None

ENV_FILE_PATH = find_dotenv()
if ENV_FILE_PATH is None:
    raise FileNotFoundError(".env file not found in project hierarchy")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
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