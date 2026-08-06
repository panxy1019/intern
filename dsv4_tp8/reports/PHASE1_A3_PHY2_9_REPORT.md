# DeepSeek-V4 TP8 第一阶段验收报告

## 部署状态

```text
namespace: ds
Ray Head: KubeRay RayCluster/dsv4-tp8
Ray Worker: Deployment/dsv4-tp8-worker-fixed-2-9
Head Python/Ray: 3.12.13 / 2.49.0
Worker Python/Ray: 3.12 / 2.49.0
vLLM: 未启动
```

## 设备分配

```text
物理板：1、2、3、4
宿主机 Phy-ID：2、3、4、5、6、7、8、9
容器设备节点：/dev/davinci2 ... /dev/davinci9
容器 CANN runtime ID：0、1、2、3、4、5、6、7
torch.npu.device_count()：8
```

Pod annotation 为：

```text
huawei.com/Ascend910: Ascend910-2,Ascend910-3,Ascend910-4,
Ascend910-5,Ascend910-6,Ascend910-7,Ascend910-8,Ascend910-9
```

## 调度实现

KubeRay Operator 以 `--batch-scheduler=volcano` 运行，会覆盖 Worker template
中的 `schedulerName`。Volcano 将 Phy-ID `2..9` 判定为无效 TP8 拓扑，因此
KubeRay Worker 无法调度。

最终保留 KubeRay 管理的 Head，使用 `default-scheduler` Deployment 创建
固定设备 Worker，并执行 `ray start --address=<head>:6379` 加入同一 Ray 集群。
这没有修改 Operator、Volcano、Device Plugin 或其他业务。

## Ray 验收

Head 实际看到：

```text
CPU: 192
NPU: 8
dsv4_worker: 1
Worker node IP: 10.42.17.174
```

Worker 无重启，Ray status 无 Pending 或 Recent failures。

## 停止 Worker

```bash
export KUBECONFIG=/home/admin/k3s.yaml
kubectl -n ds scale deployment dsv4-tp8-worker-fixed-2-9 --replicas=0
```

该命令只释放 Worker 和 Phy-ID `2..9`，不会删除 Head。第二阶段启动 vLLM 前
仍需再次检查这 8 个设备、模型分片和 Worker 健康状态。
