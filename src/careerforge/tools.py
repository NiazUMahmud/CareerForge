"""Custom tools available to the CareerForge deep agent and its subagents."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from tavily import TavilyClient

from careerforge.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _client() -> TavilyClient:
    settings = get_settings()
    if not settings.tavily_api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Add it to your .env to enable web search."
        )
    return TavilyClient(api_key=settings.tavily_api_key)


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict:
    """Search the web. Use this for company research, industry news, salary
    benchmarks, and anything else that requires up-to-date information the
    model doesn't already know."""
    logger.info("internet_search query=%r topic=%s", query, topic)
    return _client().search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
