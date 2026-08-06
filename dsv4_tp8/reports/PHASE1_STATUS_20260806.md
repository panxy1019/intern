# DeepSeek-V4 TP8 第一阶段状态报告

## 当前状态

```text
namespace: ds
RayCluster: dsv4-tp8
Head: Ready
Head Ray: 2.49.0
Worker replicas/min/max: 0/0/1
vLLM Service: dsv4-vllm:8900
Service endpoint: 无（符合未启动Worker的预期）
vLLM: 未启动
```

## 已完成

1. 完成 KubeRay、Volcano、Ascend Device Plugin 和定卡机制审计。
2. 确认前四张物理卡对应逻辑 chip `0..7`。
3. 确认模型 74 个权重分片完整，模型目录约 293 GiB。
4. 构建并推送 Ray 2.49.0 amd64 Head 镜像。
5. 构建并推送 Ray 2.49.0 arm64 vLLM-Ascend Worker 镜像。
6. 创建 `ds` namespace、Head-only RayCluster 和端口 8900 Service。
7. Head 容器实际验证 Python 3.11.13、Ray 2.49.0。

## Worker 未扩容原因

`llamafactory` 独立 Docker 容器重新启动了以下训练进程：

```text
/usr/local/python3.11.15/bin/python3.11 -u
/app/src/llamafactory/launcher.py
examples/train_full/qwen3_full_sft_0p15_cache.yaml
```

该进程占用物理卡 0 的逻辑 chip 0。由于该 Docker 容器直接挂载
`/dev/davinci0..7`，在它活跃期间无法保证 Kubernetes Worker 对目标设备的
独占性。按 fail-closed 规则，Worker 保持 0，不修改或停止训练容器。

## 恢复门禁

训练结束后必须同时满足：

1. `check-target-npus.sh` 返回成功；
2. `npu-smi info` 中物理卡 0、1、2、3 均无进程；
3. `llamafactory` 中不再存在训练 launcher 或其子进程；
4. Kubernetes 中没有其他 Pod 申请 chip `0..7`。

通过后，在 `server-00` 执行：

```bash
cd /home/admin/testpanxy/infralearning/dsv4_tp8
export KUBECONFIG=/home/admin/k3s.yaml
DSV4_NPU_GATE_PASSED=yes ./scripts/scale-worker-up.sh
```

扩容后仍需验证容器设备节点、`torch.npu.device_count()==8`、设备映射文件和
Ray 的 `dsv4_worker=1`、`NPU=8`，这些未完成前不得启动 vLLM。
