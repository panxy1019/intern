# Haidass LightEval Ascend Phase 3 Final Report

## Executive Summary

Phase 3 completed both tracks on `gpu-server-00` (Ascend 910B3):

- Track A replaced the permanent evaluation Worker pattern with an on-demand RayJob workflow. A temporary CPU Head and one-NPU Worker are created per run, results are written to persistent host storage, and the cluster is deleted after the configured 300-second TTL.
- Track B proved that the verl base can run LightEval on NPU, produced and pushed a reproducible candidate image, and passed full PIQA/HellaSwag regression plus RayJob integration.
- The verl image is retained as `CANDIDATE_PASS_NOT_PROMOTED`. It is functionally correct, but substantially larger and more complex than demo-base, so demo-base remains the known-good production default.

```text
FINAL_WORKER_IMAGE=110.120.0.3:8889/eval/lighteval-ascend-worker@sha256:c306886142f07d1de4e7df85be7239f88f26e2c26a9928077edf1ca0af52dd47
FALLBACK_WORKER_IMAGE=110.120.0.3:8889/eval/lighteval-ascend-worker@sha256:c306886142f07d1de4e7df85be7239f88f26e2c26a9928077edf1ca0af52dd47
CANDIDATE_WORKER_IMAGE=110.120.0.3:8889/eval/lighteval-ascend-worker@sha256:6dad3c708cc42c9d1edc40c9188911b3db788c2f4d97e1492b9adedb75a013b6
```

## Architecture

```text
submit_eval.sh on server-00
          |
          v
RayJob CRD (HTTPMode)
          |
          +--> temporary Ray Head on server-00 (CPU=0 for Ray tasks)
          |          |
          |          +--> run_eval_job.py
          |                  |
          |                  +--> Ray task requiring NPU=1, HAIDASS_EVAL=1
          |
          +--> temporary Worker on gpu-server-00
                       |-- one huawei.com/Ascend910
                       |-- /cache/models       read-only host cache
                       |-- /cache/datasets     read-only host cache
                       |-- /results            read-write persistent storage
                       |-- official LightEval accelerate execution
                       |-- details + bad-case analysis
                       v
             /data/haidass-eval/results/<run-id>

Job succeeds -> wait 300 seconds -> RayCluster/Head/Worker deleted -> results remain
```

## Track A

### Immutable Worker Image

The image is built from the exact requested base digest:

```text
110.120.0.3:8889/demo:v2@sha256:1ec90a9d8202cceb0f89b575b0d9773b3e18a92bdb00a855a6a2fc375f0dcee3
```

Only LightEval 0.9.2, its offline pure-Python dependencies, and Phase 3 runner files are added with `pip --no-index --no-deps`. Torch, torch_npu, Transformers, Accelerate, datasets, and NumPy are not installed or upgraded. The final image is 7,082,662,557 bytes.

Audit evidence is stored under `images/demo-base/`: Dockerfile, full image inspect, history, pip freeze, and digest.

### Persistent Cache Layout

```text
/data/haidass-eval/
├── models/Haidass-143M-v1/
├── datasets/
│   ├── piqa/
│   ├── hellaswag/
│   └── arc_easy/
└── results/<run-id>/
```

Each available model and dataset has a JSON manifest with source/revision, file list, SHA256, cache time, split names, and sample count where applicable. The router already contains fixed mappings for all requested aliases. MMLU, ARC-Challenge, WinoGrande, and OpenBookQA still require their local cache to be populated before use.

### RayJob Lifecycle Smoke

Successful smoke:

```text
RayJob: eval-hellaswag-020156-2910
Run ID: 20260813T020156Z_Haidass-143M-v1_hellaswag_c976f2
Task: HellaSwag, 16 samples, batch size 4
LightEval elapsed: 36.119 seconds
Result: SUCCEEDED
```

Observed lifecycle:

1. RayJob created a new RayCluster.
2. Head became ready on `server-00`.
3. Worker was scheduled on `gpu-server-00` with one distinct `Ascend910` allocation.
4. Ray registered `NPU=1` and `HAIDASS_EVAL=1`; the driver dispatched only to that Worker.
5. LightEval wrote the result JSON, details parquet, log, manifest, summary and bad-case files to `/results`.
6. The controller logged the exact shutdown deadline and deleted the RayCluster after 300 seconds.
7. Results remained available after Head and Worker deletion.

### Full Results

| Image | Task | Samples | acc | acc_norm | Bad-case union | Runtime |
|---|---|---:|---:|---:|---:|---:|
| demo-base | PIQA | 1838 | 0.6708378672 | 0.6741022851 | 787 | 49.404 s |
| demo-base | HellaSwag | 10042 | 0.3235411273 | 0.3799044015 | 8106 | 328.643 s |

The results exactly match the historical baseline.

## Track B

### Base Audit And Isolated Environment

The tested base is arm64, 17,412,789,016 bytes, with CANN 8.3.RC1 and a Conda environment named `verl_pt27_25rc3`. Its relevant versions are:

| Component | Version |
|---|---|
| Python | 3.10.0 |
| torch | 2.7.1 |
| torch_npu | 2.7.1 |
| Transformers | 4.56.0.dev0 |
| Accelerate | 1.10.1 |
| datasets | 3.6.0 |
| base Ray | 2.49.0 |
| candidate venv Ray | 2.10.0 |
| LightEval | 0.9.2 |

The venv at `/opt/venvs/lighteval092` uses `--system-site-packages`, so torch and torch_npu continue to load from the original Conda environment. Ray 2.10 is isolated in the venv to match the production Head.

### Validation Gates

All required gates passed: BF16 NPU matmul, venv inheritance, Accelerate NPU detection, Haidass forward, LightEval import, HellaSwag 16 samples, final image NPU smoke, and RayJob integration.

The first integration attempt intentionally exposed the Ray 2.49/2.10 incompatibility in the init container. The final image fixes this reproducibly by adding the arm64 Ray 2.10 wheel to the venv and putting that venv first in image `PATH`. No base package was uninstalled.

### Final Regression

| Image | Task | Samples | acc | acc_norm | Bad-case union | Runtime |
|---|---|---:|---:|---:|---:|---:|
| verl candidate | PIQA | 1838 | 0.6708378672 | 0.6741022851 | 787 | 45.761 s |
| verl candidate | HellaSwag | 10042 | 0.3235411273 | 0.3799044015 | 8106 | 331.856 s |

For both tasks, metrics, sample counts, details parquet schema, and all bad-case counts are equal to demo-base. The machine-readable comparison is in `results/PHASE3_REGRESSION_COMPARISON.json`.

### Promotion Decision

The candidate passed functionality and regression, but its final size is 17,553,455,158 bytes, approximately 2.48 times demo-base. It also carries verl training packages and retains base Ray 2.49 beneath the evaluation venv. This fails the “simpler or no more complex” promotion condition.

Decision:

```text
CANDIDATE_PASS_NOT_PROMOTED
stable alias: not created
demo-base: KNOWN_GOOD_FALLBACK and production default
```

## Required Questions

| # | Question | Answer |
|---:|---|---|
| 1 | Has RayJob replaced the permanent NPU RayCluster? | Yes. The old evaluation RayCluster is retired after validation. |
| 2 | Is the Worker created on demand? | Yes, one Worker per RayJob. |
| 3 | Is the Worker automatically released? | Yes, after the configured 300-second completion TTL. |
| 4 | Is the model directly mounted from cache? | Yes, read-only from `/data/haidass-eval/models`. |
| 5 | Is the benchmark directly mounted from cache? | Yes, read-only from `/data/haidass-eval/datasets`. |
| 6 | Are results persistent? | Yes, under `/data/haidass-eval/results`. |
| 7 | Does a new checkpoint need only model/task parameters? | Yes, after its directory and manifest are placed in the model cache. |
| 8 | Can the verl base perform NPU evaluation? | Yes. |
| 9 | Does the isolated venv work? | Yes. |
| 10 | Does LightEval work? | Yes, version 0.9.2. |
| 11 | Did HellaSwag smoke pass? | Yes. |
| 12 | Did full PIQA/HellaSwag regression pass? | Yes, exact metric/schema/count equality. |
| 13 | Was a candidate image built and pushed? | Yes. |
| 14 | What is its digest? | `sha256:6dad3c708cc42c9d1edc40c9188911b3db788c2f4d97e1492b9adedb75a013b6`. |
| 15 | Is it `PROMOTED_BASE`? | No; `CANDIDATE_PASS_NOT_PROMOTED` due to size and runtime complexity. |

## Operations

Use `track-a-rayjob/submit_eval.sh`; its output prints the RayJob name, run ID, result directory and watch command. Immutable image choices and the promotion decision are recorded in `image-lock.json`.
