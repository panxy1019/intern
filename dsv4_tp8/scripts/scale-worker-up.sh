#!/usr/bin/env bash
set -euo pipefail

: "${KUBECONFIG:=/home/admin/k3s.yaml}"
export KUBECONFIG

if [[ "${DSV4_NPU_GATE_PASSED:-}" != "yes" ]]; then
  echo "Refusing to scale: set DSV4_NPU_GATE_PASSED=yes only after the host gate passes." >&2
  exit 51
fi

if [[ "${ALLOW_VOLCANO_KUBERAY_WORKER:-}" != "yes" ]]; then
  echo "Refusing KubeRay worker scaling: the cluster-wide Volcano scheduler rejects Phy-ID 2..9." >&2
  echo "Use deployment/dsv4-tp8-worker-fixed-2-9 for this device set." >&2
  exit 52
fi

kubectl -n ds patch raycluster dsv4-tp8 --type=json -p='[
  {"op":"replace","path":"/spec/workerGroupSpecs/0/minReplicas","value":1},
  {"op":"replace","path":"/spec/workerGroupSpecs/0/replicas","value":1}
]'
