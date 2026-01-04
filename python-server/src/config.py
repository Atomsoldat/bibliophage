"""Module for configuration handling based on environment variables.

Environment variables:
- VECTOR_DB_URL: PostgreSQL connection string for pgvector (required)
- DOC_DB_URL: MongoDB/FerretDB connection string for document storage (required)
- EMBEDDING_MODEL_NAME: HuggingFace model for embeddings (optional, default: BAAI/bge-large-en-v1.5)
- LOG_LEVEL: Logging level (optional, default: INFO)
- OLLAMA_URL: Ollama API URL (optional, default: http://localhost:11435)
- OLLAMA_DEFAULT_MODEL: Default Ollama model (optional, default: mistral)
- OLLAMA_TEMPERATURE: LLM temperature 0.0-1.0 (optional, default: 0.7)
- OLLAMA_MAX_TOKENS: Maximum tokens to generate (optional, default: 2048)
- OLLAMA_TIMEOUT: Request timeout in seconds (optional, default: 120)
"""


# we use pydantic to handle the mapping between env vars and the configuration
# parameters in our application
# https://docs.pydantic.dev/latest/concepts/pydantic_settings/
# by default, env vars are not case sensitive
# https://docs.pydantic.dev/latest/concepts/pydantic_settings/#case-sensitivity

from pydantic import Field, MongoDsn, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database connection configuration."""

    # PostgreSQL with pgvector for vector embeddings
    # Reads from VECTOR_DB_URL environment variable
    vector_db_url: PostgresDsn = Field(
        description="PostgreSQL connection URL for pgvector (e.g., postgresql+psycopg://user:pass@localhost:5432/db)",
    )

    # MongoDB/FerretDB for document storage
    # Reads from DOC_DB_URL environment variable
    doc_db_url: MongoDsn = Field(
        description="FerretDB/MongoDB connection URL (e.g., mongodb://localhost:27017/)",
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


class OllamaConfig(BaseSettings):
    """Ollama LLM configuration."""

    ollama_url: str = Field(
        default="http://localhost:11435",
        description="Ollama API URL",
    )

    ollama_default_model: str = Field(
        default="mistral",
        description="Default Ollama model",
    )

    ollama_temperature: float = Field(
        default=0.7,
        description="LLM temperature (0.0-1.0). Higher = more creative",
    )

    ollama_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens to generate",
    )

    ollama_timeout: int = Field(
        default=120,
        description="Request timeout in seconds",
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
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


## Python is interpreted, so the stuff using other stuff has to come later
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern).

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
