#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-haidass-eval}"
PROJECT_DIR="${PROJECT_DIR:-/home/admin/haidass_eval}"
RESULT_DIR="${RESULT_DIR:-$PROJECT_DIR/results}"
KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
LIGHTEVAL_MAX_SAMPLES="${LIGHTEVAL_MAX_SAMPLES:-16}"
LIGHTEVAL_TASKS="${LIGHTEVAL_TASKS:-lighteval|arc:easy|0|0}"
LIGHTEVAL_BATCH_SIZE="${LIGHTEVAL_BATCH_SIZE:-1}"
LIGHTEVAL_RUN_NAME="${LIGHTEVAL_RUN_NAME:-phase2-smoke}"
MODEL_DIR="${MODEL_DIR:-/cache/models/Haidass-143M-v1}"

if [[ ! "$LIGHTEVAL_RUN_NAME" =~ ^[a-zA-Z0-9._-]+$ ]]; then
  echo "Invalid LIGHTEVAL_RUN_NAME: $LIGHTEVAL_RUN_NAME" >&2
  exit 2
fi

HEAD=$(kubectl --kubeconfig "$KUBECONFIG" -n "$NAMESPACE" get pod \
  -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}')
REMOTE_DIR="/tmp/haidass-phase2-$(date -u +%Y%m%dT%H%M%SZ)"

kubectl --kubeconfig "$KUBECONFIG" -n "$NAMESPACE" cp \
  "$PROJECT_DIR/phase2" "$HEAD:$REMOTE_DIR"

kubectl --kubeconfig "$KUBECONFIG" -n "$NAMESPACE" exec "$HEAD" -- \
  env \
    LIGHTEVAL_MAX_SAMPLES="$LIGHTEVAL_MAX_SAMPLES" \
    LIGHTEVAL_TASKS="$LIGHTEVAL_TASKS" \
    LIGHTEVAL_BATCH_SIZE="$LIGHTEVAL_BATCH_SIZE" \
    LIGHTEVAL_RUN_NAME="$LIGHTEVAL_RUN_NAME" \
    MODEL_DIR="$MODEL_DIR" \
    python "$REMOTE_DIR/submit_phase2.py"

mkdir -p "$RESULT_DIR"
kubectl --kubeconfig "$KUBECONFIG" -n "$NAMESPACE" cp \
  "$HEAD:/tmp/haidass-$LIGHTEVAL_RUN_NAME-results.tar.gz" \
  "$RESULT_DIR/haidass-$LIGHTEVAL_RUN_NAME-results.tar.gz"
tar -xzf "$RESULT_DIR/haidass-$LIGHTEVAL_RUN_NAME-results.tar.gz" -C "$RESULT_DIR"
echo "Results: $RESULT_DIR/$LIGHTEVAL_RUN_NAME"
