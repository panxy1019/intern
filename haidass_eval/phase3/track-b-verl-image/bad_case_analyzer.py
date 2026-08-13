import json
from pathlib import Path

import pyarrow.parquet as parquet


def analyze_bad_cases(result_dir, task_name):
    result_dir = Path(result_dir)
    details_files = sorted(result_dir.rglob("details_*.parquet"))
    rows = []
    for details_file in details_files:
        rows.extend(parquet.read_table(details_file).to_pylist())

    cases = []
    raw_errors = normalized_errors = fixed = hurt = mismatches = 0
    ignore_first_space = "piqa" in task_name or "arc:" in task_name
    for index, row in enumerate(rows):
        choices = list(row.get("choices") or [])
        scores = [float(item[0]) for item in (row.get("predictions") or []) if item]
        if not choices or len(choices) != len(scores):
            continue
        lengths = [max(len(choice) - int(ignore_first_space and choice.startswith(" ")), 1) for choice in choices]
        normalized_scores = [score / length for score, length in zip(scores, lengths)]
        raw_prediction = max(range(len(scores)), key=scores.__getitem__)
        norm_prediction = max(range(len(scores)), key=normalized_scores.__getitem__)
        gold_indexes = row.get("gold_index") or []
        gold = int(gold_indexes[0]) if gold_indexes else -1
        metrics = row.get("metrics") or {}
        raw_correct = raw_prediction == gold
        norm_correct = norm_prediction == gold
        mismatches += int(raw_correct != bool(metrics.get("acc")))
        mismatches += int(norm_correct != bool(metrics.get("acc_norm")))
        raw_errors += int(not raw_correct)
        normalized_errors += int(not norm_correct)
        fixed += int(not raw_correct and norm_correct)
        hurt += int(raw_correct and not norm_correct)
        if not raw_correct or not norm_correct:
            cases.append(
                {
                    "row_index": index,
                    "prompt": row.get("example") or row.get("full_prompt") or "",
                    "choices": choices,
                    "gold_index": gold,
                    "acc_index": raw_prediction,
                    "acc_norm_index": norm_prediction,
                    "raw_scores": scores,
                    "acc_norm_scores": normalized_scores,
                    "metrics": metrics,
                }
            )
    summary = {
        "sample_count": len(rows),
        "bad_case_union_count": len(cases),
        "raw_bad_case_count": raw_errors,
        "normalized_bad_case_count": normalized_errors,
        "normalization_fixed_count": fixed,
        "normalization_hurt_count": hurt,
        "metric_mismatch_count": mismatches,
    }
    (result_dir / "bad_cases.json").write_text(json.dumps({"summary": summary, "cases": cases}, ensure_ascii=False, indent=2))
    lines = [f"# Bad Cases: {task_name}", "", *(f"- {key}: {value}" for key, value in summary.items()), ""]
    for case in cases:
        lines.extend(
            [
                f"## Row {case['row_index']}",
                "",
                f"- Gold: `{case['gold_index']}`",
                f"- acc: `{case['acc_index']}`",
                f"- acc_norm: `{case['acc_norm_index']}`",
                "",
                "```text",
                case["prompt"],
                "```",
                "",
            ]
        )
    (result_dir / "BAD_CASES.md").write_text("\n".join(lines))
    return summary
