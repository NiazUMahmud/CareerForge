---
name: interview-prep
description: Interview preparation skill using the STAR method. Use whenever preparing a candidate for an interview, generating likely interview questions, or drafting talking points tied to their resume and a target job description.
license: MIT
metadata:
  version: "1.0"
  author: careerforge
---

# Interview Prep Skill

Prepare a candidate for interviews by generating likely questions and
STAR-formatted talking points grounded in their actual resume and the target
job description.

## When to Use
- Whenever the task involves interview questions, talking points, or
  interview readiness for a specific job application.

## Supporting Files
- `instructions.md` — the STAR method and question-generation rules.
- `examples.md` — sample question/answer talking points.

## Core Workflow
1. Read the job description and the (tailored) resume for this application.
2. Generate a mix of behavioral, technical/role-specific, and
   company-specific questions likely to come up.
3. For each behavioral question, draft a STAR-formatted talking point using
   a real example from the resume — not a hypothetical.
4. Suggest 3-5 thoughtful questions the candidate should ask the
   interviewer, informed by company research if available.
5. Return this as the `InterviewPrepKit` structured output.

## Quick Standards
- Every talking point must trace back to something actually on the resume.
- Prefer specific, role-relevant questions over generic ones ("Tell me about
  yourself" is fine to include once, but the bulk should be tailored).
