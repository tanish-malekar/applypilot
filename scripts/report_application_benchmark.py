"""Summarize independently recorded, paired application sessions."""
import argparse
import json
import math
from pathlib import Path


def summarize(rows):
    if len(rows) != 150 or len({r["posting_id"] for r in rows}) != 150:
        raise ValueError("Provide exactly 150 unique paired postings")
    for row in rows:
        for mode in ("manual", "baseline", "learned"):
            values = row[mode]
            if not math.isfinite(values["seconds"]) or values["seconds"] <= 0:
                raise ValueError("Positive finite elapsed time required, including review and corrections")
            if any(type(values[key]) is not int for key in ("correct_fields", "total_fields")) or not 0 <= values["correct_fields"] <= values["total_fields"] or values["total_fields"] <= 0:
                raise ValueError("Invalid independently reviewed field counts")
        if len({row[mode]['total_fields'] for mode in ('manual', 'baseline', 'learned')}) != 1:
            raise ValueError("Baseline and learned field denominators must match")
    seconds = {mode: sum(r[mode]["seconds"] for r in rows) for mode in ("manual", "baseline", "learned")}
    accuracy = {mode: sum(r[mode]["correct_fields"] for r in rows) / sum(r[mode]["total_fields"] for r in rows)
                for mode in ("baseline", "learned")}
    return {"postings": len(rows), "application_seconds": seconds, "field_accuracy": accuracy,
        "time_reduction_percent_vs_manual": 100 * (1 - seconds["learned"] / seconds["manual"]),
        "accuracy_gain_percentage_points": 100 * (accuracy["learned"] - accuracy["baseline"]),
        "accuracy_relative_lift_percent": 100 * (accuracy["learned"] / accuracy["baseline"] - 1) if accuracy["baseline"] else None}


def main():
    p = argparse.ArgumentParser(); p.add_argument("ledger", type=Path); p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    rows = [json.loads(s) for s in args.ledger.read_text().splitlines() if s.strip()]
    args.output.write_text(json.dumps(summarize(rows), indent=2, allow_nan=False) + "\n")


if __name__ == "__main__": main()
