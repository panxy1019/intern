# Track A: RayJob LightEval

## Submit

Run on `server-00`:

```bash
cd /home/admin/haidass_eval/phase3/track-a-rayjob

sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash submit_eval.sh \
  --model Haidass-143M-v1 \
  --task hellaswag \
  --batch-size 32
```

Optional smoke limit:

```bash
sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash submit_eval.sh \
  --model Haidass-143M-v1 \
  --task hellaswag \
  --batch-size 4 \
  --max-samples 16
```

Supported aliases are `mmlu`, `arc_easy`, `arc_challenge`, `winogrande`, `openbookqa`, `piqa`, and `hellaswag`.

## Monitor

```bash
sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n haidass-eval get rayjob,pod -w
sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n haidass-eval describe rayjob <rayjob-name>
```

The submit command prints the exact persistent result directory. Results remain under:

```text
/data/haidass-eval/results/<run-id>/
```

on `gpu-server-00` after the temporary RayCluster is deleted.

## Add A Model

Place a complete Transformers checkpoint at:

```text
/data/haidass-eval/models/<model-name>/
```

Generate `model_manifest.json`, then pass only `--model <model-name>` and `--task <alias>`. Model names are restricted to letters, digits, dots, underscores, and hyphens.

## Cache Status

Currently ready offline: `piqa`, `hellaswag`, and `arc_easy`. The router has fixed paths for all advertised aliases; aliases whose cache has not yet been populated fail explicitly instead of silently downloading through Ray `working_dir`.
