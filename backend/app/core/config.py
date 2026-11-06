from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mysql_root_password: str = "root123"
    mysql_database: str = "liveops"
    mysql_user: str = "liveops"
    mysql_password: str = "liveops123"

    postgres_db: str = "agent"
    postgres_user: str = "agent"
    postgres_password: str = "agent123"

    database_url: str = "mysql+pymysql://liveops:liveops123@localhost:3306/liveops?charset=utf8mb4"
    postgres_url: str = "postgresql+psycopg2://agent:agent123@localhost:5432/agent"
    redis_url: str = "redis://localhost:6379/0"

    milvus_host: str = "localhost"
    milvus_port: int = 19530

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"

    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: str = ""
    llm_main_model: str = "qwen-max"
    llm_light_model: str = "qwen-turbo"
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = 1024

    jwt_secret: str = "change-me-in-prod"
    jwt_expire_minutes: int = 1440

    coupon_daily_budget: float = 5000.0
    max_danmaku_per_minute: int = 60
    danmaku_rate_limit: int = 20
    ingest_token: str = "liveops-ingest-2026"
    log_level: str = "INFO"
    demo_mode: bool = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
