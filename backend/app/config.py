"""Centralized, validated configuration.

In production, secrets (DATABASE_URL, JWT secrets, API keys) are injected from
AWS Secrets Manager into the environment at container start. This loader stays
the same; only the source of the env vars changes.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["development", "test", "production"] = "development"
    port: int = 3000
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"

    # App connects as the non-owner app_user role (RLS enforced).
    database_url: str
    # Migrations run as the owner/superuser (creates roles, FORCE RLS, DDL).
    # Falls back to database_url if unset (e.g. single-role environments).
    migration_database_url: str | None = None
    redis_url: str

    jwt_access_secret: str = Field(min_length=32)
    jwt_refresh_secret: str = Field(min_length=32)
    access_token_ttl: int = 900
    refresh_token_ttl: int = 2_592_000
    bcrypt_rounds: int = Field(default=12, ge=10, le=15)

    app_base_url: str = "http://localhost:3000"
    cookie_domain: str = "localhost"
    default_tenant_id: str = "00000000-0000-0000-0000-000000000001"

    # Security: comma-separated allowlist for Host header (anti host-injection);
    # "*" only acceptable in dev. Max request body size in bytes.
    allowed_hosts: str = "*"
    max_body_bytes: int = 1_000_000
    # Comma-separated CORS origins (credentialed). Empty = no cross-origin.
    cors_origins: str = ""

    mail_transport: Literal["console", "ses", "sendgrid"] = "console"
    mail_from: str = "no-reply@financialadvisor.local"

    # Cloudflare Turnstile (bot/captcha). Disabled by default so local dev and
    # tests run without a key; enable + set the secret in staging/production.
    turnstile_enabled: bool = False
    turnstile_secret_key: str | None = None
    # Require captcha on login only after this many recent failures (step-up).
    login_captcha_after_fails: int = 3

    rate_limit_general_per_min: int = 100
    rate_limit_ai_per_min: int = 10

    # ---- Plaid (banking data) ----
    plaid_env: Literal["sandbox", "development", "production"] = "sandbox"
    plaid_client_id: str | None = None
    plaid_secret: str | None = None
    plaid_products: str = "transactions"  # comma-separated: transactions,auth,investments,liabilities
    plaid_country_codes: str = "US"
    plaid_redirect_uri: str | None = None
    plaid_webhook_url: str | None = None
    # AES-256-GCM key (base64 of 32 raw bytes) used to encrypt Plaid access
    # tokens at rest. In production this is sourced from KMS/Secrets Manager.
    plaid_enc_key: str | None = None
    plaid_enc_key_version: int = 1

    @property
    def plaid_configured(self) -> bool:
        return bool(self.plaid_client_id and self.plaid_secret and self.plaid_enc_key)

    @property
    def plaid_base_url(self) -> str:
        return {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }[self.plaid_env]

    @property
    def plaid_products_list(self) -> list[str]:
        return [p.strip() for p in self.plaid_products.split(",") if p.strip()]

    @property
    def plaid_country_codes_list(self) -> list[str]:
        return [c.strip() for c in self.plaid_country_codes.split(",") if c.strip()]

    @property
    def is_prod(self) -> bool:
        return self.env == "production"

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()] or ["*"]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from env


settings = get_settings()
