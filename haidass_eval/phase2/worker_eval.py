import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path


MODEL_CACHE_URL = os.environ.get(
    "MODEL_CACHE_URL",
    "http://haidass-model-cache.haidass-eval.svc.cluster.local:8081",
)
MODEL_DIR = Path(os.environ.get("MODEL_DIR", "/cache/models/Haidass-143M-v1"))
RUNTIME_DIR = Path(os.environ.get("LIGHTEVAL_RUNTIME", "/cache/models/lighteval-runtime-0.9.2"))
HF_CACHE = Path(os.environ.get("HF_HOME", "/cache/models/huggingface"))
RUN_NAME = os.environ.get("LIGHTEVAL_RUN_NAME", "phase2-smoke")
RESULT_DIR = Path(
    os.environ.get("RESULT_DIR", f"/cache/models/haidass-eval-results/{RUN_NAME}")
)
TASKS = os.environ.get("LIGHTEVAL_TASKS", "lighteval|arc:easy|0|0")
MAX_SAMPLES = int(os.environ.get("LIGHTEVAL_MAX_SAMPLES", "16"))
BATCH_SIZE = int(os.environ.get("LIGHTEVAL_BATCH_SIZE", "1"))


def fetch_bytes(relative_path: str) -> bytes:
    with urllib.request.urlopen(f"{MODEL_CACHE_URL}/{relative_path}", timeout=120) as response:
        return response.read()


def prepare_model() -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    checksums_text = fetch_bytes("SHA256SUMS").decode()
    expected = {}
    for line in checksums_text.splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename.removeprefix("./")] = digest

    downloaded = 0
    started = time.monotonic()
    for filename, expected_digest in expected.items():
        destination = MODEL_DIR / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            actual = hashlib.sha256(destination.read_bytes()).hexdigest()
            if actual == expected_digest:
                continue

        temporary = destination.with_suffix(destination.suffix + ".part")
        digest = hashlib.sha256()
        with urllib.request.urlopen(f"{MODEL_CACHE_URL}/{filename}", timeout=180) as response:
            with temporary.open("wb") as output:
                while chunk := response.read(8 * 1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)
        if digest.hexdigest() != expected_digest:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Checksum mismatch for {filename}")
        temporary.replace(destination)

    (MODEL_DIR / "SHA256SUMS").write_text(checksums_text)
    return {
        "downloaded_bytes": downloaded,
        "prepare_seconds": round(time.monotonic() - started, 3),
        "file_count": len(expected),
    }


def install_lighteval() -> dict:
    marker = RUNTIME_DIR / ".lighteval-0.9.2-ready"
    wheelhouse = Path(__file__).resolve().parent / "wheelhouse"
    wheels = sorted(str(path) for path in wheelhouse.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"Offline wheelhouse is empty: {wheelhouse}")
    wheel_manifest = "\n".join(Path(path).name for path in wheels) + "\n"
    if marker.exists() and marker.read_text() == wheel_manifest:
        return {"installed": False, "runtime_dir": str(RUNTIME_DIR)}

    shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    RUNTIME_DIR.mkdir(parents=True)
    env = os.environ.copy()
    started = time.monotonic()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--target",
            str(RUNTIME_DIR),
            *wheels,
        ],
        check=True,
        env=env,
    )
    marker.write_text(wheel_manifest)
    return {
        "installed": True,
        "install_seconds": round(time.monotonic() - started, 3),
        "runtime_dir": str(RUNTIME_DIR),
    }


def runtime_env() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{RUNTIME_DIR}:{env.get('PYTHONPATH', '')}"
    env["HF_HOME"] = str(HF_CACHE)
    env["HF_DATASETS_CACHE"] = str(HF_CACHE / "datasets")
    env["TOKENIZERS_PARALLELISM"] = "false"
    env["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
    return env


def run_generation_smoke() -> dict:
    code = r'''
import json
import time
import torch
import torch_npu
from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir = __import__("os").environ["MODEL_DIR"]
torch.npu.set_device(0)
started = time.monotonic()
tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    model_dir,
    local_files_only=True,
    torch_dtype=torch.bfloat16,
).to("npu:0")
model.eval()
load_seconds = time.monotonic() - started
prompt = "The capital of France is"
inputs = tokenizer(prompt, return_tensors="pt")
inputs = {key: value.to("npu:0") for key, value in inputs.items()}
generate_started = time.monotonic()
with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=16, do_sample=False)
torch.npu.synchronize()
print(json.dumps({
    "device": str(next(model.parameters()).device),
    "load_seconds": round(load_seconds, 3),
    "generate_seconds": round(time.monotonic() - generate_started, 3),
    "output": tokenizer.decode(output[0], skip_special_tokens=True),
    "hbm_allocated_bytes": torch.npu.memory_allocated(0),
}, ensure_ascii=False))
'''
    env = runtime_env()
    env["MODEL_DIR"] = str(MODEL_DIR)
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run_lighteval() -> dict:
    shutil.rmtree(RESULT_DIR, ignore_errors=True)
    RESULT_DIR.mkdir(parents=True)
    existing_results = set(MODEL_DIR.glob("results_*.json"))
    env = runtime_env()
    source_dir = Path(__file__).resolve().parent
    custom_tasks = source_dir / "offline_dataset_router.py"
    env["LIGHTEVAL_DATA_ROOT"] = str(source_dir / "datasets")
    command = [
        sys.executable,
        "-m",
        "lighteval",
        "accelerate",
        (
            f"model_name={MODEL_DIR},dtype=bfloat16,batch_size={BATCH_SIZE},"
            "model_parallel=false,compile=false"
        ),
        TASKS,
        "--custom-tasks",
        str(custom_tasks),
        "--dataset-loading-processes",
        "1",
        "--output-dir",
        str(RESULT_DIR),
        "--save-details",
    ]
    if MAX_SAMPLES > 0:
        command.extend(["--max-samples", str(MAX_SAMPLES)])
    log_path = RESULT_DIR / "lighteval.log"
    started = time.monotonic()
    with log_path.open("w") as log:
        completed = subprocess.run(
            command,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-120:])
        raise RuntimeError(f"LightEval failed with {completed.returncode}:\n{tail}")

    artifact_dir = RESULT_DIR / "lighteval-artifacts"
    artifact_dir.mkdir()
    new_results = sorted(set(MODEL_DIR.glob("results_*.json")) - existing_results)
    for result_path in new_results:
        shutil.copy2(result_path, artifact_dir / result_path.name)
        details_name = result_path.stem.removeprefix("results_")
        details_path = MODEL_DIR / details_name
        if details_path.is_dir():
            shutil.copytree(details_path, artifact_dir / details_name)

    json_files = sorted(str(path.relative_to(RESULT_DIR)) for path in RESULT_DIR.rglob("*.json"))
    return {
        "tasks": TASKS,
        "batch_size": BATCH_SIZE,
        "max_samples": MAX_SAMPLES if MAX_SAMPLES > 0 else None,
        "elapsed_seconds": round(elapsed, 3),
        "result_json_files": json_files,
    }


def analyze_bad_cases() -> dict:
    import pyarrow.parquet as parquet

    details_files = sorted((RESULT_DIR / "lighteval-artifacts").rglob("details_*.parquet"))
    if not details_files:
        return {"available": False, "reason": "No details parquet found"}

    rows = []
    for details_file in details_files:
        rows.extend(parquet.read_table(details_file).to_pylist())

    raw_bad_cases = []
    normalized_bad_cases = []
    normalization_fixed = []
    normalization_hurt = []
    normalization_prediction_mismatches = 0

    def continuation_length(tokens):
        tokens = list(tokens or [])
        while tokens and tokens[-1] == 5:
            tokens.pop()
        return max(len(tokens), 1)

    for index, row in enumerate(rows):
        metrics = row.get("metrics") or {}
        choices = row.get("choices") or []
        predictions = row.get("predictions") or []
        scores = [float(value[0]) for value in predictions if value]
        if not scores or not choices:
            continue
        token_lengths = [continuation_length(tokens) for tokens in (row.get("cont_tokens") or [])]
        if len(token_lengths) != len(scores):
            token_lengths = [1] * len(scores)
        ignore_first_space = "piqa" in TASKS or "arc:" in TASKS
        normalization_lengths = [
            max(len(choice) - (1 if ignore_first_space and choice.startswith(" ") else 0), 1)
            for choice in choices
        ]
        normalized_scores = [
            score / length for score, length in zip(scores, normalization_lengths)
        ]
        raw_ranked = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
        norm_ranked = sorted(
            range(len(normalized_scores)), key=normalized_scores.__getitem__, reverse=True
        )
        raw_predicted_index = raw_ranked[0]
        norm_predicted_index = norm_ranked[0]
        gold_indexes = row.get("gold_index") or []
        gold_index = int(gold_indexes[0]) if gold_indexes else -1
        raw_correct = metrics.get("acc", 0) == 1
        norm_correct = metrics.get("acc_norm", metrics.get("acc", 0)) == 1
        if (norm_predicted_index == gold_index) != norm_correct:
            normalization_prediction_mismatches += 1
        item = {
            "row_index": index,
            "prompt": row.get("example") or row.get("full_prompt") or "",
            "choices": choices,
            "gold_index": gold_index,
            "gold_choice": choices[gold_index] if 0 <= gold_index < len(choices) else None,
            "raw_predicted_index": raw_predicted_index,
            "raw_predicted_choice": choices[raw_predicted_index],
            "normalized_predicted_index": norm_predicted_index,
            "normalized_predicted_choice": choices[norm_predicted_index],
            "scores": scores,
            "continuation_token_lengths": token_lengths,
            "normalization_character_lengths": normalization_lengths,
            "normalized_scores": [round(value, 6) for value in normalized_scores],
            "raw_wrong_confidence_margin": round(
                scores[raw_ranked[0]] - scores[raw_ranked[1]], 6
            ),
            "normalized_wrong_confidence_margin": round(
                normalized_scores[norm_ranked[0]] - normalized_scores[norm_ranked[1]], 6
            ),
            "metrics": metrics,
        }
        if not raw_correct:
            raw_bad_cases.append(item)
        if not norm_correct:
            normalized_bad_cases.append(item)
        if not raw_correct and norm_correct:
            normalization_fixed.append(item)
        if raw_correct and not norm_correct:
            normalization_hurt.append(item)

    raw_bad_cases.sort(key=lambda item: item["raw_wrong_confidence_margin"], reverse=True)
    normalized_bad_cases.sort(
        key=lambda item: item["normalized_wrong_confidence_margin"], reverse=True
    )
    analysis = {
        "available": True,
        "sample_count": len(rows),
        "raw_bad_case_count": len(raw_bad_cases),
        "raw_error_rate": round(len(raw_bad_cases) / len(rows), 6) if rows else None,
        "normalized_bad_case_count": len(normalized_bad_cases),
        "normalized_error_rate": round(len(normalized_bad_cases) / len(rows), 6) if rows else None,
        "normalization_fixed_count": len(normalization_fixed),
        "normalization_hurt_count": len(normalization_hurt),
        "normalization_prediction_mismatches": normalization_prediction_mismatches,
        "top_raw_confidently_wrong": raw_bad_cases[:100],
        "top_normalized_confidently_wrong": normalized_bad_cases[:100],
        "normalization_fixed_examples": normalization_fixed[:100],
        "normalization_hurt_examples": normalization_hurt[:100],
    }
    (RESULT_DIR / "bad_cases.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2)
    )

    lines = [
        f"# Bad Cases: {RUN_NAME}",
        "",
        f"- Samples: {len(rows)}",
        f"- Raw incorrect: {len(raw_bad_cases)} ({analysis['raw_error_rate']})",
        f"- Length-normalized incorrect: {len(normalized_bad_cases)} ({analysis['normalized_error_rate']})",
        f"- Normalization fixed: {len(normalization_fixed)}",
        f"- Normalization hurt: {len(normalization_hurt)}",
        f"- Reconstructed normalized prediction mismatches: {normalization_prediction_mismatches}",
        "- Ordering: most confidently wrong after length normalization",
        "",
    ]
    for rank, item in enumerate(normalized_bad_cases[:50], start=1):
        lines.extend(
            [
                f"## {rank}. Row {item['row_index']}",
                "",
                f"- Gold: `{item['gold_index']}` {item['gold_choice']}",
                f"- Raw predicted: `{item['raw_predicted_index']}` {item['raw_predicted_choice']}",
                f"- Normalized predicted: `{item['normalized_predicted_index']}` {item['normalized_predicted_choice']}",
                f"- Normalized wrong-confidence margin: `{item['normalized_wrong_confidence_margin']}`",
                f"- Raw scores: `{item['scores']}`",
                f"- Token lengths: `{item['continuation_token_lengths']}`",
                f"- Normalization character lengths: `{item['normalization_character_lengths']}`",
                f"- Normalized scores: `{item['normalized_scores']}`",
                "",
                "```text",
                str(item["prompt"])[:4000],
                "```",
                "",
            ]
        )
    (RESULT_DIR / "BAD_CASES.md").write_text("\n".join(lines))
    return {key: value for key, value in analysis.items() if not isinstance(value, list)}


def package_results(summary: dict) -> bytes:
    (RESULT_DIR / "phase2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )
    archive_path = Path(f"/tmp/haidass-{RUN_NAME}-results.tar.gz")
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(RESULT_DIR, arcname=RUN_NAME)
    return archive_path.read_bytes()


def main() -> tuple[dict, bytes]:
    overall_started = time.monotonic()
    summary = {
        "model_prepare": prepare_model(),
        "runtime": install_lighteval(),
        "generation_smoke": run_generation_smoke(),
    }
    summary["lighteval"] = run_lighteval()
    summary["bad_cases"] = analyze_bad_cases()
    summary["overall_seconds"] = round(time.monotonic() - overall_started, 3)
    return summary, package_results(summary)


if __name__ == "__main__":
    result, _ = main()
    print(json.dumps(result, ensure_ascii=False, indent=2))
