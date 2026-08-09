"""Resolve a captured VLM reference analysis into a compiler scene spec.

This CLI is intentionally pure Python. It performs no image inference itself; a GPT/VLM
adapter writes the analysis JSON, then this deterministic resolver decides which proposed
parameters are allowed to reach Blender.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyzer.reference import resolve_reference_analysis  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, help="Reference-analysis JSON")
    parser.add_argument("--out", required=True, help="Resolved scene-spec JSON")
    parser.add_argument("--report", required=True, help="Resolution decision report JSON")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--minimum-confidence", type=float, default=0.35)
    return parser.parse_args()


def write_json(path: str | Path, data: dict) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> None:
    args = parse_args()
    analysis_path = Path(args.analysis)
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    spec, report = resolve_reference_analysis(
        analysis,
        seed=args.seed,
        minimum_confidence=args.minimum_confidence,
    )

    spec_path = write_json(args.out, spec)
    report_path = write_json(args.report, report)
    accepted = sum(1 for item in report["decisions"] if item["accepted"])
    rejected = len(report["decisions"]) - accepted
    print(f"resolved factory={spec['factory']} accepted={accepted} rejected={rejected}")
    print(f"scene_spec={spec_path}")
    print(f"resolution_report={report_path}")


if __name__ == "__main__":
    main()
