#!/usr/bin/env bash
set -euo pipefail

IMAGE="110.120.0.3:8889/eval/lighteval-ascend-worker:demo-ray2.10-py310-torch2.7.1-cann8.3-lighteval0.9.2"
OUTPUT_DIR="/data/haidass-eval/phase3-images/demo-base"
mkdir -p "$OUTPUT_DIR"

docker image inspect "$IMAGE" > "$OUTPUT_DIR/image-inspect.json"
docker history --no-trunc "$IMAGE" > "$OUTPUT_DIR/docker-history.txt"
docker run --rm \
  --entrypoint bash \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  "$IMAGE" -lc '
    source /root/miniconda3/etc/profile.d/conda.sh
    conda activate ms
    set +u
    source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
    set -u
    export LD_LIBRARY_PATH="/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH:-}"
    python - <<"PY"
import lighteval
import ray
import torch
import torch_npu

print("IMPORT_PASS", ray.__version__, lighteval.__version__, torch.__version__, torch_npu.__version__)
PY
    python -m pip freeze
  ' > "$OUTPUT_DIR/pip-freeze.txt"

docker push "$IMAGE"
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}' > "$OUTPUT_DIR/image-digest.txt"
printf '%s\n' "$IMAGE" > "$OUTPUT_DIR/image-tag.txt"
cat "$OUTPUT_DIR/image-digest.txt"
