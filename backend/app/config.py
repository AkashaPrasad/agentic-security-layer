"""
Pydantic Settings — environment-driven application configuration.

All settings are loaded from environment variables (or .env file).
This module is imported by database.py, Alembic env.py, and the FastAPI app factory.
"""

from urllib.parse import quote as _urlquote

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "agentshield"
    app_env: str = "development"
    app_debug: bool = True
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    log_level: str = "info"

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_red_team"
    postgres_user: str = "postgres"
    postgres_password: str = "changeme"
    database_url: str | None = None

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_url: str | None = None

    # --- Celery ---
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_worker_concurrency: int = 4

    # --- Security ---
    secret_key: str = "changeme-generate-a-64-char-random-string"
    encryption_key: str = ""
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # --- Rate Limiting ---
    firewall_enabled: bool = False
    firewall_rate_limit_per_minute: int = 100
    api_rate_limit_per_minute: int = 60

    # --- LLM Defaults ---
    llm_judge_model: str = "gpt-4o"
    llm_judge_temperature: float = 0.0
    llm_judge_max_tokens: int = 1024
    llm_request_timeout: int = 30

    # --- Experiment Defaults ---
    experiment_batch_size: int = 10
    experiment_batch_concurrency: int = 3
    experiment_max_retries: int = 3
    experiment_retry_delay: int = 5
    experiment_cost_budget_usd: float = 25.0
    experiment_revenue_per_test_usd: float = 0.05
    experiment_strategy_memory_ttl_seconds: int = 1_209_600
    experiment_strategy_memory_max_items: int = 40
    experiment_strict_strategy_failures: bool = True
    experiment_strategy_chain_enabled: bool = True
    experiment_strategy_chain_depth: int = 4
    experiment_stale_timeout_seconds: int = 900
    experiment_default_seed: int = 1337
    judge_fallback_enabled: bool = True

    # --- Provider Pool Quota Controls ---
    provider_pool_requests_per_minute: int = 120
    provider_pool_tokens_per_minute: int = 120000
    provider_pool_max_rate_limit_retries: int = 2
    provider_pool_base_retry_delay_seconds: float = 0.5
    provider_pool_max_retry_delay_seconds: float = 20.0
    provider_pool_failover_on_transient_errors: bool = True
    provider_pool_cache_enabled: bool = True
    provider_pool_cache_ttl_seconds: int = 1800
    provider_pool_cache_max_entries: int = 5000

    # --- Custom Plugins ---
    custom_plugins_enabled: bool = True
    custom_plugin_paths: str = ""

    # --- Database Pool ---
    database_pool_size: int = 2
    database_max_overflow: int = 3

    # --- Monad / AgentShield ---
    monad_rpc_url: str = "https://testnet-rpc.monad.xyz"
    monad_chain_id: int = 10143
    monad_facilitator_url: str = "https://x402-facilitator.molandak.org"
    pay_to_address: str = ""
    testnet_usdc_address: str = "0x534b2f3A21130d7a60830c2Df862319e593943A3"
    scan_price_usdc: str = "0.10"
    erc8004_identity_registry: str = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
    erc8004_reputation_registry: str = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"

    # --- Sarvam AI ---
    sarvam_api_key: str = ""
    sarvam_api_url: str = "https://api.sarvam.ai/v1"

    @property
    def async_database_url(self) -> str:
        """Construct async database URL from components if not explicitly set.

        Strips ``?ssl=require`` when present — SSL is handled via an explicit
        ``ssl.SSLContext`` passed in ``connect_args`` (see database.py).
        """
        if self.database_url:
            url = self.database_url
            # Remove ssl query params — asyncpg uses connect_args ssl context
            import re as _re
            url = _re.sub(r'[?&]ssl(mode)?=require', '', url)
            return url
        return (
            f"postgresql+asyncpg://{_urlquote(self.postgres_user, safe='')}:{_urlquote(self.postgres_password, safe='')}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync database URL for Alembic migrations."""
        base = (
            f"postgresql+asyncpg://{_urlquote(self.postgres_user, safe='')}:{_urlquote(self.postgres_password, safe='')}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.postgres_requires_ssl:
            base += "?sslmode=require"
        return base

    @property
    def postgres_requires_ssl(self) -> bool:
        """Infer whether the configured Postgres host should use SSL."""
        import ipaddress

        host = self.postgres_host.strip().lower()
        if not host:
            return False
        if host in {"localhost", "postgres", "host.docker.internal"} or host.endswith(".local"):
            return False

        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            # Bare service names are usually local Docker/Kubernetes hosts.
            return "." in host

        return not (ip.is_loopback or ip.is_private)

    @property
    def redis_connection_url(self) -> str:
        """Construct Redis URL from components if not explicitly set."""
        if self.redis_url:
            return self.redis_url
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


def get_settings() -> Settings:
    """Factory function for settings. Can be overridden in tests via FastAPI dependency injection."""
    return Settings()


# Module-level singleton for convenience imports.
settings = get_settings()
