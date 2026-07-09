import pytest
from langgraph.store.memory import InMemoryStore

from careerforge import agent as agent_module
from careerforge.agent import AgentConfig, build_agent


@pytest.fixture
def capture_create_deep_agent(monkeypatch):
    captured = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return "fake-agent"

    monkeypatch.setattr(agent_module, "create_deep_agent", fake_create_deep_agent)
    return captured


def test_state_backend_seeds_agents_md_and_skills(capture_create_deep_agent):
    cfg = AgentConfig(backend="state", use_agents_md=True, use_skills=True, use_subagents=True)
    agent, seed_files = build_agent(cfg)

    assert agent == "fake-agent"
    assert "/context/AGENTS.md" in seed_files
    assert any(p.startswith("/skills/") for p in seed_files)
    assert capture_create_deep_agent["memory"] == ["/context/AGENTS.md"]
    assert capture_create_deep_agent["skills"] == ["/skills/"]
    assert len(capture_create_deep_agent["subagents"]) == 4


def test_store_backend_requires_store():
    cfg = AgentConfig(backend="store", store=None)
    with pytest.raises(ValueError, match="store"):
        build_agent(cfg)


def test_store_backend_passes_store_through(capture_create_deep_agent):
    store = InMemoryStore()
    cfg = AgentConfig(backend="store", store=store)
    build_agent(cfg)
    assert capture_create_deep_agent["store"] is store


def test_store_backend_seeds_agents_md_and_skills_once(capture_create_deep_agent):
    store = InMemoryStore()
    cfg = AgentConfig(backend="store", store=store, use_agents_md=True, use_skills=True)
    build_agent(cfg)

    assert store.get(("careerforge",), "/context/AGENTS.md") is not None
    assert any(
        key.startswith("/skills/")
        for key in (item.key for item in store.search(("careerforge",)))
    )


def test_filesystem_backend_mirrors_context_to_disk(tmp_path, capture_create_deep_agent):
    cfg = AgentConfig(backend="filesystem", filesystem_root=tmp_path)
    build_agent(cfg)

    assert (tmp_path / "context" / "AGENTS.md").exists()
    assert (tmp_path / "skills").is_dir()
    assert any((tmp_path / "skills").rglob("*.md"))


def test_disabling_subagents_and_skills(capture_create_deep_agent):
    cfg = AgentConfig(backend="state", use_agents_md=False, use_skills=False, use_subagents=False)
    build_agent(cfg)
    assert "subagents" not in capture_create_deep_agent
    assert "skills" not in capture_create_deep_agent
    assert "memory" not in capture_create_deep_agent


def test_subagent_names(capture_create_deep_agent):
    cfg = AgentConfig(backend="state")
    build_agent(cfg)
    names = {s["name"] for s in capture_create_deep_agent["subagents"]}
    assert names == {
        "company-researcher", "resume-tailor", "cover-letter-writer", "interview-coach",
    }
