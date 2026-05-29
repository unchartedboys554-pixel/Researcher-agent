# arXiv research agents (writer + reviewer)

Two [Cursor SDK](https://cursor.com/docs/sdk/python) agents tuned for **arXiv preprints**: LaTeX output, integrity guardrails, and a **7-dimension rubric (0–10)** so you can iterate toward submission quality.

> **Honest expectation:** The rubric is an internal quality gate. It does **not** guarantee arXiv acceptance, moderation approval, or a "perfect" paper—you still verify every proof, number, and citation.

## What gets produced

| File | Purpose |
|------|---------|
| `main.tex` | Compilable paper (from `templates/arxiv_main.tex`) |
| `appendix_math.tex` | Formal proofs |
| `references.bib` | BibTeX (`VERIFY` tag if uncertain) |
| `verification_log.md` | Claim → evidence map (required) |
| `arxiv_metadata.md` | Category, keywords, compile notes |
| `review.md` | Rubric scores + blockers |
| `SUBMISSION_CHECKLIST.md` | Human sign-off before upload |

## Setup

```powershell
cd c:\Users\narim\mini-llm\research_agents
pip install -r requirements.txt
$env:CURSOR_API_KEY = "cursor_..."   # https://cursor.com/dashboard/integrations
```

## 1. Fill in your real research (important)

Copy and edit the contribution spec—**this is what separates a honest draft from fabricated results**:

```powershell
copy research_agents\prompts\contribution_default.md my_paper\contribution.md
# Edit: authors, novel claims, REAL numbers, datasets, code URLs
```

## 2. Run the pipeline

From repo root:

```powershell
python research_agents/orchestrate.py `
  --topic "Your paper title" `
  --arxiv-category cs.LG `
  --contribution my_paper\contribution.md `
  --output-dir my_paper `
  --revise --re-review
```

### Flags

| Flag | Meaning |
|------|---------|
| `--arxiv-category cs.LG` | Primary arXiv category |
| `--contribution PATH` | Your verified claims & results (strongly recommended) |
| `--revise` | Writer applies `review.md` |
| `--revise-loops 2` | Multiple revision passes |
| `--re-review` | Reviewer runs again after revisions |
| `--target-score 8` | Revision goal on internal rubric |
| `--writer-only` / `--review-only` | Single agent |

Outputs default to `research_output/` if `--output-dir` is omitted.

## 3. Human steps before arXiv

1. Read `review.md` — fix all **critical blockers**.
2. Clear every `TODO` / `VERIFY` in `verification_log.md` and `main.tex`.
3. Compile locally: `latexmk -pdf main.tex` (from your output folder).
4. Complete `SUBMISSION_CHECKLIST.md`.
5. Upload at [arxiv.org](https://arxiv.org/submit).

## Rubric (in `review.md`)

| Dimension | What it measures |
|-----------|------------------|
| Novelty & positioning | vs. related work |
| Technical correctness | math, algorithms |
| Clarity & structure | abstract, flow |
| Reproducibility | methods, data/code |
| References & attribution | real cites |
| Integrity & arXiv fit | no fabrication; category |
| LaTeX / submission readiness | compiles, metadata |

**Overall** = average of the seven. Labels: `not_ready` → `author_verify_then_submit`.

Aiming for **8+** after `--revise --re-review` with a filled `contribution.md` is realistic for a strong draft; **10** should be rare until you have verified results and proofs yourself.

## Customize

- `prompts/writer.md` / `reviewer.md` / `revise.md` — behavior
- `templates/arxiv_main.tex` — document class, packages

## Academic integrity

You are the author of record. Agents assist drafting and review; institutions may require disclosing AI help. Never submit unchecked citations or experimental numbers.
