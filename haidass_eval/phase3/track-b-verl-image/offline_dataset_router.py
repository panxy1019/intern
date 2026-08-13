import os
from pathlib import Path

from datasets import load_dataset

import lighteval.tasks.lighteval_task as task_module


DATA_ROOT = Path(os.environ.get("LIGHTEVAL_DATA_ROOT", "/cache/datasets"))
ORIGINAL_DOWNLOAD_DATASET_WORKER = task_module.download_dataset_worker


ROUTES = {
    ("ai2_arc", "ARC-Easy"): (
        "arc_easy",
        "parquet",
        {"train": "train.parquet", "validation": "validation.parquet", "test": "test.parquet"},
    ),
    ("ai2_arc", "ARC-Challenge"): (
        "arc_challenge",
        "parquet",
        {"train": "train.parquet", "validation": "validation.parquet", "test": "test.parquet"},
    ),
    ("ybisk/piqa", "plain_text"): (
        "piqa",
        "json",
        {"train": "train.jsonl", "validation": "validation.jsonl"},
    ),
    ("hellaswag", "default"): (
        "hellaswag",
        "parquet",
        {"train": "train.parquet", "validation": "validation.parquet"},
    ),
    ("winogrande", "winogrande_xl"): (
        "winogrande",
        "parquet",
        {"train": "train.parquet", "validation": "validation.parquet"},
    ),
    ("allenai/openbookqa", "main"): (
        "openbookqa",
        "parquet",
        {"train": "train.parquet", "validation": "validation.parquet", "test": "test.parquet"},
    ),
    ("cais/mmlu", "all"): (
        "mmlu",
        "parquet",
        {"auxiliary_train": "auxiliary_train.parquet", "test": "test.parquet", "validation": "validation.parquet"},
    ),
}


def load_offline_dataset(dataset_path, dataset_config_name, *args, **kwargs):
    route = ROUTES.get((dataset_path, dataset_config_name))
    if route is None:
        return ORIGINAL_DOWNLOAD_DATASET_WORKER(dataset_path, dataset_config_name, *args, **kwargs)
    directory, loader, filenames = route
    base = DATA_ROOT / directory
    data_files = {split: str(base / filename) for split, filename in filenames.items()}
    missing = [path for path in data_files.values() if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"Offline dataset cache is incomplete for {dataset_path}: {missing}")
    return load_dataset(loader, data_files=data_files)


task_module.download_dataset_worker = load_offline_dataset
TASKS_TABLE = []
