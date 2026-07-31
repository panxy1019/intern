# 当前状态

更新时间：2026-07-31 01:23 UTC。

## 已完成

- `Qwen3.6-27B-w8a8` 权重下载与 9 个分片完整性检查。
- 基于 `v0.22.1rc1-a3` 构建 PD Worker 镜像。
- Ray `2.48.0`、Mooncake、`mooncake_master` 和官方 PD Proxy 构建门禁。
- 镜像推送到 HTTP 私库并校验 manifest digest。
- 在 `infra-learning` 注册 ConfigMap、Service 和 `replicas=0` Deployment。
- 将构建日志复制到 `markdowns/raw/`。
- 清理 rootless Podman 临时镜像，存储从约 18GB 降至 168KB。

## 镜像

```text
110.120.0.3:8889/infra/qwen36-pd-worker:v0.22.1rc1-a3-ray248-20260730
sha256:15c3a3db3772807cc09d9ad37756cd973e3b078956b6a239375ec4ae23317133
```

## 当前阻断

2026-07-31 00:58 UTC 启动前门禁曾确认物理 `Phy-ID 2-7` 无进程，
但启动期间宿主机 Docker 容器 `/llamafactory` 开始了新的 8 卡训练：

```text
image: hiyouga/llamafactory:latest-npu-a3
job: examples/train_full/qwen3_full_sft_0p15_train.yaml
container: f46ab260f3505e632183729ae369bc0884502f7ccc1481ba9b50a160148de3a6
processes: 4021280-4021287
```

该训练覆盖物理 `Phy-ID 0-7`，每卡占用约 `34.7-34.8 GiB` HBM。
物理 `Phy-ID 8-15` 同时由既有 vLLM 进程占用约 `55 GiB` HBM。
当前 16 个逻辑 NPU 均没有可安全分配的空位。

检测到冲突后，PD Deployment 已立即缩容为 `replicas=0`。我方
`VLLMWorker_TP` 进程已经退出，没有终止或修改 `/llamafactory` 训练任务，
也没有改动物理 `Phy-ID 8-15` 上的既有 vLLM 服务。

## 卡空闲后的启动命令

在 A3 上确认：

```bash
cd /home/admin/qwen36_pd_1p2d
sudo python3 scripts/check_target_npus_idle.py
```

只有输出 `PASS` 后，在 server-00 执行：

```bash
cd /home/admin/testpanxy/infralearning/qwen36_pd_1p2d
NPU_IDLE_CONFIRMED=YES ./start.sh
```

监控：

```bash
sudo /usr/local/bin/k3s kubectl -n infra-learning get pod -w
sudo /usr/local/bin/k3s kubectl -n infra-learning logs \
  deploy/ray-vllm-pd-worker-qwen36-27b -f
```

停止：

```bash
cd /home/admin/testpanxy/infralearning/qwen36_pd_1p2d
./rollback.sh
```
