"""The CareerForge deep agent factory.

This is the architectural core of the project: it assembles a
``deepagents.create_deep_agent`` instance from a small, explicit
configuration object. Everything that makes this a *deep* agent rather than
a single LLM call lives here:

- **Planning** — the built-in ``write_todos`` tool (free, comes from
  ``create_deep_agent``).
- **Context offloading** — a virtual file system (backend-dependent) so
  resumes, job descriptions, research notes, and drafts live outside the
  chat context window.
- **Subagents** — isolated child agents for company research, resume
  tailoring, cover-letter drafting, and interview coaching. The interview
  coach and company researcher return validated structured output.
- **Skills** — markdown-defined playbooks (resume tailoring rules, the STAR
  interview method, report writing standards) discovered from
  ``agents_context/skills/``.
- **Swappable backends** — where the virtual file system actually lives:
  in-thread state, real disk, or a durable cross-thread store (used to
  remember a candidate's profile across different job applications).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore

from careerforge.config import AGENTS_MD_PATH, SKILLS_DIR
from careerforge.schemas import CompanyResearch, InterviewPrepKit
from careerforge.tools import internet_search

BackendChoice = Literal["state", "filesystem", "store"]

DEFAULT_SYSTEM_PROMPT = (
    "You are CareerForge, an AI career copilot. Given a candidate's resume "
    "and a target job description, you plan the work with write_todos, "
    "research the company, tailor the resume to the role, draft a cover "
    "letter, and prepare the candidate for interviews. Delegate deep-dive "
    "work to your subagents rather than doing it all yourself. Offload long "
    "drafts and research notes to files instead of repeating them in the "
    "chat. Always ground tailored content in what the candidate actually "
    "provided — never invent experience they don't have."
)


@dataclass
class AgentConfig:
    model: str = "openai:gpt-4.1"
    backend: BackendChoice = "store"
    use_agents_md: bool = True
    use_skills: bool = True
    use_subagents: bool = True
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    checkpointer: BaseCheckpointSaver | None = None
    store: BaseStore | None = None
    filesystem_root: Path | None = None


def _load_agents_md() -> str:
    return AGENTS_MD_PATH.read_text(encoding="utf-8") if AGENTS_MD_PATH.exists() else ""


def _load_skill_seed_files() -> dict:
    """Read every skill file on disk and convert it to in-state file data, so
    backends without disk access (StateBackend, StoreBackend) can still
    discover and read skills."""
    files = {}
    if SKILLS_DIR.exists():
        for f in SKILLS_DIR.rglob("*.md"):
            virtual = "/skills/" + f.relative_to(SKILLS_DIR).as_posix()
            files[virtual] = create_file_data(f.read_text(encoding="utf-8"))
    return files


def _sync_filesystem_context(root: Path) -> None:
    """Mirror AGENTS.md and skills onto real disk under ``root`` so the
    FilesystemBackend's virtual paths ("/context/AGENTS.md", "/skills/...")
    resolve the same way they do for the other two backends."""
    root.mkdir(parents=True, exist_ok=True)
    context_dir = root / "context"
    context_dir.mkdir(exist_ok=True)
    if AGENTS_MD_PATH.exists():
        shutil.copyfile(AGENTS_MD_PATH, context_dir / "AGENTS.md")
    if SKILLS_DIR.exists():
        shutil.copytree(SKILLS_DIR, root / "skills", dirs_exist_ok=True)


def _seed_store_context(store: BaseStore, cfg: AgentConfig) -> None:
    """Seed AGENTS.md/skills into the durable store exactly once — a
    StoreBackend has no disk to fall back on, so unlike StateBackend
    (reseeded every invocation) this only needs to happen the first time."""
    namespace = ("careerforge",)
    if cfg.use_agents_md and store.get(namespace, "/context/AGENTS.md") is None:
        store.put(namespace, "/context/AGENTS.md", create_file_data(_load_agents_md()))
    if cfg.use_skills:
        for path, data in _load_skill_seed_files().items():
            if store.get(namespace, path) is None:
                store.put(namespace, path, data)


def _build_subagents() -> list[dict]:
    return [
        {
            "name": "company-researcher",
            "description": (
                "Researches a target company: what it does, recent news, "
                "culture signals, and concrete talking points a candidate "
                "can use. Use before tailoring a resume or drafting a cover "
                "letter."
            ),
            "system_prompt": (
                "You are a sharp company research analyst. Search the web, "
                "verify claims across sources, and extract facts a job "
                "candidate can actually use — not generic marketing copy."
            ),
            "tools": [internet_search],
            "response_format": CompanyResearch,
        },
        {
            "name": "resume-tailor",
            "description": (
                "Rewrites resume bullet points to match a specific job "
                "description's keywords and priorities, following ATS best "
                "practices. Only reorders/reframes real experience — never "
                "fabricates it."
            ),
            "system_prompt": (
                "You are an expert resume writer. Read the resume-tailoring "
                "skill for the exact rules. Tailor bullets to the job "
                "description's language and keywords without inventing "
                "experience the candidate doesn't have."
            ),
            "tools": [],
        },
        {
            "name": "cover-letter-writer",
            "description": (
                "Drafts a concise, specific cover letter using the tailored "
                "resume and company research. Use after resume-tailor and "
                "company-researcher have produced their output."
            ),
            "system_prompt": (
                "You write concise, specific cover letters (under 350 "
                "words) that reference real facts about the company and the "
                "candidate's real experience. No generic filler."
            ),
            "tools": [],
        },
        {
            "name": "interview-coach",
            "description": (
                "Prepares the candidate for interviews: likely questions, "
                "STAR-method talking points, and questions to ask back. "
                "Returns structured output."
            ),
            "system_prompt": (
                "You are an interview coach. Read the interview-prep skill "
                "for the STAR method. Base talking points on the candidate's "
                "actual resume and the job description."
            ),
            "tools": [],
            "response_format": InterviewPrepKit,
        },
    ]


def build_agent(cfg: AgentConfig) -> tuple[object, dict]:
    """Assemble a deep agent per ``cfg``. Returns ``(agent, seed_files)`` —
    ``seed_files`` must be passed as the ``files`` key of the first
    ``invoke()`` payload for backends without disk access."""
    seed_files: dict = {}
    memory_paths = ["/context/AGENTS.md"] if cfg.use_agents_md else None

    if cfg.backend == "state":
        backend = StateBackend()
        if cfg.use_agents_md:
            seed_files["/context/AGENTS.md"] = create_file_data(_load_agents_md())
        if cfg.use_skills:
            seed_files.update(_load_skill_seed_files())

    elif cfg.backend == "filesystem":
        root = cfg.filesystem_root or Path.cwd()
        _sync_filesystem_context(root)
        backend = FilesystemBackend(root_dir=str(root), virtual_mode=True)

    else:  # store — durable across threads, used for the candidate profile
        if cfg.store is None:
            raise ValueError("AgentConfig.store is required for the 'store' backend")
        _seed_store_context(cfg.store, cfg)
        backend = StoreBackend(store=cfg.store, namespace=lambda rt: ("careerforge",))

    kwargs: dict = dict(
        model=cfg.model,
        tools=[internet_search],
        system_prompt=cfg.system_prompt,
        backend=backend,
    )
    if cfg.checkpointer is not None:
        kwargs["checkpointer"] = cfg.checkpointer
    if cfg.use_subagents:
        kwargs["subagents"] = _build_subagents()
    if cfg.use_skills:
        kwargs["skills"] = ["/skills/"]
    if memory_paths:
        kwargs["memory"] = memory_paths
    if cfg.backend == "store":
        kwargs["store"] = cfg.store

    return create_deep_agent(**kwargs), seed_files
