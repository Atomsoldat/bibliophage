"""
Environment variables:
- VECTOR_DB_URL: PostgreSQL connection string for pgvector (required)
- DOC_DB_URL: MongoDB/FerretDB connection string for document storage (required)
- EMBEDDING_MODEL_NAME: HuggingFace model for embeddings (optional, default: BAAI/bge-large-en-v1.5)
- LOG_LEVEL: Logging level (optional, default: INFO)
"""


# we use pydantic to handle the mapping between env vars and the configuration
# parameters in our application
# https://docs.pydantic.dev/latest/concepts/pydantic_settings/
# by default, env vars are not case sensitive
# https://docs.pydantic.dev/latest/concepts/pydantic_settings/#case-sensitivity

from pydantic import Field, PostgresDsn, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database connection configuration."""

    # PostgreSQL with pgvector for vector embeddings
    # Reads from VECTOR_DB_URL environment variable
    vector_db_url: PostgresDsn = Field(
        description="PostgreSQL connection URL for pgvector (e.g., postgresql+psycopg://user:pass@localhost:5432/db)"
    )

    # MongoDB/FerretDB for document storage
    # Reads from DOC_DB_URL environment variable
    doc_db_url: MongoDsn = Field(
        description="FerretDB/MongoDB connection URL (e.g., mongodb://localhost:27017/)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",  # Optional: for local development convenience
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown environment variables
    )


class EmbeddingConfig(BaseSettings):
    """Embedding model configuration."""

    embedding_model_name: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description="HuggingFace embedding model name",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class LogConfig(BaseSettings):
    """Logging configuration."""

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """Application settings - aggregates all configuration."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    log: LogConfig = Field(default_factory=LogConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance - lazy loaded on first access
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).

    This is the main function other modules should use to access configuration.
    It caches the settings instance so validation only happens once.

    Returns:
        Settings: Application configuration loaded from environment variables

    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
