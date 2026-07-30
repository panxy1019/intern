# 10-Book E2E Qwen Pipeline Profile

## Run

- Dagster Run: `5fb12e24-c477-49d5-bfca-12b87686a4a2`
- Ray Job: `k12-e2e-5fb12e24-c47`
- Status: `10/10 success`
- Wall time: `1636.438s`
- MinerU devices: physical NPU 12 and 13
- Qwen devices: physical NPU 14 and 15
- Stage 2: `stage2-v1.1.0`
- Prompt: `k12-qa-zh-v1.2`

## Qwen Queue And Continuous Batching

| Metric | Value |
|---|---:|
| Logical generation requests | 301 |
| Logical judge requests | 92 |
| HTTP responses processed | 480 |
| Retries | 87 |
| Request errors | 108 |
| Generation queue wait P50 / P95 / max | 181.300 / 246.294 / 276.204s |
| Judge queue wait P50 / P95 / max | 78.425 / 173.644 / 208.479s |
| Coordinator peak generation waiting / active | 63 / 8 |
| Coordinator peak judge waiting / active | 31 / 4 |
| vLLM running active-window average / max | 7.040 / 8 |
| vLLM full-8 active-window sample ratio | 68.29% |
| vLLM waiting active-window average / max | 1.203 / 4 |
| vLLM waiting-positive active-window ratio | 34.08% |
| Longest continuous vLLM busy interval | 1480.864s |
| Prompt / generation token throughput | 364.579 / 265.351 tokens/s |

The Qwen service had no empty sample inside its 1480.363-second active window.
Generation used all eight configured slots. When four judge requests were also
admitted, vLLM reported eight running and up to four waiting requests. The
pipeline therefore supplies enough work for continuous batching; its main
queue is now model capacity rather than S3, MinerU, or cleaning.

## Cross-Book Pipeline Overlap

| Overlap | Seconds |
|---|---:|
| MinerU and QA | 327.217 |
| Cleaning and QA | 3.381 |
| MinerU, cleaning, and QA | 3.381 |

The first book entered QA at 153.380s while the MinerU lanes continued until
480.057s. Compared with a strict parse-all-then-QA barrier, book-level
handoff hides about 327 seconds of parsing wall time in this batch.

Cleaning takes only 0.548-1.452 seconds per book, so its overlap interval is
small by design and it is not a throughput bottleneck.

## Per-Book Results

| Document | MinerU s | Clean s | QA s | QA verified | MCQ verified |
|---|---:|---:|---:|---:|---:|
| `pdf-06ab075c00ea72f24632` | 83.267 | 0.548 | 1104.849 | 33 | 31 |
| `pdf-0060e203e21be9105143` | 74.180 | 0.585 | 1136.832 | 36 | 37 |
| `pdf-054b5b0ca11e91b3ec5f` | 78.944 | 1.368 | 955.995 | 18 | 17 |
| `pdf-04711a86294f2460d3c0` | 151.927 | 1.452 | 596.125 | 26 | 21 |
| `pdf-02db6b2a6b60aace09c0` | 77.745 | 1.356 | 992.560 | 36 | 37 |
| `pdf-04ab7061e1e77834d3a5` | 78.893 | 1.317 | 1241.181 | 38 | 40 |
| `pdf-027fd22e4cc4e6bca066` | 166.663 | 0.675 | 570.083 | 31 | 30 |
| `pdf-0308c393b2b253506e45` | 85.224 | 1.425 | 847.490 | 36 | 35 |
| `pdf-07664f2000b3860da5a0` | 78.523 | 0.593 | 1114.412 | 38 | 37 |
| `pdf-00449534271c4dbe19d5` | 77.421 | 0.604 | 1292.773 | 41 | 41 |

- QA candidates / verified: `369 / 333`
- MCQ candidates / verified: `367 / 326`
- Total verified training items: `659`
- Aggregate candidate acceptance: `89.54%`

## Conclusion

1. Book-level MinerU, cleaning, and QA handoff is working and materially
   overlaps the two NPU worker groups.
2. Qwen is continuously supplied: during its active interval, running requests
   never dropped to zero and reached eight in 68.29% of samples.
3. The current `generation=8` plus `judge=4` configuration deliberately creates
   a small vLLM queue of up to four requests. It maintains full batches but
   should not be increased before raising or re-testing vLLM scheduling
   capacity.
4. The large Coordinator queue is expected when ten books release up to 48
   generation units each. Increasing book or block inflight would increase
   latency without improving this two-NPU service's throughput.
5. The next optimization target is response reliability: 87 retries and 21
   exhausted logical requests indicate that JSON/prompt conformance can be
   improved independently of model scheduling.
