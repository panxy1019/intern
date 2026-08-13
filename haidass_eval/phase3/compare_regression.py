#!/usr/bin/env python3
import json
from pathlib import Path

import pyarrow.parquet as parquet


ROOT = Path("/host/data/haidass-eval/results")
RUNS = {
    "demo_piqa": "20260813T020536Z_Haidass-143M-v1_piqa_1528a9",
    "demo_hellaswag": "20260813T020537Z_Haidass-143M-v1_hellaswag_438b6b",
    "candidate_piqa": "20260813T022117Z_candidate_Haidass-143M-v1_piqa_full",
    "candidate_hellaswag": "20260813T022117Z_candidate_Haidass-143M-v1_hellaswag_full",
}


def read_run(name):
    directory = ROOT / RUNS[name]
    result_file = next(directory.glob("results_*.json"))
    details_file = next(directory.rglob("details_*.parquet"))
    result = json.loads(result_file.read_text())
    summary = json.loads((directory / "summary.json").read_text())
    table = parquet.read_table(details_file)
    metrics = result["results"]
    task_key = next(key for key in metrics if key != "all")
    return {
        "run_id": RUNS[name],
        "task_key": task_key,
        "acc": metrics[task_key]["acc"],
        "acc_norm": metrics[task_key]["acc_norm"],
        "sample_count": table.num_rows,
        "details_schema": str(table.schema),
        "bad_cases": summary["bad_cases"],
        "elapsed_seconds": summary["elapsed_seconds"],
    }


report = {name: read_run(name) for name in RUNS}
checks = {}
for task in ("piqa", "hellaswag"):
    demo = report[f"demo_{task}"]
    candidate = report[f"candidate_{task}"]
    checks[task] = {
        "metrics_equal": (demo["acc"], demo["acc_norm"]) == (candidate["acc"], candidate["acc_norm"]),
        "sample_count_equal": demo["sample_count"] == candidate["sample_count"],
        "details_schema_equal": demo["details_schema"] == candidate["details_schema"],
        "bad_case_counts_equal": demo["bad_cases"] == candidate["bad_cases"],
    }
report["checks"] = checks
report["regression_pass"] = all(all(values.values()) for values in checks.values())
output = ROOT / "PHASE3_REGRESSION_COMPARISON.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report["regression_pass"]:
    raise SystemExit(1)
