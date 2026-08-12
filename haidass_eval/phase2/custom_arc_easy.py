import os
from pathlib import Path

from datasets import load_dataset

import lighteval.tasks.lighteval_task as task_module
from lighteval.metrics.metrics import Metrics
from lighteval.tasks import default_prompts as prompt
from lighteval.tasks.lighteval_task import LightevalTaskConfig


DATA_DIR = Path(os.environ["LOCAL_ARC_DATA_DIR"])


def load_local_arc_dataset(*_args, **_kwargs):
    return load_dataset(
        "parquet",
        data_files={
            "train": str(DATA_DIR / "train.parquet"),
            "validation": str(DATA_DIR / "validation.parquet"),
            "test": str(DATA_DIR / "test.parquet"),
        },
    )


# LightEval 0.9.2 has no data_files field in LightevalTaskConfig. Keep its
# official ARC task semantics and replace only the dataset transport.
task_module.download_dataset_worker = load_local_arc_dataset

arc_easy_offline = LightevalTaskConfig(
    name="arc_easy_offline",
    suite=["custom"],
    prompt_function=prompt.arc,
    hf_repo="local_arc_easy_parquet",
    hf_subset="ARC-Easy",
    hf_avail_splits=["train", "validation", "test"],
    evaluation_splits=["test"],
    few_shots_split=None,
    few_shots_select="random_sampling_from_train",
    generation_size=1,
    metric=[Metrics.loglikelihood_acc, Metrics.loglikelihood_acc_norm_nospace],
    stop_sequence=["\n"],
    trust_dataset=False,
    version=0,
)

TASKS_TABLE = [arc_easy_offline]
