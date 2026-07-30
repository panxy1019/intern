# Stage 2 8-NPU v1.1 Optimization Report

## Result

- Dagster run: `1f788d1a-7803-4554-88a7-ded509586869`
- Ray job: `stage2-qa-run-1f788d1a`
- Status: success
- Documents: 16/16
- Ray wall time: 935.588 seconds
- Throughput: 61.566 documents/hour
- Required throughput: 40.547 documents/hour
- Projected 2595-document time: 42.15 hours
- Target: 64 hours

## Request Reduction

- Eligible Stage 1 blocks: 8743
- Selected generation units: 768
- Eligible-to-selected reduction: 11.38x
- Judge candidates: 982
- Judge batches: 130
- Average Judge batch: 7.55 candidates

## Quality Gate

All automated gates passed:

- JSON/JSONL parsing
- unique item IDs
- valid Stage 1 block references
- evidence traceability
- math program recheck
- quarantine isolation
- single-correct MCQ structure
- verified-only training exports

Verified outputs:

- QA: 474
- MCQ: 450
- textbook exercise solutions: 65

## Production Defaults

```text
document_inflight=8
block_inflight=4
generation_max_inflight=8
judge_max_inflight=8
http_pool_size=16
microbatch_size=2
merge_max_chars=3200
merge_max_blocks=8
chapter_max_units=12
document_max_units=48
judge_batch_size=8
```

The full job uses a separate `stage2-v1.1.0-8npu` prefix and remains unstarted.
