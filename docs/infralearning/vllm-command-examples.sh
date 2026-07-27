#!/usr/bin/env bash
# Command examples only. Source this file, then call tp4 or tp8 manually.
set -euo pipefail

common_env() {
  export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
  export HCCL_OP_EXPANSION_MODE=AIV
  export HCCL_BUFFSIZE=1024
  export OMP_NUM_THREADS=1
  export TASK_QUEUE_ENABLE=1
}

serve_qwen() {
  local tp=${1:?tensor parallel size required}
  common_env
  exec vllm serve /models/Qwen3.6-35B-A3B-w8a8 \
    --host 0.0.0.0 --port 8000 \
    --served-model-name qwen3.6-35b-a3b \
    --data-parallel-size 1 \
    --tensor-parallel-size "$tp" \
    --enable-expert-parallel \
    --quantization ascend --dtype bfloat16 \
    --max-model-len 8192 \
    --max-num-seqs 16 \
    --max-num-batched-tokens 4096 \
    --gpu-memory-utilization 0.85 \
    --trust-remote-code \
    --no-enable-prefix-caching
}

tp4() { serve_qwen 4; }
tp8() { serve_qwen 8; }

echo "Examples loaded. Run: tp4   or   tp8"
