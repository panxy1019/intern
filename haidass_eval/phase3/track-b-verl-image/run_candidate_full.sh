#!/usr/bin/env bash
set -euo pipefail

IMAGE="110.120.0.3:8889/eval/lighteval-ascend-worker@sha256:6dad3c708cc42c9d1edc40c9188911b3db788c2f4d97e1492b9adedb75a013b6"
RESULT_ROOT="/data/haidass-eval/results"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

start_eval() {
  local name="$1" device="$2" task="$3" run_id="$4"
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d \
    --name "$name" \
    --user root \
    --cpus 12 \
    --memory 64g \
    --device "/dev/davinci${device}:/dev/davinci0" \
    --device /dev/davinci_manager \
    --device /dev/hisi_hdc \
    --device /dev/devmm_svm \
    --device /dev/dvpp_cmdlist \
    -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
    -v /usr/local/dcmi:/usr/local/dcmi:ro \
    -v /data/haidass-eval/models:/cache/models:ro \
    -v /data/haidass-eval/datasets:/cache/datasets:ro \
    -v "$RESULT_ROOT:/results" \
    "$IMAGE" python -c \
    "import json; from worker_eval import run_worker; print(json.dumps(run_worker('Haidass-143M-v1', '$task', 32, 0, '$run_id'), ensure_ascii=False, indent=2))"
  echo "$name device=$device run_id=$run_id"
}

start_eval candidate-piqa-full 4 piqa "${TIMESTAMP}_candidate_Haidass-143M-v1_piqa_full"
start_eval candidate-hellaswag-full 5 hellaswag "${TIMESTAMP}_candidate_Haidass-143M-v1_hellaswag_full"
