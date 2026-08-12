import os
from pathlib import Path

from datasets import load_dataset

import lighteval.tasks.lighteval_task as task_module


DATA_ROOT = Path(os.environ["LIGHTEVAL_DATA_ROOT"])
ORIGINAL_DOWNLOAD_DATASET_WORKER = task_module.download_dataset_worker


def load_offline_dataset(dataset_path, dataset_config_name, *args, **kwargs):
    if dataset_path == "ai2_arc" and dataset_config_name == "ARC-Easy":
        base = DATA_ROOT / "ARC-Easy"
        return load_dataset(
            "parquet",
            data_files={
                "train": str(base / "train.parquet"),
                "validation": str(base / "validation.parquet"),
                "test": str(base / "test.parquet"),
            },
        )

    if dataset_path == "ybisk/piqa" and dataset_config_name == "plain_text":
        base = DATA_ROOT / "PIQA"
        return load_dataset(
            "json",
            data_files={
                "train": str(base / "train.jsonl"),
                "validation": str(base / "validation.jsonl"),
            },
        )

    if dataset_path == "hellaswag" and dataset_config_name == "default":
        base = DATA_ROOT / "HellaSwag"
        return load_dataset(
            "parquet",
            data_files={
                "train": str(base / "train.parquet"),
                "validation": str(base / "validation.parquet"),
            },
        )

    return ORIGINAL_DOWNLOAD_DATASET_WORKER(
        dataset_path,
        dataset_config_name,
        *args,
        **kwargs,
    )


task_module.download_dataset_worker = load_offline_dataset

# Importing this module applies the transport patch. Official task definitions
# remain in LightEval's default registry and are selected by their normal names.
TASKS_TABLE = []
