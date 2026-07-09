"""Centralized, validated configuration for CareerForge.

All environment variables are read exactly once, here, and exposed as a
typed ``Settings`` object. Nothing else in the codebase should call
``os.getenv`` directly — that keeps configuration auditable and makes
missing-key errors surface early with a clear message instead of as a
confusing failure deep inside a subagent call.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
CONTEXT_DIR = ROOT_DIR / "agents_context"
SKILLS_DIR = CONTEXT_DIR / "skills"
AGENTS_MD_PATH = CONTEXT_DIR / "AGENTS.md"


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    default_model: str = Field(default="openai:gpt-4.1", alias="CAREERFORGE_MODEL")
    log_level: str = Field(default="INFO", alias="CAREERFORGE_LOG_LEVEL")

    def missing_keys_for(self, model: str) -> list[str]:
        """Return which required API keys are missing for the given model string."""
        missing = []
        if model.startswith("openai") and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if model.startswith("groq") and not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_logging(level: str | None = None) -> None:
    logging.basicConfig(
        level=level or get_settings().log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
