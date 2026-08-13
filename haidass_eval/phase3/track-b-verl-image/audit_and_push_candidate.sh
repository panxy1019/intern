#!/usr/bin/env bash
set -euo pipefail

IMAGE="110.120.0.3:8889/eval/lighteval-ascend-worker:verl-pt27-25rc3-lighteval0.9.2-20260813"
OUTPUT_DIR="/data/haidass-eval/phase3-images/verl-base"
mkdir -p "$OUTPUT_DIR"
docker rm -f verl-lighteval-test >/dev/null 2>&1 || true

docker image inspect "$IMAGE" > "$OUTPUT_DIR/image-inspect.json"
docker history --no-trunc "$IMAGE" > "$OUTPUT_DIR/docker-history.txt"
docker run --rm -i \
  --device /dev/davinci1:/dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/hisi_hdc \
  --device /dev/devmm_svm \
  --device /dev/dvpp_cmdlist \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  "$IMAGE" python - <<'PY' > "$OUTPUT_DIR/image-smoke.txt"
import inspect

import lighteval
import torch
import torch_npu
from accelerate import Accelerator

accelerator = Accelerator()
assert accelerator.device.type == "npu", accelerator.device
assert "/opt/venvs/lighteval092" not in inspect.getfile(torch)
torch.npu.set_device(0)
value = torch.ones((1024, 1024), dtype=torch.bfloat16, device="npu:0")
result = value @ value
torch.npu.synchronize()
print("CANDIDATE_IMAGE_NPU_PASS", result.device, lighteval.__version__, torch.__version__, torch_npu.__version__)
PY

docker run --rm --entrypoint bash "$IMAGE" -lc '
  source /root/miniconda3/etc/profile.d/conda.sh
  conda activate verl_pt27_25rc3
  source /opt/venvs/lighteval092/bin/activate
  python -m pip freeze
' > "$OUTPUT_DIR/pip-freeze.txt"
docker push "$IMAGE"
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}' > "$OUTPUT_DIR/image-digest.txt"
printf '%s\n' "$IMAGE" > "$OUTPUT_DIR/image-tag.txt"
cat "$OUTPUT_DIR/image-smoke.txt"
cat "$OUTPUT_DIR/image-digest.txt"
