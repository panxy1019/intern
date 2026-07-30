# Stage 2 Throughput Optimization Report

| Configuration | Wall time | Documents/hour | Candidates/s | Verified/s | Qwen requests | Retries |
|---|---:|---:|---:|---:|---:|---:|
| conservative | 492.959 s | 73.028 | 0.0974 | 0.0588 | 84 | 9 |
| optimized | 205.724 s | 174.992 | 0.2382 | 0.1312 | 80 | 7 |

The optimized configuration was selected: `document_inflight=3`,
`block_inflight=8`, generation inflight `8`, Judge inflight `4`, HTTP pool
`16`, microbatch `2`, and four representative blocks per document.

Generation HTTP latency increased under concurrency (P50/P95 from
10.228/22.531 s to 18.048/35.109 s), but cross-document overlap reduced total
wall time by 58.3% and improved verified throughput by 2.23x without failing
any automated quality gate.

