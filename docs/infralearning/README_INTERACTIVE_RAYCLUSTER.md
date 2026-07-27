# 交互式 RayCluster vLLM 学习环境

## 架构

`vllm-interactive-lab` 是一个独立的 KubeRay 集群，位于 `infra-learning` 命名空间。Head 不申请 NPU；Worker 使用已验证同时包含 `Ray 2.48.0` 与 `vLLM-Ascend 0.21.0` 的镜像。Worker 由 KubeRay 执行 `ray start --block` 并保持常驻，因此不要把 `ray-worker` 改为 `sleep infinity`。

初始模式为 `4a`：一个 Worker 使用物理 `Phy-ID 8-11`。你进入该 Worker 手动启动 vLLM；Kubernetes Service 将流量转发到 Worker 的 `8000` 端口。

| 模式 | npu-4a | npu-4b | npu-8 | 实际 NPU |
|---|---:|---:|---:|---|
| `4a` | 1 | 0 | 0 | 一个 TP=4：8-11 |
| `dual-4` | 1 | 1 | 0 | 两个 TP=4：8-11、12-15 |
| `8` | 0 | 0 | 1 | 一个 TP=8：8-15 |

严禁手工同时启用 `npu-8` 与任意四卡 Group；它们有物理 NPU 重叠。使用 `set-vllm-lab-mode.sh` 切换，不要手工 patch 单个 Group。

## 启动集群

```bash
cd /home/admin/testpanxy/infralearning
sudo -i

# 此命令只删除之前的独立学习 Deployment，不影响 k12 的 Ray Head、Dagster、MinerU 和 MinIO。
k3s kubectl -n k12 delete -f qwen36-35b-a3b-tp4-learning.yaml

k3s kubectl apply -f vllm-interactive-lab-raycluster.yaml
k3s kubectl -n infra-learning get raycluster,pod,svc -o wide
```

等待 Head 与 `npu-4a` Worker 都变为 `Running`：

```bash
k3s kubectl -n infra-learning get pod -w
```

## 进入 Worker 并手动启动 TP=4 服务

```bash
export WORKER=$(k3s kubectl -n infra-learning get pod -l ray.io/group=npu-4a -o jsonpath='{.items[0].metadata.name}')
k3s kubectl -n infra-learning exec -it "$WORKER" -c ray-worker -- bash
```

Worker 内先验证设备和 Ray：

```bash
ray status
npu-smi info
python -c 'import torch, torch_npu; print(torch.npu.device_count())'
```

预期 `torch.npu.device_count()` 为 `4`。然后在前台启动 B0 基线服务：

```bash
export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
export HCCL_OP_EXPANSION_MODE=AIV
export HCCL_BUFFSIZE=1024
export OMP_NUM_THREADS=1
export TASK_QUEUE_ENABLE=1

vllm serve /models/Qwen3.6-35B-A3B-w8a8 \
  --host 0.0.0.0 --port 8000 \
  --served-model-name qwen3.6-35b-a3b \
  --data-parallel-size 1 \
  --tensor-parallel-size 4 \
  --enable-expert-parallel \
  --quantization ascend --dtype bfloat16 \
  --max-model-len 8192 \
  --max-num-seqs 16 \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.85 \
  --trust-remote-code \
  --no-enable-prefix-caching
```

前台运行便于学习日志；需要退出 shell 后服务继续运行时，请用 `tmux` 或 `nohup ... > /tmp/vllm.log 2>&1 &`。

## 从 server-00 测试服务与 Dashboard

```bash
# vLLM API
k3s kubectl -n infra-learning port-forward svc/vllm-interactive-lab-4a 8000:8000

# 另开终端
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/v1/models | jq .

# Ray Dashboard
k3s kubectl -n infra-learning port-forward svc/vllm-interactive-lab-head-svc 8265:8265
```

## 切换模式

Worker 在停止 vLLM 后才能切换。由 root 在 server-00 执行：

```bash
cd /home/admin/testpanxy/infralearning
./set-vllm-lab-mode.sh 4a
./set-vllm-lab-mode.sh dual-4
./set-vllm-lab-mode.sh 8
```

`dual-4` 时分别进入 `ray.io/group=npu-4a` 和 `ray.io/group=npu-4b` 的 Worker，各自启动 `TP=4`。`8` 时进入 `ray.io/group=npu-8` 的 Worker，将启动命令中的 `--tensor-parallel-size 4` 改为 `8`；同时容器应显示 8 个逻辑 NPU。

## 停止

```bash
sudo -i
k3s kubectl delete namespace infra-learning
```

该命令只删除本交互式实验集群及其三个 Service，不会删除 `k12` 命名空间中的生产服务。
