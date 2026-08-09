"""Apply a bounded visual QA review to an existing compiler scene spec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qa.visual_review import apply_visual_review  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="Input scene-spec JSON")
    parser.add_argument("--review", required=True, help="Visual-review JSON")
    parser.add_argument("--out", required=True, help="Repaired scene-spec JSON")
    parser.add_argument("--report", required=True, help="Repair decision report JSON")
    parser.add_argument("--minimum-confidence", type=float, default=0.40)
    return parser.parse_args()


def write_json(path: str | Path, data: dict) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> None:
    args = parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    review = json.loads(Path(args.review).read_text(encoding="utf-8"))
    repaired, report = apply_visual_review(
        spec,
        review,
        minimum_confidence=args.minimum_confidence,
    )
    out_path = write_json(args.out, repaired)
    report_path = write_json(args.report, report)

    decisions = report["decisions"] + report["room_decisions"]
    accepted = sum(1 for item in decisions if item["accepted"])
    rejected = len(decisions) - accepted
    severe_gaps = sum(1 for gap in report["template_gaps"] if gap["severity"] >= 0.80)
    print(
        f"visual repair factory={repaired['factory']} "
        f"patches={accepted} accepted/{rejected} rejected "
        f"severe_template_gaps={severe_gaps}"
    )
    print(f"scene_spec={out_path}")
    print(f"repair_report={report_path}")


if __name__ == "__main__":
    main()
