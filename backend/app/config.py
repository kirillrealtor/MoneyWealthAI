"""Centralized, validated configuration.

In production, secrets (DATABASE_URL, JWT secrets, API keys) are injected from
AWS Secrets Manager into the environment at container start. This loader stays
the same; only the source of the env vars changes.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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
    jwt_issuer: str = "financial-advisor"
    jwt_audience: str = "financial-advisor-api"

    app_base_url: str = "http://localhost:3000"
    cookie_domain: str = "localhost"
    default_tenant_id: str = "00000000-0000-0000-0000-000000000001"

    # Security: comma-separated allowlist for Host header (anti host-injection);
    # "*" only acceptable in dev. Max request body size in bytes.
    allowed_hosts: str = "*"
    max_body_bytes: int = 1_000_000
    # Comma-separated CORS origins (credentialed). Empty = no cross-origin.
    cors_origins: str = ""

    # ---- Email ----
    # console = log instead of sending (dev). smtp = any SMTP provider (Gmail,
    # Amazon SES SMTP endpoint, Mailgun, ...). sendgrid = SendGrid HTTP API.
    mail_transport: Literal["console", "smtp", "sendgrid"] = "console"
    mail_from: str = "no-reply@financialadvisor.local"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True  # STARTTLS on port 587 (set False only for :25 relays)
    sendgrid_api_key: str | None = None

    @model_validator(mode="after")
    def _check_mail_transport(self) -> Settings:
        # Fail at startup, not at first signup: a half-configured transport
        # would otherwise surface as users who never get their verify email.
        if self.mail_transport == "smtp" and not self.smtp_host:
            raise ValueError("MAIL_TRANSPORT=smtp requires SMTP_HOST")
        if self.mail_transport == "sendgrid" and not self.sendgrid_api_key:
            raise ValueError("MAIL_TRANSPORT=sendgrid requires SENDGRID_API_KEY")
        return self

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

    # ---- AI advisor ----
    # Provider selection: 'auto' prefers Claude, falls back to Groq if only Groq
    # is configured. Set 'groq' to force the free/cheap path; 'claude' to force Claude.
    advisor_provider: Literal["auto", "claude", "groq"] = "auto"
    anthropic_api_key: str | None = None
    # Groq (OpenAI-compatible, free tier) — good for dev/load-testing the plumbing.
    # NOTE: open models are weaker at compliance framing; run evals before trusting
    # them as the production advisor brain (see docs/PHASE3_PENDING.md).
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    # Default to Opus 4.8 for financial-reasoning quality. At high volume, set
    # ADVISOR_MODEL=claude-sonnet-4-6 to cut cost (~$3/$15 vs $5/$25 per 1M).
    advisor_model: str = "claude-opus-4-8"
    classifier_model: str = "claude-haiku-4-5"  # cheap model for jailbreak checks
    advisor_max_tokens: int = 1500
    advisor_max_tool_rounds: int = 5            # cap agentic loop (cost/runaway guard)
    advisor_history_turns: int = 10             # chat turns loaded for context
    advisor_thinking: bool = False              # adaptive thinking off by default (latency/cost)
    # Per-tier daily token budgets (input+output) enforced before each turn.
    token_budget_free: int = 10_000
    token_budget_plus: int = 100_000
    token_budget_premium: int = 500_000

    @property
    def plaid_configured(self) -> bool:
        return bool(self.plaid_client_id and self.plaid_secret and self.plaid_enc_key)

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def ai_configured(self) -> bool:
        return self.anthropic_configured or self.groq_configured

    def token_budget_for(self, tier: str) -> int:
        return {
            "free": self.token_budget_free,
            "plus": self.token_budget_plus,
            "premium": self.token_budget_premium,
        }.get(tier, self.token_budget_free)

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
