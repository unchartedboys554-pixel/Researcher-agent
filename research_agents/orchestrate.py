#!/usr/bin/env python3
"""
arXiv-oriented research pipeline: Writer (LaTeX + math) -> Reviewer (rubric) -> optional revisions.

Requires CURSOR_API_KEY and: pip install -r research_agents/requirements.txt
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from cursor_sdk import Agent, CursorAgentError, LocalAgentOptions

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
TEMPLATES = ROOT / "templates"
DEFAULT_OUTPUT = "research_output"
DEFAULT_CATEGORY = "cs.LG"
DEFAULT_TARGET_SCORE = "8"


def load_prompt(name: str, **kwargs: str) -> str:
    """Insert prompt fields without treating user content braces as format placeholders."""
    text = (PROMPTS / name).read_text(encoding="utf-8")
    for key, value in kwargs.items():
        text = text.replace("{" + key + "}", value)
    return text


def load_contribution(path: Path | None) -> str:
    if path is None:
        return (PROMPTS / "contribution_default.md").read_text(encoding="utf-8")
    if not path.is_file():
        print(f"Contribution file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def seed_output_dir(out_path: Path) -> None:
    """Copy LaTeX skeleton and checklist if not already present."""
    out_path.mkdir(parents=True, exist_ok=True)
    for name in ("arxiv_main.tex", "appendix_math.tex", "SUBMISSION_CHECKLIST.md"):
        src = TEMPLATES / name
        dst_name = "main.tex" if name == "arxiv_main.tex" else name
        dst = out_path / dst_name
        if not dst.exists() and src.is_file():
            shutil.copy2(src, dst)


def stream_run(agent: Agent, prompt: str, label: str) -> None:
    print(f"\n--- {label} ---\n")
    run = agent.send(prompt)
    print(f"[{label}] run_id={run.id} agent_id={agent.agent_id}")
    for message in run.messages():
        if message.type != "assistant":
            continue
        for block in message.message.content:
            if block.type == "text" and block.text:
                print(block.text, end="", flush=True)
    result = run.wait()
    if result.status == "error":
        print(f"\n[{label}] run failed: {result.id}", file=sys.stderr)
        sys.exit(2)
    print(f"\n[{label}] finished ({result.status})")


def make_agent(cwd: Path, model: str) -> Agent:
    api_key = os.environ.get("CURSOR_API_KEY")
    if not api_key:
        print("Set CURSOR_API_KEY (see .env.example).", file=sys.stderr)
        sys.exit(1)
    return Agent.create(
        model=model,
        api_key=api_key,
        local=LocalAgentOptions(cwd=str(cwd), setting_sources=[]),
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="arXiv preprint agents: writer (LaTeX) + reviewer (rubric) + optional revision loops.",
    )
    p.add_argument("--topic", required=True, help="Paper title / topic")
    p.add_argument(
        "--outline",
        default=(
            "IMRaD structure; 8–12 pages; precise definitions; limitations section; "
            "no fabricated experiments."
        ),
        help="Venue style, page limit, section requirements",
    )
    p.add_argument(
        "--arxiv-category",
        default=DEFAULT_CATEGORY,
        help=f"Primary arXiv category (default: {DEFAULT_CATEGORY})",
    )
    p.add_argument(
        "--contribution",
        type=Path,
        default=None,
        help="Markdown file with YOUR verified claims, results, authors (strongly recommended)",
    )
    p.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT,
        help=f"Output folder under --cwd (default: {DEFAULT_OUTPUT})",
    )
    p.add_argument(
        "--cwd",
        default=None,
        help="Workspace root for agents (default: repo root)",
    )
    p.add_argument(
        "--model",
        default="composer-2.5",
        help="Cursor model id",
    )
    p.add_argument(
        "--revise",
        action="store_true",
        help="After review, run writer revision pass(es)",
    )
    p.add_argument(
        "--revise-loops",
        type=int,
        default=1,
        metavar="N",
        help="Revision passes when --revise is set (default: 1)",
    )
    p.add_argument(
        "--re-review",
        action="store_true",
        help="Run reviewer again after each revision pass",
    )
    p.add_argument(
        "--target-score",
        default=DEFAULT_TARGET_SCORE,
        help=f"Rubric target for revision pass (default: {DEFAULT_TARGET_SCORE})",
    )
    p.add_argument("--writer-only", action="store_true", help="Skip reviewer")
    p.add_argument("--review-only", action="store_true", help="Skip writer")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.review_only and args.writer_only:
        print("Choose at most one of --writer-only and --review-only.", file=sys.stderr)
        sys.exit(1)
    if args.revise_loops < 1:
        print("--revise-loops must be >= 1.", file=sys.stderr)
        sys.exit(1)

    cwd = Path(args.cwd).resolve() if args.cwd else ROOT.parent
    output_dir = args.output_dir.strip("/\\")
    out_path = cwd / output_dir
    contribution_spec = load_contribution(
        args.contribution.resolve() if args.contribution else None,
    )

    seed_output_dir(out_path)

    prompt_kwargs = {
        "topic": args.topic,
        "outline": args.outline,
        "output_dir": output_dir,
        "arxiv_category": args.arxiv_category,
        "contribution_spec": contribution_spec,
        "target_score": args.target_score,
    }

    try:
        if not args.review_only:
            with make_agent(cwd, args.model) as writer:
                stream_run(
                    writer,
                    load_prompt("writer.md", **prompt_kwargs),
                    "Writer (arXiv draft)",
                )

        if not args.writer_only:
            with make_agent(cwd, args.model) as reviewer:
                stream_run(
                    reviewer,
                    load_prompt("reviewer.md", **prompt_kwargs),
                    "Reviewer (rubric)",
                )

        if args.revise and not args.writer_only:
            review_file = out_path / "review.md"
            if not review_file.is_file():
                print(f"No {review_file}; run reviewer first.", file=sys.stderr)
                sys.exit(1)

            for loop in range(1, args.revise_loops + 1):
                review_text = review_file.read_text(encoding="utf-8")
                with make_agent(cwd, args.model) as writer:
                    revise_body = load_prompt("revise.md", **prompt_kwargs)
                    full_prompt = (
                        f"{revise_body}\n\n"
                        f"--- REVIEW (pass {loop}) ---\n{review_text}"
                    )
                    stream_run(
                        writer,
                        full_prompt,
                        f"Writer (revision {loop}/{args.revise_loops})",
                    )

                if args.re_review:
                    with make_agent(cwd, args.model) as reviewer:
                        stream_run(
                            reviewer,
                            load_prompt("reviewer.md", **prompt_kwargs),
                            f"Reviewer (re-review {loop})",
                        )

    except CursorAgentError as err:
        print(f"Agent startup failed: {err.message}", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone. arXiv bundle in: {out_path}")
    print("  main.tex, references.bib, verification_log.md, review.md (rubric scores)")
    print("  Complete templates/SUBMISSION_CHECKLIST.md before uploading to arXiv.")


if __name__ == "__main__":
    main()
