"""Run the Claude triage over the dev or test tickets (needs an Anthropic API key).

    python scripts/run_llm.py --model claude-haiku-5-5 --split dev            # shows the cost estimate, stops
    python scripts/run_llm.py --model claude-haiku-5-5 --split dev --yes      # runs it

The key is read from the ANTHROPIC_API_KEY environment variable and never written
anywhere. Responses go to results/llm/<model>/<split>_<prompt>_responses.jsonl, one line
per ticket, as they arrive. Running the same command again only sends the
tickets that have no good answer yet.

The test split is meant to be run once per model, after the prompt is settled on
dev (docs/05). Nothing stops you running it twice, but the evaluation report
lists every run in the file, so a second run would show.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triage import DATA, RESULTS  # noqa: E402
from triage.llm import estimate, prices, run  # noqa: E402

SPLITS = {"dev": DATA / "eval" / "dev.csv", "test": DATA / "eval" / "test.csv"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, choices=sorted(prices()))
    ap.add_argument("--split", required=True, choices=sorted(SPLITS))
    ap.add_argument("--prompt", default="triage_v3")
    ap.add_argument("--limit", type=int, help="only the first N tickets (for a smoke test)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--label", default="", help="suffix for the output file, e.g. 'repeat' for the consistency re-run")
    ap.add_argument("--temperature", type=float, default=None,
                    help="only if the SDK and model accept it; the SDK used on 16 Oct 2026 does not")
    ap.add_argument("--yes", action="store_true", help="actually call the API")
    args = ap.parse_args(argv)

    with open(SPLITS[args.split], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]
    est = estimate(args.model, rows, args.prompt)
    print(f"{args.model} on {args.split}: {est['tickets']} tickets, about {est['input_tokens']:,} input and "
          f"{est['output_tokens']:,} output tokens, about ${est['usd']:.2f} at list price (before prompt caching).")
    if not args.yes:
        print("Nothing sent. Add --yes to run it.")
        return 0
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set in this shell.", file=sys.stderr)
        return 2

    import anthropic  # only needed for live runs

    client = anthropic.Anthropic(max_retries=4, timeout=60)
    name = f"{args.split}_{args.prompt}" + (f"_{args.label}" if args.label else "") + "_responses.jsonl"
    out = RESULTS / "llm" / args.model / name
    summary = run(client, args.model, rows, out, prompt_version=args.prompt, workers=args.workers,
                  temperature=args.temperature, sdk=anthropic.__version__)
    print(f"Done: {summary}. Responses in {out.relative_to(ROOT)}")
    return 0 if summary["api_error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
