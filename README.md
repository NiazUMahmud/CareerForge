# 🧭 CareerForge

**An AI career copilot, built as a deep agent.**

CareerForge takes a resume and a job description and produces a tailored
resume, a cover letter, and an interview-prep kit — by planning the work,
delegating to specialized subagents, and grounding every claim in what the
candidate actually provided. It's built on [`deepagents`](https://github.com/langchain-ai/deepagents)
(LangGraph) as a hands-on exploration of what makes an agent "deep": planning,
context offloading, subagents, skills, and swappable memory backends.

> Built while learning deep agent architecture — CareerForge is the
> second project in that series, applying the same architectural patterns
> (planning, virtual file system, subagents, skills, backends) to a
> real, opinionated use case instead of a generic research chatbot.

---

## What it does

1. **Paste your resume once.** With the default backend, it's saved to a
   durable profile that survives across every future job application.
2. **Paste a job description** and give the application a short label.
3. Click **Build application kit** — the agent:
   - plans the work (`write_todos`)
   - delegates **company research** to a subagent (structured output: summary, culture notes, recent news, talking points, confidence)
   - delegates **resume tailoring** to a subagent that reorders/reframes real experience to match the job — never fabricates it
   - delegates **cover letter drafting**, grounded in the research + tailored resume
   - delegates **interview prep** to a subagent that returns a structured kit (likely questions, STAR talking points, questions to ask back)
   - saves every artifact as a file you can inspect and download
4. Keep chatting to iterate — "make the cover letter shorter", "focus more on my leadership experience".

## Why a *deep* agent, not a single prompt

A single LLM call struggles with this task: it has to hold the resume, the
job description, company research, and four different writing styles in one
context window, with no way to verify its own work. CareerForge instead uses
four architectural pillars (see [`agents_context/AGENTS.md`](agents_context/AGENTS.md)
for the full internal spec the agent itself is given):

| Pillar | How CareerForge uses it |
|---|---|
| **Planning** | `write_todos` breaks "build an application kit" into research → tailor → draft → prep, and tracks progress |
| **Context offloading** | Resume, job description, and every draft live in a virtual file system (`/profile/`, `/jobs/<slug>/`), not repeated in the chat |
| **Subagents** | `company-researcher`, `resume-tailor`, `cover-letter-writer`, `interview-coach` each get an isolated context and a narrow job |
| **Structured output** | `company-researcher` and `interview-coach` return validated Pydantic objects (`CompanyResearch`, `InterviewPrepKit`), not free text |
| **Skills** | Markdown playbooks (`resume-tailoring`, `interview-prep`, `report-writer`) encode the *exact* method — ATS keyword rules, the STAR method — so behavior is auditable and editable without touching code |
| **Swappable backends** | `StateBackend` (ephemeral), `FilesystemBackend` (real disk), `StoreBackend` (durable, cross-thread profile) — same agent code, different persistence |

---

## Architecture

```
                         ┌───────────────────────────┐
                         │      CareerForge Agent    │
                         │  create_deep_agent        │
                         │  (LangGraph)              │
                         └──────────┬────────────────┘
                                    │
      ┌───────────────┬─────────────┴────────┬───────────────────────┐
      ▼               ▼                      ▼                       ▼
┌───────────┐  ┌────────────────┐   ┌───────────────────────┐   ┌───────────────┐
│ Planning  │  │ Virtual files  │   │ Subagents             │   │ Custom tool   │
│ write_    │  │ /profile/      │   │ company-researcher →  │   │ internet_     │
│ todos     │  │ /jobs/<slug>/  │   │   CompanyResearch     │   │ search        │
│           │  │                │   │ resume-tailor         │   │ (Tavily)      │
│           │  │                │   │ cover-letter-writer   │   │               │
│           │  │                │   │ interview-coach →     │   │               │
│           │  │                │   │   InterviewPrepKit    │   │               │
└───────────┘  └────────────────┘   └───────────────────────┘   └───────────────┘
```

### Project layout

```
CareerForge/
├── src/careerforge/
│   ├── config.py      # typed Settings (pydantic-settings), single source of env config
│   ├── schemas.py      # CompanyResearch, InterviewPrepKit — structured subagent output
│   ├── tools.py        # internet_search (Tavily)
│   ├── agent.py         # build_agent(): the deep agent factory (backends, subagents, skills)
│   ├── rendering.py    # pure message-formatting helpers (unit-testable, no Streamlit)
│   └── app.py            # Streamlit UI
├── agents_context/
│   ├── AGENTS.md         # architecture + operating rules, loaded into the agent's context
│   └── skills/
│       ├── resume-tailoring/
│       ├── interview-prep/
│       └── report-writer/
├── tests/                # pytest unit tests
└── .github/workflows/ci.yml
```

---

## Getting started

### Prerequisites
- Python 3.11+
- An API key for at least one model provider (OpenAI or Groq)
- A [Tavily](https://tavily.com/) API key (used by `company-researcher` for web search)

### Install

```bash
git clone <this-repo-url> CareerForge
cd CareerForge
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in your keys
```

### Run

```bash
streamlit run src/careerforge/app.py
```

Open the local URL Streamlit prints, paste a resume and a job description in
the sidebar/main panel, and click **Build application kit**.

### Test

```bash
pytest --cov=careerforge
ruff check .
```

---

## Backend choice — why it matters

| Backend | Where files live | Use it when |
|---|---|---|
| `StoreBackend` (default) | LangGraph `Store`, keyed by namespace | You want your resume saved once and reused across every job application |
| `StateBackend` | In-thread LangGraph state | You just want to try it out with no persistence |
| `FilesystemBackend` | Real files under `./workspace/` | You want to inspect/version the generated resumes and cover letters directly on disk |

All three backends see the *same* virtual paths (`/profile/resume.md`,
`/jobs/<slug>/...`) — `build_agent()` mirrors `agents_context/AGENTS.md` and
the skills onto whichever backend is active so the agent's context is
identical regardless of where the bytes actually live.

---

## Configuration

All environment variables are read once, in `src/careerforge/config.py`, into
a validated `Settings` object — nothing else calls `os.getenv` directly.

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | one of these two | Model provider |
| `GROQ_API_KEY` | one of these two | Model provider |
| `TAVILY_API_KEY` | yes | Web search for company research |
| `CAREERFORGE_MODEL` | no | Default model string (`provider:model`) |
| `CAREERFORGE_LOG_LEVEL` | no | Logging verbosity |

---

## Honesty guarantee

Every subagent prompt and skill explicitly instructs the agent to **never
fabricate experience**. If a job description asks for something the resume
doesn't support, the agent is instructed to flag the gap in its summary
instead of inventing a bullet point. This is enforced at the prompt/skill
level (see `agents_context/skills/resume-tailoring/examples.md` for the
exact expected behavior on a gap) — review generated content before sending
it, as with any LLM output.

---

## Roadmap

- [ ] PDF resume upload/parsing (currently plain text/markdown paste)
- [ ] Multi-model comparison (run the same job through two models, diff the output)
- [ ] Export application kit as a single PDF
- [ ] Durable store backed by Postgres/Redis instead of `InMemoryStore` for real persistence across restarts

## Acknowledgements

Built on [`deepagents`](https://github.com/langchain-ai/deepagents) and
[LangGraph](https://github.com/langchain-ai/langgraph). Architecturally
inspired by Claude Code, Deep Research, and Manus-style long-horizon agents.

## License

MIT — see [LICENSE](LICENSE).
