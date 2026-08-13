# verl Candidate Smoke Report

## Candidate

```text
110.120.0.3:8889/eval/lighteval-ascend-worker@sha256:6dad3c708cc42c9d1edc40c9188911b3db788c2f4d97e1492b9adedb75a013b6
```

Base image:

```text
swr.cn-south-1.myhuaweicloud.com/ascendhub/verl_pt27_25rc3@sha256:4bd09b37b843d2f7a415cc35a06888e99e6165fb529a6e90731ed86278ab160a
```

## Gates

| Gate | Result |
|---|---|
| `BASE_NPU_PASS` | PASS, BF16 2048x2048 matmul on Ascend 910B3 |
| `VENV_NPU_PASS` | PASS, torch and torch_npu remain in the original Conda environment |
| `ACCELERATE_NPU_PASS` | PASS, `Accelerator().device.type == "npu"` |
| `HAIDASS_FORWARD_PASS` | PASS, logits on `npu:0` |
| `LIGHTEVAL_IMPORT_PASS` | PASS, LightEval 0.9.2 |
| `HELLASWAG_16_PASS` | PASS, acc 0.4375 / acc_norm 0.6250 |
| Image-level NPU smoke | PASS |
| Ray 2.10 integration smoke | PASS, RayJob `SUCCEEDED` |
| PIQA full regression | PASS |
| HellaSwag full regression | PASS |

The image keeps the base Conda environment intact and creates `/opt/venvs/lighteval092` with `--system-site-packages`. LightEval and pure Python dependencies are installed from the offline wheelhouse. Ray 2.10 is installed only in that venv so the Worker can join the production Ray 2.10 Head; the base Ray 2.49 installation remains unchanged.

## Decision

`CANDIDATE_PASS_NOT_PROMOTED`

The candidate is functionally correct but is about 17.55 GB versus 7.08 GB for demo-base and carries the full verl training runtime. It is retained by immutable digest, but it is not assigned the `stable` alias and does not replace the smaller known-good default.
