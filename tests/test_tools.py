import pytest

from careerforge import config, tools


@pytest.fixture(autouse=True)
def _clear_caches(monkeypatch):
    config.get_settings.cache_clear()
    tools._client.cache_clear()
    yield
    config.get_settings.cache_clear()
    tools._client.cache_clear()


def test_internet_search_raises_without_tavily_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setattr(config.Settings, "model_config", {**config.Settings.model_config, "env_file": None})
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        tools.internet_search("test query")


def test_internet_search_calls_tavily_client(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    monkeypatch.setattr(config.Settings, "model_config", {**config.Settings.model_config, "env_file": None})

    calls = {}

    class FakeClient:
        def __init__(self, api_key):
            calls["api_key"] = api_key

        def search(self, query, max_results, include_raw_content, topic):
            calls["query"] = query
            return {"results": []}

    monkeypatch.setattr(tools, "TavilyClient", FakeClient)
    result = tools.internet_search("langgraph deep agents")
    assert calls["api_key"] == "fake-key"
    assert calls["query"] == "langgraph deep agents"
    assert result == {"results": []}
