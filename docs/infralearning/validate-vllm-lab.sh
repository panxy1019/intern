#!/usr/bin/env bash
set -euo pipefail

namespace=infra-learning
kctl() { k3s kubectl "$@"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

kctl get namespace "$namespace" >/dev/null
kctl -n "$namespace" get service ray-vllm-lab-head >/dev/null
head_pod=$(kctl -n "$namespace" get pod -l app=ray-vllm-lab-head \
  -o jsonpath='{.items[0].metadata.name}')
[[ -n "$head_pod" ]] || fail "Head Pod not found"
[[ $(kctl -n "$namespace" get pod "$head_pod" -o jsonpath='{.status.phase}') == Running ]] \
  || fail "Head is not Running"

active=0
for spec in \
  "ray-vllm-lab-worker-4a|8,9,10,11|4|VLLM_LAB_4A" \
  "ray-vllm-lab-worker-4b|12,13,14,15|4|VLLM_LAB_4B" \
  "ray-vllm-lab-worker-8|8,9,10,11,12,13,14,15|8|VLLM_LAB_8"; do
  IFS='|' read -r deployment physical_ids count resource <<<"$spec"
  desired=$(kctl -n "$namespace" get deploy "$deployment" -o jsonpath='{.spec.replicas}')
  [[ "$desired" == 0 ]] && continue
  active=$((active + 1))
  pod=$(kctl -n "$namespace" get pod -l "app=$deployment" \
    -o jsonpath='{.items[0].metadata.name}')
  [[ -n "$pod" ]] || fail "$deployment Pod not found"
  [[ $(kctl -n "$namespace" get pod "$pod" -o jsonpath='{.spec.schedulerName}') == default-scheduler ]] \
    || fail "$pod is not using default-scheduler"
  [[ $(kctl -n "$namespace" get pod "$pod" -o jsonpath='{.spec.nodeName}') == a3-server-00 ]] \
    || fail "$pod is not on a3-server-00"
  annotation=$(kctl -n "$namespace" get pod "$pod" \
    -o jsonpath='{.metadata.annotations.huawei\.com/Ascend910}')
  expected=$(sed 's/[0-9]\+/Ascend910-&/g; s/,Ascend910-/,Ascend910-/g' <<<"$physical_ids")
  [[ "$annotation" == "$expected" ]] || fail "$pod annotation=$annotation expected=$expected"
  request=$(kctl -n "$namespace" get pod "$pod" \
    -o jsonpath='{.spec.containers[0].resources.requests.huawei\.com/Ascend910}')
  limit=$(kctl -n "$namespace" get pod "$pod" \
    -o jsonpath='{.spec.containers[0].resources.limits.huawei\.com/Ascend910}')
  [[ "$request" == "$count" && "$limit" == "$count" ]] || fail "$pod NPU request/limit mismatch"
  kctl -n "$namespace" exec "$pod" -c ray-worker -- \
    python3 /opt/vllm-lab/discover_npu_mapping.py \
      --physical-ids "$physical_ids" --output /tmp/vllm-lab/npu-mapping.json >/dev/null
  kctl -n "$namespace" exec "$pod" -c ray-worker -- \
    test -f /tmp/vllm-lab/npu-mapping.json
  echo "OK: $pod physical=$physical_ids resource=$resource"
done

rep_4a=$(kctl -n "$namespace" get deploy ray-vllm-lab-worker-4a -o jsonpath='{.spec.replicas}')
rep_4b=$(kctl -n "$namespace" get deploy ray-vllm-lab-worker-4b -o jsonpath='{.spec.replicas}')
rep_8=$(kctl -n "$namespace" get deploy ray-vllm-lab-worker-8 -o jsonpath='{.spec.replicas}')
(( rep_8 == 0 || (rep_4a == 0 && rep_4b == 0) )) || fail "overlapping Worker modes"
kctl get podgroup -A 2>/dev/null | grep -q infra-learning && fail "unexpected Volcano PodGroup"
ray_status=$(kctl -n "$namespace" exec "$head_pod" -c ray-head -- ray status)
grep -q "VLLM_LAB_4A\\|VLLM_LAB_4B\\|VLLM_LAB_8" <<<"$ray_status" \
  || fail "active Worker custom Ray resource is missing"
grep -qE '[0-9.]+/[0-9.]+ NPU$' <<<"$ray_status" \
  && fail "generic NPU resource must not be registered"
echo "$ray_status"
echo "OK: Head, current mode, mapping and Ray registration validated (active groups=$active)."
