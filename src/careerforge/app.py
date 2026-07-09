"""CareerForge — Streamlit UI.

Run with:  streamlit run src/careerforge/app.py

Workflow:
1. Paste your resume once in the sidebar and click "Save profile" — with the
   StoreBackend this persists across every future job application (new
   thread, even a new browser session against the same store).
2. Paste a job description, give the application a short slug (e.g. the
   company name), and click "Build application kit".
3. The deep agent plans the work, delegates to its subagents (company
   research, resume tailoring, cover letter drafting, interview prep), and
   returns a tailored resume, cover letter, and structured interview prep
   kit — all saved as files you can inspect and download.
4. Keep chatting in the box below to iterate ("make the cover letter
   shorter", "focus more on my leadership experience", ...).
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import streamlit as st
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from careerforge.agent import AgentConfig, build_agent
from careerforge.config import ROOT_DIR, configure_logging, get_settings
from careerforge.rendering import extract_text, render_files, render_steps
from careerforge.resilience import call_with_retry

configure_logging()
settings = get_settings()

WORKSPACE_DIR = ROOT_DIR / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="CareerForge", page_icon="🧭", layout="wide")
st.title("🧭 CareerForge — AI Career Copilot")
st.caption(
    "Planning • Company research • Resume tailoring • Cover letters • "
    "Interview prep — powered by a deepagents deep agent with subagents, "
    "skills, and a persistent candidate profile."
)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "role"


# --- session state init ------------------------------------------------------
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = MemorySaver()
if "store" not in st.session_state:
    st.session_state.store = InMemoryStore()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []
if "profile_saved" not in st.session_state:
    st.session_state.profile_saved = False

STORE_NAMESPACE = ("careerforge",)

# --- sidebar: configuration + candidate profile ------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    model = st.selectbox(
        "Model",
        [
            "openai:gpt-4.1-mini",
            "openai:gpt-4.1",
            "openai:gpt-5.4",
            "groq:llama-3.3-70b-versatile",
            "groq:qwen/qwen3-32b",
        ],
        index=0,
        help=(
            "gpt-4.1-mini is the safest default on a new/low-tier OpenAI "
            "account: this agent's per-turn token demand (planner + up to 4 "
            "subagents) regularly exceeds gpt-4.1's 30k TPM limit at the "
            "lowest usage tier, but gpt-4.1-mini gets a much higher ceiling "
            "for the same spend. Groq's free tier has low per-model TPM "
            "limits too — qwen/qwen3-32b caps around 6k TPM; "
            "llama-3.3-70b-versatile is the safer Groq choice."
        ),
    )

    backend_label = st.radio(
        "Backend (where files & profile live)",
        [
            "StoreBackend (persistent profile, recommended)",
            "StateBackend (in-thread only, ephemeral)",
            "FilesystemBackend (real disk under ./workspace)",
        ],
        help=(
            "StoreBackend keeps your resume and past applications available "
            "across every new job / new thread. StateBackend forgets "
            "everything once the thread ends. FilesystemBackend writes real "
            "files under ./workspace for you to inspect."
        ),
    )
    backend = {
        "StoreBackend (persistent profile, recommended)": "store",
        "StateBackend (in-thread only, ephemeral)": "state",
        "FilesystemBackend (real disk under ./workspace)": "filesystem",
    }[backend_label]

    with st.expander("Advanced"):
        use_subagents = st.checkbox("Subagents", value=True)
        use_skills = st.checkbox("Skills", value=True)
        use_agents_md = st.checkbox("AGENTS.md context", value=True)

    st.divider()
    st.subheader("👤 Your profile")
    resume_text = st.text_area(
        "Resume (plain text or markdown)", height=200,
        placeholder="Paste your resume here...",
        key="resume_text",
    )
    if st.button("💾 Save profile", use_container_width=True, disabled=backend != "store"):
        st.session_state.store.put(
            STORE_NAMESPACE, "/profile/resume.md",
            create_file_data(resume_text),
        )
        st.session_state.profile_saved = True
        st.success("Profile saved — it will persist across new job threads.")
    if backend != "store":
        st.caption("Saved profiles require the StoreBackend.")
    elif st.session_state.store.get(STORE_NAMESPACE, "/profile/resume.md"):
        st.caption("✅ A profile is currently saved in this session's store.")

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("🆕 New application", use_container_width=True,
                   help="Fresh conversation. With StoreBackend your saved "
                        "profile and past applications are still there."):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.history = []
        st.rerun()
    if col2.button("🗑️ Reset all", use_container_width=True):
        for k in ("checkpointer", "store", "thread_id", "history", "profile_saved"):
            st.session_state.pop(k, None)
        st.rerun()

    missing = settings.missing_keys_for(model)
    for key in missing:
        st.error(f"{key} missing from .env")

# --- main panel: job application inputs --------------------------------------
st.subheader("📋 New job application")
jd_col, meta_col = st.columns([3, 1])
job_description = jd_col.text_area(
    "Job description", height=160, placeholder="Paste the job description here...",
)
job_label = meta_col.text_input("Company / role label", placeholder="e.g. Acme-Backend-Eng")
build_clicked = meta_col.button("🚀 Build application kit", type="primary", use_container_width=True)

cfg = AgentConfig(
    model=model,
    backend=backend,
    use_agents_md=use_agents_md,
    use_skills=use_skills,
    use_subagents=use_subagents,
    checkpointer=st.session_state.checkpointer,
    store=st.session_state.store if backend == "store" else None,
    filesystem_root=WORKSPACE_DIR if backend == "filesystem" else None,
)
cfg_key = (model, backend, use_agents_md, use_skills, use_subagents)
if st.session_state.get("cfg_key") != cfg_key:
    st.session_state.agent, st.session_state.seed_files = build_agent(cfg)
    st.session_state.cfg_key = cfg_key


def _prep_job_context(slug: str) -> dict:
    """Make the resume + job description available to the agent according to
    the active backend, and return any extra files to seed at invoke time."""
    extra_files: dict = {}
    if backend == "store":
        st.session_state.store.put(
            STORE_NAMESPACE, f"/jobs/{slug}/job_description.md",
            create_file_data(job_description),
        )
        if resume_text and not st.session_state.store.get(STORE_NAMESPACE, "/profile/resume.md"):
            st.session_state.store.put(
                STORE_NAMESPACE, "/profile/resume.md", create_file_data(resume_text),
            )
    elif backend == "filesystem":
        job_dir = WORKSPACE_DIR / "jobs" / slug
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "job_description.md").write_text(job_description, encoding="utf-8")
        (WORKSPACE_DIR / "profile").mkdir(exist_ok=True)
        (WORKSPACE_DIR / "profile" / "resume.md").write_text(resume_text or "", encoding="utf-8")
    else:  # state — nothing persists, so seed both files on this invocation
        extra_files["/profile/resume.md"] = create_file_data(resume_text or "")
        extra_files[f"/jobs/{slug}/job_description.md"] = create_file_data(job_description)
    return extra_files


_EXCLUDE_EXACT = {"/context/AGENTS.md"}
_EXCLUDE_PREFIXES = ("/skills/",)


def _is_output_file(path: str) -> bool:
    return path not in _EXCLUDE_EXACT and not path.startswith(_EXCLUDE_PREFIXES)


def _collect_output_files() -> dict:
    """Gather generated documents from wherever the active backend actually
    stores them. ``result["files"]`` (LangGraph state) only reflects
    StateBackend — StoreBackend keeps files in the external store, and
    FilesystemBackend writes them straight to real disk, so both need to be
    read back from their own source instead."""
    if backend == "store":
        # BaseStore.search() defaults to limit=10 — AGENTS.md + the 9 skill
        # files alone fill that quota, silently hiding every job document.
        return {
            item.key: item.value
            for item in st.session_state.store.search(STORE_NAMESPACE, limit=1000)
            if _is_output_file(item.key)
        }
    if backend == "filesystem":
        files = {}
        for path in WORKSPACE_DIR.rglob("*.md"):
            rel = "/" + path.relative_to(WORKSPACE_DIR).as_posix()
            if _is_output_file(rel):
                files[rel] = {"content": path.read_text(encoding="utf-8")}
        return files
    return {}  # state backend is read from result["files"] directly


# --- replay chat history ------------------------------------------------------
for role, text, steps, files in st.session_state.history:
    with st.chat_message(role):
        if steps:
            render_steps(steps)
        st.markdown(text)
        if files:
            render_files(files)


def run_turn(prompt: str, extra_files: dict) -> None:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.history.append(("user", prompt, None, None))

    payload = {"messages": [{"role": "user", "content": prompt}]}
    seed = {**st.session_state.seed_files, **extra_files}
    if seed:
        payload["files"] = seed

    config = {
        "configurable": {"thread_id": st.session_state.thread_id},
        "recursion_limit": 100,
    }

    with st.chat_message("assistant"):
        status = st.empty()
        with st.spinner("🧭 Planning, researching, and drafting..."):

            def _invoke():
                return st.session_state.agent.invoke(payload, config=config)

            def _on_retry(attempt: int, wait: float) -> None:
                status.info(
                    f"⏳ Rate limit hit — retrying in {wait:.0f}s "
                    f"(attempt {attempt}/3)..."
                )

            try:
                result = call_with_retry(_invoke, max_retries=3, on_retry=_on_retry)
            except Exception as e:  # noqa: BLE001 — surface any agent error to the UI
                st.error(f"Agent error: {e}")
                st.stop()
        status.empty()

        all_msgs = result["messages"]
        turn_start = max(
            (i for i, m in enumerate(all_msgs) if getattr(m, "type", "") == "human"),
            default=0,
        )
        new_msgs = all_msgs[turn_start + 1:]

        render_steps(new_msgs)
        answer = extract_text(all_msgs[-1].content) or "*(no text response)*"
        st.markdown(answer)

        if backend == "state":
            files = {p: d for p, d in result.get("files", {}).items() if p not in seed}
        else:
            files = _collect_output_files()
        render_files(files)

    st.session_state.history.append(("assistant", answer, new_msgs, files))


if build_clicked:
    if not job_description.strip():
        st.warning("Paste a job description first.")
    else:
        slug = slugify(job_label or "role")
        extra_files = _prep_job_context(slug)
        kit_prompt = (
            f"Build me a complete application kit for this role (label: {job_label or slug}).\n\n"
            f"Job description:\n{job_description}\n\n"
            "Steps: research the company, tailor my resume to this specific job, "
            "draft a cover letter, and prepare interview prep. My resume is "
            f"available at /profile/resume.md. Save the tailored resume to "
            f"/jobs/{slug}/resume.md, the cover letter to /jobs/{slug}/cover_letter.md, "
            f"and the interview prep to /jobs/{slug}/interview_prep.md."
        )
        run_turn(kit_prompt, extra_files)

if prompt := st.chat_input("Ask CareerForge anything about this application..."):
    run_turn(prompt, {})
