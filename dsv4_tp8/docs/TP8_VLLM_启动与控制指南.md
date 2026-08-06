# DeepSeek-V4 Flash TP8 启动与控制指南

## 当前部署

- Namespace：`ds`
- Worker：`deployment/dsv4-tp8-worker-fixed-2-9`
- 物理逻辑 NPU：`Phy-ID 2,3,4,5,6,7,8,9`
- 容器运行时 NPU：`0..7`
- 服务：`dsv4-vllm.ds.svc.cluster.local:8900`
- 模型：`/models/DeepSeek-V4-Flash-0731-w8a8`，只读挂载
- 可写状态、日志与 PID：`/cache/vllm`

`runtime ID 0..7` 是容器内重新编号，不能据此推断宿主机物理卡号；固定卡关系以
`/cache/vllm/state/device-mapping.json` 为准。

## 启动、状态和停止

在 `server-00` 执行：

```bash
cd /home/admin/testpanxy/infralearning/dsv4_tp8
export KUBECONFIG=/home/admin/k3s.yaml

./scripts/start-vllm-tp8.sh
./scripts/status-vllm-tp8.sh
./scripts/stop-vllm-tp8.sh
```

`start-vllm-tp8.sh` 会检查 PID 文件和 `/proc/<pid>/cmdline`，已有同一 vLLM 实例时
不会重复拉起。`stop-vllm-tp8.sh` 向该实例的进程组发送 `SIGTERM`，最多等待 120 秒，
之后才发送 `SIGKILL`；它不会停止 Pod、Ray Head 或其他业务。

## 修改 vLLM 参数

编辑 `k8s/26-vllm-control-config.yaml` 中 `data.vllm-tp8.args`。每个参数或参数值独占
一行，JSON 值也作为单独一行，例如：

```yaml
--max-num-seqs
2
--gpu-memory-utilization
0.90
```

应用修改并重启：

```bash
./scripts/stop-vllm-tp8.sh
./scripts/apply-vllm-config.sh

# 等待 ConfigMap 卷投射，再核对容器实际读取的参数。
kubectl -n ds exec deploy/dsv4-tp8-worker-fixed-2-9 -- \
  cat /opt/dsv4-vllm/config/vllm-tp8.args

./scripts/start-vllm-tp8.sh
./scripts/status-vllm-tp8.sh
```

首次基线刻意保持 `--enforce-eager`、关闭 prefix cache，并未启用 DSpark、MTP、ACL
Graph、Mooncake、KV offload、DCP 或 PCP。改变任一性能相关参数时，应单变量修改并
记录运行 ID 与测量结果。

## API 验证

服务只暴露 ClusterIP。可从 Worker 内验证：

```bash
export KUBECONFIG=/home/admin/k3s.yaml
WPOD=$(kubectl -n ds get pod -l dsv4.openai.com/device-set=phy-2-9 \
  -o jsonpath='{.items[0].metadata.name}')

kubectl -n ds exec "$WPOD" -- curl -fsS http://127.0.0.1:8900/health
kubectl -n ds exec "$WPOD" -- curl -fsS http://127.0.0.1:8900/v1/models
```

模型当前 tokenizer 没有内置 chat template，因此用于连通性验证时优先用
`/v1/completions`，而不要把未模板化的原始 prompt 当成聊天能力评测。客户端接入时，
应由客户端显式使用模型官方 chat template 后再请求 `/v1/completions`，或确认模板后
使用 `/v1/chat/completions`。

## 交互式多轮对话

`dsv4_chat.py` 不依赖第三方 Python 包，保存会话到 `~/.dsv4_chat/`，支持 `/new`、
`/switch`、`/list`、`/history`、`/clear` 和 `/exit`。在 `server-00` 上最直接的启动方式：

```bash
cd /home/admin/testpanxy/infralearning/dsv4_tp8
export KUBECONFIG=/home/admin/k3s.yaml
./dsv4_chat.py --port-forward
```

`--port-forward` 会在客户端生命周期内创建 `ds/dsv4-vllm` 到本地 `8900` 的转发，退出
时仅终止这个由脚本创建的子进程。它不修改 Deployment，也不使用进程扫描。

常用变体：

```bash
# 新建并命名会话，固定采样便于复现。
./dsv4_chat.py --port-forward --new --session experiment-a \
  --temperature 0 --max-tokens 1024

# 恢复同一会话。
./dsv4_chat.py --port-forward --session experiment-a

# 已经有外部端口转发或在 Worker 内运行时，不创建新的转发。
./dsv4_chat.py --base-url http://127.0.0.1:8900/v1
```

默认使用流式输出；传入 `--no-stream` 可改为等待整段回答后再显示。

## 低风险观察

```bash
./scripts/status-vllm-tp8.sh
kubectl -n ds logs deploy/dsv4-tp8-worker-fixed-2-9 --tail=120
```

宿主机卡状态只在需要时手动执行：

```bash
ssh admin@110.123.0.3
sudo npu-smi info
```

不要在循环里使用 `ps`。此前宿主机出现过大量处于 D 状态的 `ps`，此环境的脚本不依赖
扫描式进程监控。
