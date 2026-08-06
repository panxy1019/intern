# DeepSeek-V4 TP8 第一阶段

该目录用于在 `ds` namespace 中部署隔离的 Ray 集群并启动 DeepSeek-V4-Flash-0731
TP8 服务。KubeRay 管理 CPU-only Head；由于集群级 KubeRay Operator 强制 Volcano，
而 Volcano 拒绝跨拓扑边界的 Phy-ID `2..9`，NPU Worker 使用已验证的
`default-scheduler` Deployment 加入同一 Ray Head。

执行门禁：

1. `a3-server-00` 的逻辑 NPU `0..7` 不得存在进程。
2. Worker 必须只注入 `/dev/davinci2` 至 `/dev/davinci9`。
3. Head 和 Worker 的 Ray 版本必须均为 `2.49.0`。
4. Ray 必须注册 `dsv4_worker=1` 和 `NPU=8`。

当前 Worker：

```text
deployment/dsv4-tp8-worker-fixed-2-9
physical Phy-ID: 2,3,4,5,6,7,8,9
container runtime ID: 0,1,2,3,4,5,6,7
```

第二阶段操作入口：

```bash
cd /home/admin/testpanxy/infralearning/dsv4_tp8
export KUBECONFIG=/home/admin/k3s.yaml
./scripts/status-vllm-tp8.sh
./scripts/stop-vllm-tp8.sh
./scripts/start-vllm-tp8.sh
```

参数修改、重启和验证细节见 `docs/TP8_VLLM_启动与控制指南.md`。镜像 digest、
设备映射及每阶段验证结果见 `reports/`。

交互式多轮对话：

```bash
./dsv4_chat.py --port-forward
```
