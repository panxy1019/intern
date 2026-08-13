import argparse
import json
import re

import ray


@ray.remote(num_cpus=8, resources={"NPU": 1, "HAIDASS_EVAL": 1}, max_retries=0)
def evaluate(model, task, batch_size, max_samples, run_id):
    from worker_eval import run_worker

    return run_worker(model, task, batch_size, max_samples, run_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    for value, name in ((args.model, "model"), (args.run_id, "run-id")):
        if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
            raise ValueError(f"Invalid {name}: {value!r}")
    if args.batch_size < 1 or args.max_samples < 0:
        raise ValueError("batch-size must be positive and max-samples must be non-negative")
    ray.init(address="auto")
    result = ray.get(evaluate.remote(args.model, args.task, args.batch_size, args.max_samples, args.run_id))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
