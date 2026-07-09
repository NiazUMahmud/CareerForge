---
name: resume-tailoring
description: Resume tailoring skill. Use whenever rewriting or tailoring resume bullets to match a specific job description. Applies ATS keyword matching and bullet-rewriting rules without fabricating experience.
license: MIT
metadata:
  version: "1.0"
  author: careerforge
---

# Resume Tailoring Skill

Tailor an existing resume to a specific job description — reorder,
re-emphasize, and re-word real experience so it matches what the job
description is looking for. Never invent skills, titles, tools, or metrics
the candidate didn't provide.

## When to Use
- Whenever a job description and a resume are both available and the task
  is to produce a tailored version of the resume.

## Supporting Files
- `instructions.md` — the exact bullet-rewriting method and ATS keyword rules.
- `examples.md` — before/after bullet examples.

## Core Workflow
1. Read the job description and extract its top 8-10 keywords/requirements
   (skills, tools, seniority signals, domain terms).
2. Read the candidate's resume from `/profile/resume.md`.
3. For each resume bullet, check whether it can honestly be reworded to
   surface a matching keyword. Reorder bullets so the most relevant ones per
   role come first.
4. Keep the resume's factual content unchanged — same employers, titles,
   dates, and metrics. Only wording, emphasis, and order change.
5. Flag any requirement in the job description that the resume doesn't
   support, instead of quietly fabricating it.

## Quick Standards
- Bullets start with a strong past-tense verb, include a quantifiable result
  where the source resume has one.
- Do not exceed the original resume's length.
- Save the tailored resume as markdown to `/jobs/<slug>/resume.md`.
