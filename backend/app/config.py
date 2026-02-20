"""Environment variable configuration for Shadow Ops backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Amazon Nova 2 Lite (inference placeholder)
    nova_2_lite_api_key: str = ""
    nova_2_lite_region: str = "us-east-1"
    nova_2_lite_endpoint: str = ""

    # Amazon Nova Act (agent execution placeholder)
    nova_act_api_key: str = ""
    nova_act_region: str = "us-east-1"
    nova_act_endpoint: str = ""

    # Logging
    log_level: str = "INFO"

    # Inference: mock (deterministic from session) or real (Nova 2 Lite)
    nova_mode: str = "mock"


settings = Settings()
