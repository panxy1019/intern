#!/usr/bin/env bash
set -euo pipefail

: "${KUBECONFIG:=/home/admin/k3s.yaml}"
export KUBECONFIG
WORKER_POD="$(kubectl -n ds get pod -l dsv4.openai.com/device-set=phy-2-9 -o jsonpath='{.items[0].metadata.name}')"
[[ -n "${WORKER_POD}" ]] || { echo "No TP8 Worker Pod found." >&2; exit 1; }
kubectl -n ds exec "${WORKER_POD}" -- /bin/bash /opt/dsv4-vllm/control/status-vllm.sh
