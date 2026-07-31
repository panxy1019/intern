# 实施记录

## 2026-07-30 只读审计

- A3 节点：`a3-server-00`，驱动 `26.0.rc1`，16 个 `Ascend910` 逻辑资源。
- `NPU 1/2/3` 对应物理 `Phy-ID 2-7`，审计时均无运行进程。
- 目标模型已下载到 `/home/admin/models/Qwen3.6-27B-w8a8`。
- 权重共 9 个 safetensors 分片，索引引用完整，目录约 34GiB。
- 现有 Ray Head 位于 `infra-learning`，Ray 版本为 `2.48.0`。
- 用户确认 Worker 资源固定为 `64 CPU / 256Gi memory`。

## 镜像与网络决策

- 基础镜像：`quay.io/ascend/vllm-ascend:v0.22.1rc1-a3`。
- Quay 直连 manifest 检查成功，约耗时 28 秒。
- `m.daocloud.io` 镜像地址返回 `denied: Read Only`，不采用。
- 初始构建使用 Quay 直连；只有拉层持续停滞时才启用
  `http://110.120.0.3:18080` 代理。
- Python 包使用华为云 PyPI 镜像。

## 设计决定

- 使用一个 Kubernetes Deployment 和一个 Pod，申请 6 个 Ascend 逻辑资源。
- Pod 内运行一个 Prefill TP2、两个 Decode TP2 和一个官方 PD Proxy。
- 使用非 Layerwise `MooncakeConnectorV1`，先验证正确性，再做性能调优。
- 三个模型顺序启动：Prefill、Decode A、Decode B。
- 禁用 prefix cache 和 speculative decoding，避免首轮同时引入额外变量。
- Mooncake `kv_port` 使用 36000、36100、36200，避开 A3 的随机传输端口范围。

## 2026-07-30 构建与推送结果

- Quay 直连拉取时，层 `1e43eb0ddf11` 和 `086b0120f2ec` 连续发生网络重试。
- 为避免修改或重启 Docker daemon，终止直连构建，改用 rootless Podman：

  ```bash
  export HTTP_PROXY=http://110.120.0.3:18080
  export HTTPS_PROXY=http://110.120.0.3:18080
  podman pull quay.io/ascend/vllm-ascend:v0.22.1rc1-a3
  podman save quay.io/ascend/vllm-ascend:v0.22.1rc1-a3 | sudo docker load
  ```

- 基础镜像 manifest：`sha256:c4d766b5f04fe6238a74731d67a215bb6331072ba242c7c5f24a25f99ce36c3b`。
- 派生镜像本地 ID：`sha256:6d454e6d5715ac8792868408e57f9287aa0444867db23747b797ddaae5ff924a`。
- 派生镜像大小：`18270627939` bytes，约 18.27GB。
- 构建门禁通过：
  - vLLM-Ascend 基础版本为 `0.22.1rc1-a3`；
  - Ray 为 `2.48.0`；
  - Python 可以导入 `mooncake`；
  - `/usr/local/bin/mooncake_master` 存在；
  - 官方非 Layerwise PD Proxy 文件存在。
- 私库只提供 HTTP，Docker 首次推送报
  `server gave HTTP response to HTTPS client`。没有修改全局
  `insecure-registries`，而是使用：

  ```bash
  sudo docker save "$IMAGE" | podman load
  podman push --tls-verify=false "$IMAGE"
  ```

- 私库镜像：
  `110.120.0.3:8889/infra/qwen36-pd-worker:v0.22.1rc1-a3-ray248-20260730`
- 私库 digest：
  `sha256:15c3a3db3772807cc09d9ad37756cd973e3b078956b6a239375ec4ae23317133`

## 部署前资源门禁

镜像推送完成后再次检查 A3，发现目标资源状态已发生变化：

```text
NPU 1: 两个 python3.11 训练进程，HBM 约 59GiB / 53GiB
NPU 2: 两个 python3.11 训练进程，HBM 约 43GiB / 40GiB
NPU 3: 两个 python3.11 训练进程，HBM 约 43GiB / 39GiB
```

进程命令：

```text
/usr/local/python3.11.15/bin/python3.11
  -u /app/src/llamafactory/launcher.py
  examples/train_full/qwen3_full_sft_0p15_train.yaml
```

归属 Docker 容器：

```text
name=/llamafactory
image=hiyouga/llamafactory:latest-npu-a3
container=f46ab260f3505e632183729ae369bc0884502f7ccc1481ba9b50a160148de3a6
```

该容器由宿主机 Docker 直接启动，不在 Kubernetes 设备插件的资源账本中。
因此 Kubernetes 即使允许 Pod 调度，也可能把相同物理设备再次分配给 PD Worker。
为避免干扰训练任务，Deployment 使用 `replicas=0` 安全注册，不启动模型。

启动前必须在 A3 执行：

```bash
cd /home/admin/qwen36_pd_1p2d
sudo python3 scripts/check_target_npus_idle.py
```

只有输出 `PASS` 后，才在 server-00 执行：

```bash
cd /home/admin/testpanxy/infralearning/qwen36_pd_1p2d
NPU_IDLE_CONFIRMED=YES ./start.sh
```

安全注册结果：

```text
deployment.apps/ray-vllm-pd-worker-qwen36-27b  replicas=0
service/qwen36-pd                              ClusterIP=10.43.212.138
configmap/qwen36-pd-worker-scripts             created
```

资源已经注册到 `infra-learning`，但没有创建 Pod、没有申请 NPU，也没有启动
vLLM。首次 `deploy.sh` 的最后一个组合 `kubectl get` 写法会将两个名称同时应用
到两种资源类型，导致非破坏性的 `NotFound` 返回；Deployment、Service 和
ConfigMap 均已成功创建，脚本已拆成两条精确查询命令。

## 临时存储清理

构建和推送结束后，原始及派生镜像仍保留在 Docker，并且派生镜像已经进入
私库。rootless Podman 仅用于代理拉取和 HTTP 私库推送，因此执行：

```bash
podman rmi \
  110.120.0.3:8889/infra/qwen36-pd-worker:v0.22.1rc1-a3-ray248-20260730 \
  quay.io/ascend/vllm-ascend:v0.22.1rc1-a3
podman image prune -f
```

清理后 Podman 存储为 `168K`。原始构建日志已经复制到
`markdowns/raw/`。

## 2026-07-31 启动尝试与自动回退

00:58 UTC 启动前，A3 主机门禁返回：

```text
PASS: NPU 1/2/3 均无运行进程，可以启动 PD Worker。
```

随后在 server-00 执行 `NPU_IDLE_CONFIRMED=YES ./start.sh`。私库镜像在
约 35 秒内拉取完成，容器内设备映射验证为：

```text
prefill=2,3
decode_a=4,5
decode_b=6,7
```

Ray Worker 成功注册：

```text
CPU=64
NPU=6
PD_PREFILL=1
PD_DECODE=2
QWEN36_PD_WORKER=1
```

Prefill TP2 完成 9 个权重分片加载，每个 rank 权重约 `16.87 GB`，随后进入
Ascend 首次图/算子编译。为避免首次编译被过短的健康等待窗口终止，
`VLLM_STARTUP_TIMEOUT` 默认值由 1200 秒调整为 3600 秒，并更新了 ConfigMap。

01:21 UTC 再次检查时，发现宿主机 `/llamafactory` 容器已经启动新的 8 卡
Qwen3 全参 SFT：

```text
command=/app/src/llamafactory/launcher.py \
  examples/train_full/qwen3_full_sft_0p15_train.yaml
PIDs=4021280-4021287
physical_npus=0-7
per_npu_hbm=约 34.7-34.8 GiB
```

该任务由宿主机 Docker 直接管理，不受 Kubernetes 设备插件排他调度约束，
因此它在 PD Pod 启动后占用了相同的物理卡 2、3。物理卡 8-15 另有既有
vLLM 进程，当前没有可迁移的空闲卡。

发现资源冲突后立即执行：

```bash
sudo /usr/local/bin/k3s kubectl -n infra-learning scale \
  deployment/ray-vllm-pd-worker-qwen36-27b --replicas=0
```

缩容后我方 Prefill 进程全部退出；`npu-smi` 只保留原训练任务和既有 vLLM
进程。没有停止、重启或修改任何非本项目工作负载。本次未启动 Decode 和
PD Proxy，也未执行推理 smoke。
