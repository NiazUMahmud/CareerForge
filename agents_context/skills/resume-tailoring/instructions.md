# Resume Tailoring — Detailed Instructions

## 1. Keyword Extraction
From the job description, pull out:
- Required hard skills / tools (e.g. "Kubernetes", "SQL", "Figma")
- Soft-skill signals (e.g. "cross-functional", "ownership", "mentorship")
- Seniority cues (e.g. "5+ years", "lead", "IC")
- Domain vocabulary (e.g. "fintech", "B2B SaaS", "healthcare compliance")

## 2. Bullet Rewriting Method
For each existing bullet:
1. Identify the underlying achievement (what changed, by how much, using what).
2. Check if any extracted keyword genuinely applies to that achievement.
3. If yes, rework the bullet to lead with the action verb and surface the
   keyword naturally — do not keyword-stuff.
4. If no honest match exists, leave the bullet as-is or de-prioritize its
   position; do not force a connection that isn't true.

Formula: `<Strong verb> + <what you did> + <tool/skill used> + <quantified result>`

## 3. Reordering
- Within each role, put the 1-3 bullets most relevant to this job first.
- Across roles, the most recent and most relevant role stays at the top —
  don't reorder employment history itself, only bullet order within roles.

## 4. Gaps
If the job description asks for something not evidenced anywhere in the
resume (e.g. a specific certification or technology), note it explicitly in
your summary back to the user — e.g. "Note: the JD asks for AWS certification,
which isn't reflected in your resume. Consider mentioning it if you have
informal experience, or leave this gap for the interview to address."

## 5. Output Format
Save the tailored resume as clean markdown (headings per section: Summary,
Experience, Skills, Education) to `/jobs/<slug>/resume.md`.
