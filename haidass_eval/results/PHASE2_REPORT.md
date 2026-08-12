# Phase 2: Single-NPU LightEval Smoke

## Result

- Date: 2026-08-12 UTC
- Model revision: `6f668e57712b756024425dff07c931b55636091f`
- Worker: `gpu-server-00`, Ascend 910B3, one visible NPU
- Runtime: Python 3.10, torch 2.7.1, torch_npu 2.7.1
- Evaluator: LightEval 0.9.2, Transformers/Accelerate backend
- Task: ARC-Easy, zero-shot, 16 test samples
- `acc`: 0.6875, stderr 0.119678
- `acc_norm`: 0.6875, stderr 0.119678
- LightEval wall time: 35.245 seconds
- LightEval reported evaluation time: 13.178 seconds

This is a partial smoke result and is not comparable with a full ARC-Easy run.

## NPU Evidence

Accelerate completed its gather test on `npu:0`. LightEval then loaded the BF16
model on the NPU. The separate generation smoke reported:

```text
device: npu:0
model load: 2.872 seconds
generation: 2.059 seconds
allocated HBM: 286,299,136 bytes
```

## Data Path

The 910B node could not reliably reach Hugging Face through the configured
proxy. The three official ARC-Easy Parquet splits were therefore downloaded on
`server-00` and shipped in the Ray working directory. The custom task changes
only dataset transport; it reuses LightEval 0.9.2's ARC prompt and its
`loglikelihood_acc` and `loglikelihood_acc_norm_nospace` metrics.

## Artifacts

- `phase2-smoke/phase2_summary.json`: phase timings and generation smoke
- `phase2-smoke/lighteval.log`: full evaluator log
- `phase2-smoke/lighteval-artifacts/results_*.json`: aggregate metrics
- `phase2-smoke/lighteval-artifacts/<timestamp>/details_*.parquet`: 16 sample details

After completion, no evaluation process remained. Ray reported zero CPU and NPU
resource usage while the Head and one Worker stayed Ready.
