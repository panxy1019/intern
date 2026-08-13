#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/etc/profile.d/conda.sh
conda activate verl_pt27_25rc3
set +u
source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
if [[ -f /usr/local/Ascend/cann/nnal/atb/set_env.sh ]]; then
  source /usr/local/Ascend/cann/nnal/atb/set_env.sh
fi
set -u
export LD_LIBRARY_PATH="/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH:-}"

python - <<'PY'
import json

import torch
import torch_npu

versions = {}
for name in ["torch", "torch_npu", "transformers", "accelerate", "datasets", "ray", "numpy"]:
    try:
        module = __import__(name)
        versions[name] = getattr(module, "__version__", "unknown")
    except Exception as exc:
        versions[name] = f"MISSING:{exc!r}"
print(json.dumps(versions, indent=2))

torch.npu.set_device(0)
left = torch.randn((2048, 2048), device="npu:0", dtype=torch.bfloat16)
right = torch.randn((2048, 2048), device="npu:0", dtype=torch.bfloat16)
result = left @ right
torch.npu.synchronize()
print("BASE_NPU_PASS", result.shape, result.device, result.dtype, float(result.float().mean().cpu()))
PY
