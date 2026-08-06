#!/usr/bin/env bash
set -euo pipefail

: "${KUBECONFIG:=/home/admin/k3s.yaml}"
export KUBECONFIG
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kubectl apply -f "${SCRIPT_DIR}/../k8s/26-vllm-control-config.yaml"
echo "ConfigMap updated. Verify the mounted args before starting or restarting vLLM."
