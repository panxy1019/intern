# Haidass 910B Evaluation Cluster

Phase 1 provisions a Ray 2.10.0 cluster and a pinned copy of
`DALabCommunity/Haidass-143M-v1`. Phase 2 runs a single-NPU LightEval smoke.

## Layout

- Namespace: `haidass-eval`
- RayCluster: `raycluster-haidass-910b`
- Head: `server-00`, amd64, `num-cpus=0`
- Worker: `gpu-server-00`, arm64/Ascend 910B3, one NPU per Pod
- Initial/max workers: `1/8`
- Model store: `/home/admin/models/Haidass-143M-v1` on `server-00`
- Model revision: `6f668e57712b756024425dff07c931b55636091f`

The Head exposes the read-only model directory through the internal
`haidass-model-cache:8081` Service. Worker Pods use local ephemeral storage;
evaluation tasks can stream or cache the model without relying on a cross-node
`hostPath`.

## Status

Run these commands on `server-00` as root, or prefix them with `sudo`:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl -n haidass-eval get raycluster,pods,svc,podgroup -o wide
HEAD=$(kubectl -n haidass-eval get pod -l ray.io/node-type=head \
  -o jsonpath='{.items[0].metadata.name}')
kubectl -n haidass-eval exec "$HEAD" -- ray status
```

Re-run the NPU and model-transfer smoke:

```bash
kubectl -n haidass-eval cp scripts/ray_npu_smoke.py \
  "$HEAD:/tmp/ray_npu_smoke.py"
kubectl -n haidass-eval exec "$HEAD" -- python /tmp/ray_npu_smoke.py
```

## Scale Workers

Each replica requests exactly one NPU. Scale only after phase 2 succeeds on one
card:

```bash
kubectl -n haidass-eval patch raycluster raycluster-haidass-910b \
  --type=json \
  -p='[{"op":"replace","path":"/spec/workerGroupSpecs/0/replicas","value":2}]'
```

Use `1` through `8` for `replicas`. Do not change the node driver or CANN from
this project.

## Model Integrity

```bash
cd /home/admin/models/Haidass-143M-v1
sha256sum --check SHA256SUMS
cat REVISION
```

The worker image preflight established the following compatible stack:

```text
Driver 25.5.1
CANN 8.3.RC1
Python 3.10.0
Ray 2.10.0
torch 2.7.1+cpu
torch_npu 2.7.1
Device Ascend910B3
```

## Phase 2 Evaluation

The evaluation uses LightEval 0.9.2 with its Transformers/Accelerate backend.
Dependencies are distributed from `phase2/wheelhouse` and installed under the
Worker cache, so the base Conda environment is not modified.

ARC-Easy uses the official `train`, `validation`, and `test` Parquet files. The
custom task in `phase2/custom_arc_easy.py` preserves LightEval's official ARC
prompt and metrics and replaces only online Hub loading with local Parquet.

Run on `server-00`:

```bash
sudo -i
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
bash /home/admin/haidass_eval/phase2/run_phase2.sh
```

Optional smoke settings:

```bash
LIGHTEVAL_MAX_SAMPLES=32 \
LIGHTEVAL_TASKS='custom|arc_easy_offline|0|0' \
bash /home/admin/haidass_eval/phase2/run_phase2.sh
```

Results are copied from the Worker to:

```text
/home/admin/haidass_eval/results/phase2-smoke
```

The default `max_samples=16` run is a functional smoke only. Do not compare its
partial score with the full benchmark score. Set `LIGHTEVAL_MAX_SAMPLES=0` to
omit the sample limit and run the complete task.
