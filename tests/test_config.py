from careerforge.config import Settings


def test_missing_keys_for_openai_without_key():
    settings = Settings(
        OPENAI_API_KEY=None, GROQ_API_KEY=None, TAVILY_API_KEY=None,
        _env_file=None,
    )
    missing = settings.missing_keys_for("openai:gpt-4.1")
    assert "OPENAI_API_KEY" in missing
    assert "TAVILY_API_KEY" in missing
    assert "GROQ_API_KEY" not in missing


def test_missing_keys_for_groq_without_key():
    settings = Settings(
        OPENAI_API_KEY=None, GROQ_API_KEY=None, TAVILY_API_KEY="x",
        _env_file=None,
    )
    missing = settings.missing_keys_for("groq:qwen/qwen3-32b")
    assert missing == ["GROQ_API_KEY"]


def test_no_missing_keys_when_all_present():
    settings = Settings(
        OPENAI_API_KEY="x", GROQ_API_KEY="x", TAVILY_API_KEY="x",
        _env_file=None,
    )
    assert settings.missing_keys_for("openai:gpt-4.1") == []
