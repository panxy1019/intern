#!/usr/bin/env python3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/host/data/haidass-eval")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_records(directory, excluded_names=()):
    records = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name not in excluded_names:
            records.append(
                {"path": str(path.relative_to(directory)), "size": path.stat().st_size, "sha256": sha256_file(path)}
            )
    return records


def model_manifest(model_dir):
    records = file_records(model_dir, {"model_manifest.json"})
    source_file = model_dir / "MODEL_ID"
    revision_file = model_dir / "REVISION"
    manifest = {
        "name": model_dir.name,
        "source": source_file.read_text().strip() if source_file.exists() else model_dir.name,
        "revision": revision_file.read_text().strip() if revision_file.exists() else "unknown",
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256("".join(item["sha256"] for item in records).encode()).hexdigest(),
        "file_count": len(records),
        "files": records,
    }
    (model_dir / "model_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def parquet_rows(path):
    try:
        import pyarrow.parquet as parquet

        return parquet.ParquetFile(path).metadata.num_rows
    except Exception:
        return None


def line_rows(path):
    with path.open("rb") as source:
        return sum(1 for _ in source)


def dataset_manifest(dataset_dir):
    records = file_records(dataset_dir, {"dataset_manifest.json"})
    splits = {}
    for item in records:
        path = dataset_dir / item["path"]
        if path.suffix == ".parquet":
            splits[path.stem] = parquet_rows(path)
        elif path.suffix in {".jsonl", ".json"} and path.parent == dataset_dir:
            splits[path.stem] = line_rows(path)
    source_file = dataset_dir / "SOURCE"
    revision_file = dataset_dir / "REVISION"
    manifest = {
        "dataset": dataset_dir.name,
        "source": source_file.read_text().strip() if source_file.exists() else dataset_dir.name,
        "revision": revision_file.read_text().strip() if revision_file.exists() else "pinned-local-cache",
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "splits": splits,
        "sample_count": sum(value for value in splits.values() if value is not None),
        "sha256": hashlib.sha256("".join(item["sha256"] for item in records).encode()).hexdigest(),
        "files": records,
    }
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


for directory in sorted((ROOT / "models").iterdir()):
    if directory.is_dir():
        model_manifest(directory)
for directory in sorted((ROOT / "datasets").iterdir()):
    if directory.is_dir():
        dataset_manifest(directory)
