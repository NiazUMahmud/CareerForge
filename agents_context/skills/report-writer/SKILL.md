---
name: report-writer
description: Report writing skill applied after completing an application kit (or any substantive request). Saves a structured markdown summary of what was researched, tailored, and produced so the candidate has one file to review everything.
license: MIT
metadata:
  version: "1.0"
  author: careerforge
---

# Report Writer Skill

After producing an application kit (or any substantive multi-step answer),
write a single structured markdown summary tying together what was
researched, what was produced, and where each file lives.

## When to Use
- ALWAYS after finishing a full application-kit request.
- When the user explicitly asks for a summary of what was done.
- Skip for trivial exchanges (greetings, single clarifying questions).

## Supporting Files
- `instructions.md` — the exact report template and file-naming rules.
- `examples.md` — a sample report.

## Core Workflow
1. Complete the actual work first (research, tailored resume, cover letter,
   interview prep).
2. Read `instructions.md` for the report template.
3. Fill in the template referencing the real files you wrote.
4. Save the report to `/jobs/<slug>/application_kit_summary.md`.
5. Tell the user the summary was saved and where.

## Quick Standards
- The report is self-contained — readable without the chat transcript.
- Only reference files and facts that were actually produced; no invented claims.
