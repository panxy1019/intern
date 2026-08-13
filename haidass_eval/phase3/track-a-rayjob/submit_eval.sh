#!/usr/bin/env bash
set -euo pipefail

MODEL=""
TASK=""
BATCH_SIZE=""
MAX_SAMPLES=0
NAMESPACE="${NAMESPACE:-haidass-eval}"
KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
WORKER_IMAGE="${WORKER_IMAGE:-110.120.0.3:8889/eval/lighteval-ascend-worker@sha256:c306886142f07d1de4e7df85be7239f88f26e2c26a9928077edf1ca0af52dd47}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

while (($#)); do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --task) TASK="$2"; shift 2 ;;
    --batch-size) BATCH_SIZE="$2"; shift 2 ;;
    --max-samples) MAX_SAMPLES="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ "$MODEL" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "Invalid --model" >&2; exit 2; }
[[ "$TASK" =~ ^(mmlu|arc_easy|arc_challenge|winogrande|openbookqa|piqa|hellaswag)$ ]] || { echo "Invalid --task" >&2; exit 2; }
[[ "$BATCH_SIZE" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid --batch-size" >&2; exit 2; }
[[ "$MAX_SAMPLES" =~ ^[0-9]+$ ]] || { echo "Invalid --max-samples" >&2; exit 2; }

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${TIMESTAMP}_${MODEL}_${TASK}_$(openssl rand -hex 3)"
RAYJOB_NAME="eval-$(echo "$TASK" | tr _ -)-$(date -u +%H%M%S)-$(openssl rand -hex 2)"
RENDERED="$(mktemp --suffix=.yaml)"
trap 'rm -f "$RENDERED"' EXIT

kubectl --kubeconfig "$KUBECONFIG" -n "$NAMESPACE" create configmap haidass-phase3-driver-code \
  --from-file="$SCRIPT_DIR/run_eval_job.py" \
  --from-file="$SCRIPT_DIR/task_catalog.py" \
  --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -

sed \
  -e "s|__RAYJOB_NAME__|$RAYJOB_NAME|g" \
  -e "s|__MODEL__|$MODEL|g" \
  -e "s|__TASK__|$TASK|g" \
  -e "s|__BATCH_SIZE__|$BATCH_SIZE|g" \
  -e "s|__MAX_SAMPLES__|$MAX_SAMPLES|g" \
  -e "s|__RUN_ID__|$RUN_ID|g" \
  -e "s|__WORKER_IMAGE__|$WORKER_IMAGE|g" \
  "$SCRIPT_DIR/rayjob-template.yaml" > "$RENDERED"

kubectl --kubeconfig "$KUBECONFIG" apply -f "$RENDERED"
echo "RAYJOB=$RAYJOB_NAME"
echo "RUN_ID=$RUN_ID"
echo "RESULT_DIR=/data/haidass-eval/results/$RUN_ID"
echo "WATCH=kubectl --kubeconfig $KUBECONFIG -n $NAMESPACE get rayjob,pod -w"
