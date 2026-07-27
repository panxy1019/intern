#!/usr/bin/env bash
set -euo pipefail

namespace=infra-learning
deploy_4a=ray-vllm-lab-worker-4a
deploy_4b=ray-vllm-lab-worker-4b
deploy_8=ray-vllm-lab-worker-8
mode=${1:-status}

kctl() { k3s kubectl "$@"; }
replicas() {
  kctl -n "$namespace" get deploy "$1" -o jsonpath='{.spec.replicas}'
}
pods_for() {
  kctl -n "$namespace" get pod -l "app=$1" -o name
}
reject_running_vllm() {
  local deployment pod
  for deployment in "$deploy_4a" "$deploy_4b" "$deploy_8"; do
    while read -r pod; do
      [[ -z "$pod" ]] && continue
      if ! processes=$(kctl -n "$namespace" exec "${pod#pod/}" -c ray-worker -- \
        sh -c 'pgrep -af "vllm serve" || true'); then
        echo "Cannot inspect ${pod#pod/}; state is unknown, fail closed." >&2
        exit 1
      fi
      if [[ -n "$processes" ]]; then
        echo "Refusing mode switch: vLLM is running in ${pod#pod/}." >&2
        echo "Stop it manually, then retry." >&2
        exit 1
      fi
    done < <(pods_for "$deployment")
  done
}
scale_zero() {
  local deployment=$1
  kctl -n "$namespace" scale deploy "$deployment" --replicas=0
  if [[ -n "$(pods_for "$deployment")" ]]; then
    kctl -n "$namespace" wait --for=delete pod \
      -l "app=$deployment" --timeout=180s || {
        echo "Pods for $deployment did not fully terminate; fail closed." >&2
        exit 1
      }
  fi
}
check_target_unclaimed() {
  local ids=$1 found
  found=$(kctl get pod -A -o json | jq -r --arg ns "$namespace" --arg ids "$ids" '
    .items[]
    | select(.metadata.namespace != $ns)
    | (.metadata.annotations["huawei.com/Ascend910"] // "") as $a
    | select(any(($ids | split(","))[]; . as $id | $a | contains("Ascend910-" + $id)))
    | .metadata.namespace + "/" + .metadata.name + " " + $a
  ')
  if [[ -n "$found" ]]; then
    echo "Target devices are claimed by other Pods:" >&2
    echo "$found" >&2
    exit 1
  fi
}
status() {
  printf '4A=%s 4B=%s 8=%s\n' \
    "$(replicas "$deploy_4a")" "$(replicas "$deploy_4b")" "$(replicas "$deploy_8")"
  kctl -n "$namespace" get pod -o wide
}

case "$mode" in
  status)
    status
    exit 0
    ;;
  4|4x2|8|off) ;;
  *)
    echo "Usage: $0 {4|4x2|8|off|status}" >&2
    exit 2
    ;;
esac

reject_running_vllm
scale_zero "$deploy_4a"
scale_zero "$deploy_4b"
scale_zero "$deploy_8"

case "$mode" in
  4)
    check_target_unclaimed "8,9,10,11"
    kctl -n "$namespace" scale deploy "$deploy_4a" --replicas=1
    ;;
  4x2)
    check_target_unclaimed "8,9,10,11,12,13,14,15"
    kctl -n "$namespace" scale deploy "$deploy_4a" "$deploy_4b" --replicas=1
    ;;
  8)
    check_target_unclaimed "8,9,10,11,12,13,14,15"
    kctl -n "$namespace" scale deploy "$deploy_8" --replicas=1
    ;;
  off) ;;
esac

status
