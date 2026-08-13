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

rm -rf /opt/venvs/lighteval092
python -m venv --system-site-packages /opt/venvs/lighteval092
source /opt/venvs/lighteval092/bin/activate
python -m pip install --no-index --no-deps /opt/wheelhouse/*.whl

python - <<'PY'
import inspect

import torch
import torch_npu
from accelerate import Accelerator

assert "/opt/venvs/lighteval092" not in inspect.getfile(torch)
assert "/opt/venvs/lighteval092" not in inspect.getfile(torch_npu)
print("VENV_NPU_PASS", inspect.getfile(torch), inspect.getfile(torch_npu))
accelerator = Accelerator()
assert accelerator.device.type == "npu", accelerator.device
print("ACCELERATE_NPU_PASS", accelerator.device)
import lighteval
print("LIGHTEVAL_IMPORT_PASS", lighteval.__version__)
PY

python - <<'PY'
import torch
import torch_npu
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "/cache/models/Haidass-143M-v1"
torch.npu.set_device(0)
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    local_files_only=True,
    torch_dtype=torch.bfloat16,
).to("npu:0")
inputs = tokenizer("The capital of France is", return_tensors="pt")
inputs = {key: value.to("npu:0") for key, value in inputs.items()}
with torch.inference_mode():
    outputs = model(**inputs)
torch.npu.synchronize()
assert outputs.logits.device.type == "npu", outputs.logits.device
print("HAIDASS_FORWARD_PASS", outputs.logits.shape, outputs.logits.device)
PY

rm -rf /tmp/lighteval-model /tmp/hellaswag-smoke
mkdir -p /tmp/lighteval-model /tmp/hellaswag-smoke
find /cache/models/Haidass-143M-v1 -mindepth 1 -maxdepth 1 \
  ! -name 'results_*' ! -name '20*' -exec ln -s '{}' /tmp/lighteval-model/ \;
export LIGHTEVAL_DATA_ROOT=/cache/datasets
export HF_HOME=/tmp/huggingface
export HF_DATASETS_CACHE=/tmp/huggingface/datasets
export TOKENIZERS_PARALLELISM=false
export TORCH_DEVICE_BACKEND_AUTOLOAD=0
python -m lighteval accelerate \
  "model_name=/tmp/lighteval-model,dtype=bfloat16,batch_size=4,model_parallel=false,compile=false" \
  "leaderboard|hellaswag|0|0" \
  --custom-tasks /opt/phase3-code/offline_dataset_router.py \
  --dataset-loading-processes 1 \
  --max-samples 16 \
  --output-dir /tmp/hellaswag-smoke \
  --save-details

find /tmp/hellaswag-smoke /tmp/lighteval-model -name 'results_*.json' -print -quit | grep -q .
echo HELLASWAG_16_PASS
