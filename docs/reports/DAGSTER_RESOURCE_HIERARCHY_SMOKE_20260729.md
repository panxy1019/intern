# Dagster Resource Hierarchy Smoke Report

## Result

- Dagster job: `k12_e2e_autoscale_nojudge_job`
- Dagster run: `bffe0caa-58c7-4192-b353-120975a38936`
- Dagster status: `SUCCESS`
- Dagster steps: 139 succeeded, 0 failed
- Dagster wall time: 1375.158 seconds
- Ray job: `k12-autoscale-nojudge-bffe0caa-58c`
- Ray status: `SUCCEEDED`
- Ray pipeline wall time: 1172.245 seconds
- Documents: 10 succeeded, 0 failed
- Qwen requests: 301 completed

Output:

```text
s3://k12-cleaned-corpus/stage2/training-jsonl-collection-nojudge-autoscale-v1/runs/bffe0caa-58c/
```

## Implemented Topology

```text
submit_ray_pipeline_job
└── mineru_worker_pod_ready
    ├── mineru_serve_a_ready
    │   └── mineru_serve_a_books
    │       └── book -> MinerU -> Cleaning -> QA/MCQ
    │           -> Schema Validate -> MinIO Write
    └── mineru_serve_b_ready
        └── mineru_serve_b_books
            └── book -> MinerU -> Cleaning -> QA/MCQ
                -> Schema Validate -> MinIO Write

first_cleaning_output_ready
├── qa_8_9_worker_pod_ready
│   ├── qa_8_9_vllm_8_ready -> actual book/block assignments
│   └── qa_8_9_vllm_9_ready -> actual book/block assignments
├── qa_10_11_worker_pod_ready
│   ├── qa_10_11_vllm_10_ready -> actual book/block assignments
│   └── qa_10_11_vllm_11_ready -> actual book/block assignments
└── qa_12_13_worker_pod_ready
    ├── qa_12_13_vllm_12_ready -> actual book/block assignments
    └── qa_12_13_vllm_13_ready -> actual book/block assignments
```

MinerU books are expanded from `_MINERU_ROUTING_PLAN.json`, so each book is
shown under its actual A/B service. Qwen uses continuous batching; therefore a
book may appear under multiple vLLM services. Each resource-centric node shows
the real request count, block IDs, queue wait, and processing time.

## Physical Mapping

| Worker group | Pod | Serve | Chip | Requests |
|---|---|---|---:|---:|
| qa-8-9 | `...qa-8-9-worker-vc589` | `qa-8-9-vllm-8` | 8 | 43 |
| qa-8-9 | `...qa-8-9-worker-vc589` | `qa-8-9-vllm-9` | 9 | 55 |
| qa-10-11 | `...qa-10-11-worker-hsfwd` | `qa-10-11-vllm-10` | 10 | 47 |
| qa-10-11 | `...qa-10-11-worker-hsfwd` | `qa-10-11-vllm-11` | 11 | 40 |
| qa-12-13 | `...qa-12-13-worker-n5c7c` | `qa-12-13-vllm-12` | 12 | 47 |
| qa-12-13 | `...qa-12-13-worker-n5c7c` | `qa-12-13-vllm-13` | 13 | 54 |

The actor derives this identity from the actual Kubernetes Pod name and local
service port after Ray placement. It no longer assumes logical `pod_index`
matches a physical worker group.

## Lifecycle Verification

- MinerU physical chips 14 and 15 were used by two independent services.
- QA physical chips 8 through 13 were used by six independent TP1 services.
- QA workers were not started before the first Stage 1 cleaning output.
- Cleaning, remaining MinerU work, and QA overlapped across books.
- Autoscaling events contain requested, ready, draining, and released states.
- Twelve resource release events were recorded.
- After completion, all MinerU and QA NPU Worker Pods were removed.
- Dagster webserver and daemon remained healthy with no restart.

