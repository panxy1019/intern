# Dagster Autoscale Observability

## Scope

This observability layer applies to `k12_e2e_autoscale_nojudge_job`.
It does not change Ray placement groups, least-inflight routing, model
concurrency, KubeRay replica limits, or resource-release conditions.

## Dagster Graph

The resource branch contains:

```text
mineru_worker_pod
├── mineru_serve_a
└── mineru_serve_b

qa_worker_pod_0_gate
├── qa_worker_pod_0
├── qa_pod_0_vllm_serve_0
└── qa_pod_0_vllm_serve_1

qa_worker_pod_1_gate
├── qa_worker_pod_1
├── qa_pod_1_vllm_serve_0
└── qa_pod_1_vllm_serve_1

qa_worker_pod_2_gate
├── qa_worker_pod_2
├── qa_pod_2_vllm_serve_0
└── qa_pod_2_vllm_serve_1
```

Each QA gate has an optional output. If KubeRay never requests that pod, its
Pod and Serve lifecycle nodes are shown as skipped.

Pod and Serve nodes replay the persisted lifecycle immediately after the Ray
job completes. They do not occupy long-running Dagster worker processes while
the models are active. Live resource assignments remain available in the Ray
progress file and logs; the book-level nodes are the live Dagster view.

The book branch is dynamically mapped by `document_id`:

```text
book_mineru[book_id]
  -> book_cleaning[book_id]
  -> book_qa_mcq[book_id]
  -> book_schema_validate[book_id]
  -> book_minio_write[book_id]
```

Different books can occupy different stages at the same time. Completing
Cleaning for one book immediately unlocks its QA/MCQ node; it does not wait
for the remaining books.

## Metadata

MinerU book nodes expose:

```text
book_id
pod_name
serve_id
actor_id
chip_id
queue_wait
processing_time
page_count
```

QA/MCQ book nodes expose the actual continuous-batching assignments:

```text
document_id
block_ids
pod_name
serve_id
actor_id
chip_id
dispatch_queue_wait
serve_queue_wait
queue_wait
processing_time
```

One book is not pinned to one vLLM Serve. The UI reports the actual
block-level least-inflight routing and aggregates the Serve IDs used by each
book.

## Lifecycle

Pod and Serve observers log and retain:

```text
requested -> ready -> busy -> draining -> released
```

`busy` is derived from live Ray assignments in `_PROGRESS.json`. Requested,
ready, draining, and released are persisted in
`_AUTOSCALING_EVENTS.json`.

Per-book Stage 2 markers are persisted at:

```text
<stage2_prefix>/<document_id>/_OBSERVABILITY.json
```

The final `_SUCCESS.json` remains the last committed document marker.

## UI Status Meaning

- Yellow: the underlying Ray stage or lifecycle is still active.
- Green: the observed stage completed successfully.
- Red: the document failed, Ray stopped/failed, or the expected output was
  not produced.
- Gray/skipped: the corresponding optional QA Pod was never requested.

Dagster's multiprocess executor is capped at six observer processes. This
limit affects only how many UI polling nodes are live at once; it does not
limit Ray document concurrency or vLLM continuous batching.

## 2026-07-29 OOM Correction

The first visualization run used `max_concurrent=24` and started long-lived
Pod, Serve, and book pollers together. The Dagster daemon container exceeded
its 4 GiB limit and was OOMKilled. Ray remained independent and completed all
10 books successfully, but the Dagster run became orphaned.

The corrected graph:

1. caps polling subprocesses at six;
2. keeps only book stages as live pollers;
3. replays Pod and Serve lifecycle nodes after the Ray summary is committed;
4. preserves the original Ray/KubeRay concurrency and scale-to-zero behavior.
