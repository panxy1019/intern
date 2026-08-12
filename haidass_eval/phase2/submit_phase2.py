import json
import os
from pathlib import Path

import ray


RUN_NAME = os.environ.get("LIGHTEVAL_RUN_NAME", "phase2-smoke")
RESULT_ARCHIVE = Path(
    os.environ.get("RESULT_ARCHIVE", f"/tmp/haidass-{RUN_NAME}-results.tar.gz")
)


@ray.remote(num_cpus=8, resources={"NPU": 1, "HAIDASS_EVAL": 1}, max_retries=0)
def evaluate_on_910b():
    from worker_eval import main

    return main()


working_dir = str(Path(__file__).resolve().parent)
forwarded_env = {
    name: os.environ[name]
    for name in [
        "LIGHTEVAL_MAX_SAMPLES",
        "LIGHTEVAL_TASKS",
        "LIGHTEVAL_BATCH_SIZE",
        "LIGHTEVAL_RUN_NAME",
        "MODEL_DIR",
    ]
    if name in os.environ
}
ray.init(
    address="auto",
    runtime_env={"working_dir": working_dir, "env_vars": forwarded_env},
)
summary, archive = ray.get(evaluate_on_910b.remote())
RESULT_ARCHIVE.write_bytes(archive)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(f"RESULT_ARCHIVE={RESULT_ARCHIVE}")
