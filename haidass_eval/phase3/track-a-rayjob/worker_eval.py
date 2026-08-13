import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bad_case_analyzer import analyze_bad_cases
from task_catalog import resolve_task


def sha256_file(path):
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_worker(model, task_alias, batch_size, max_samples, run_id):
    cached_model_dir = Path("/cache/models") / model
    dataset_root = Path("/cache/datasets")
    result_dir = Path("/results") / run_id
    if not cached_model_dir.is_dir():
        raise FileNotFoundError(f"Model cache is missing: {cached_model_dir}")
    result_dir.mkdir(parents=True, exist_ok=False)
    model_dir = Path("/tmp/lighteval-model") / run_id
    model_dir.mkdir(parents=True)
    for source in cached_model_dir.iterdir():
        if source.name.startswith("results_") or source.name[:4].isdigit():
            continue
        (model_dir / source.name).symlink_to(source)

    task = resolve_task(task_alias)
    environment = os.environ.copy()
    environment.update(
        {
            "HF_HOME": f"/tmp/huggingface/{run_id}",
            "HF_DATASETS_CACHE": f"/tmp/huggingface/{run_id}/datasets",
            "LIGHTEVAL_DATA_ROOT": str(dataset_root),
            "TOKENIZERS_PARALLELISM": "false",
            "TORCH_DEVICE_BACKEND_AUTOLOAD": "0",
        }
    )
    source_dir = Path(__file__).resolve().parent
    command = [
        sys.executable,
        "-m",
        "lighteval",
        "accelerate",
        f"model_name={model_dir},dtype=bfloat16,batch_size={batch_size},model_parallel=false,compile=false",
        task,
        "--custom-tasks",
        str(source_dir / "offline_dataset_router.py"),
        "--dataset-loading-processes",
        "1",
        "--output-dir",
        str(result_dir),
        "--save-details",
    ]
    if max_samples > 0:
        command.extend(["--max-samples", str(max_samples)])

    started_at = datetime.now(timezone.utc)
    manifest = {
        "run_id": run_id,
        "model": model,
        "model_path": str(cached_model_dir),
        "model_facade": str(model_dir),
        "task_alias": task_alias,
        "task": task,
        "batch_size": batch_size,
        "max_samples": max_samples or None,
        "started_at": started_at.isoformat(),
        "command": command,
        "hostname": os.uname().nodename,
    }
    (result_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    log_path = result_dir / "lighteval.log"
    started = time.monotonic()
    with log_path.open("w") as log:
        completed = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, text=True)
    if completed.returncode != 0:
        manifest["status"] = "failed"
        manifest["returncode"] = completed.returncode
        manifest["ended_at"] = datetime.now(timezone.utc).isoformat()
        (result_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-120:])
        raise RuntimeError(f"LightEval failed with {completed.returncode}:\n{tail}")

    for candidate in model_dir.glob("results_*.json"):
        if candidate.stat().st_mtime >= started_at.timestamp() - 2:
            shutil.copy2(candidate, result_dir / candidate.name)
            detail_dir = model_dir / candidate.stem.removeprefix("results_")
            if detail_dir.is_dir():
                shutil.copytree(detail_dir, result_dir / detail_dir.name, dirs_exist_ok=True)

    bad_cases = analyze_bad_cases(result_dir, task)
    artifacts = []
    for path in sorted(result_dir.rglob("*")):
        if path.is_file():
            artifacts.append(
                {"path": str(path.relative_to(result_dir)), "size": path.stat().st_size, "sha256": sha256_file(path)}
            )
    summary = {
        "status": "success",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "bad_cases": bad_cases,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    (result_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    manifest.update({"status": "success", "ended_at": datetime.now(timezone.utc).isoformat()})
    (result_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return {"run_id": run_id, "result_dir": str(result_dir), **summary}
