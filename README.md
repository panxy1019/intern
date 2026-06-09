# K8s/K3s 集群启动昇腾 NPU Ray Worker 记录

本文记录如何在 K8s/K3s 集群中为 `RayCluster` 启动昇腾 NPU worker 节点。内容覆盖 worker 镜像准备、镜像分发、KubeRay 配置、任务提交验证，以及常见问题排查。
<img width="1024" height="1536" alt="ChatGPT Image 2026年6月8日 19_24_34" src="https://github.com/user-attachments/assets/75990451-1405-4d0e-92ec-8d0476376a78" />
这套流程要解决两个层面的调度问题：

1. Kubernetes 要知道哪些节点有 Ascend 910B3 NPU，并把 worker Pod 调度到这些节点。
2. Ray 要知道 worker 进程拥有多少 NPU 资源，并把需要 NPU 的任务调度到对应 worker。

如果只完成其中一个层面，集群通常会出现两类问题：Pod 能启动但 Ray 不会分配 NPU 任务，或者 Ray 配置了 NPU 资源但 Kubernetes 没有真正把容器放到 NPU 节点上。

Ray 的基础概念可以参考 [Ray 基础知识整理](ray.md)。

## 0. 环境假设

开始前默认已经具备以下条件：

- K8s/K3s 集群可用，并已经安装 KubeRay Operator。
- NPU 节点已经安装 Ascend 驱动、CANN/ATB 运行环境和 NPU device plugin。
- NPU 节点带有可用于调度的标签，例如 `node.kubernetes.io/npu.chip.name=910B3`。
- 私有镜像仓库 `110.120.0.3:8889` 能被所有 K3s server/agent 节点访问。

可以先检查节点标签和 NPU 扩展资源：

```bash
kubectl get nodes -L node.kubernetes.io/npu.chip.name
kubectl describe node <npu-node-name> | grep -A5 -E "Capacity|huawei.com/Ascend910"
```

## 1. 整体思路

RayCluster 通常由 head 节点和 worker 节点组成：

- head 节点负责 Ray GCS、Dashboard、Job Submission、集群元数据和调度入口。
- worker 节点负责实际执行任务。
- Kubernetes 负责创建 Pod、挂载宿主机资源、注入设备，并保证 Pod 运行在正确节点上。
- Ray 负责在已启动的 worker 之间调度 Python task/actor。

因此，NPU worker 的关键不是单独写一份 YAML，而是让“镜像、Pod、节点、Ray 资源声明”四件事保持一致：

- 镜像中要有任务运行所需的 Python 包，例如 `daft`。
- Pod 要申请 `huawei.com/Ascend910`，让 Kubernetes 分配真实 NPU 设备。
- Pod 要挂载 Ascend driver/DCMI 路径，并在启动时加载 CANN/ATB 环境变量。
- Ray worker 启动参数要声明 `resources: '{"NPU": 8}'`，让 Ray 调度器看到自定义 NPU 资源。

## 2. 准备 Worker 镜像

worker 镜像基于已有的 `ms_verl_ful:v1`，并把 Python 依赖安装到 `ms` conda 环境中。这样做的原因是：Ray 的 `runtime_env` 适合分发项目代码和轻量依赖，但系统库、NPU 运行时、重量级 Python 环境更适合固定在镜像里，避免 worker 启动后再临时安装导致版本不一致或启动过慢。

### Dockerfile

```dockerfile
FROM ms_verl_ful:v1

ENV MS_VENV=/root/miniconda3/envs/ms
ENV PATH="${MS_VENV}/bin:${PATH}"

# 安装到 Ray worker 实际使用的 ms conda 环境中。
RUN ${MS_VENV}/bin/python -m pip install daft -i https://mirrors.aliyun.com/pypi/simple/

CMD ["/bin/bash"]
```

### 构建与推送镜像

```bash
docker build -t demo:v2 .
docker tag demo:v2 110.120.0.3:8889/demo:v2
docker push 110.120.0.3:8889/demo:v2
```

K3s 默认使用 containerd 运行 Pod，本机 Docker 里存在的镜像不会自动出现在每个节点的 containerd 中。因此需要把镜像推送到私有仓库，再让各个节点拉取同一个镜像。这样可以避免 worker Pod 在不同节点上出现 `ImagePullBackOff` 或镜像版本不一致。

如果私有仓库是 HTTP 服务，`k3s ctr images pull` 需要加 `--plain-http`；如果仓库已经配置 HTTPS，可以去掉这个参数。

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE="110.120.0.3:8889/demo:v2"
NODES=("110.129.0.12" "110.129.0.14" "110.129.0.5")
SSH_OPTS="-o StrictHostKeyChecking=no"

echo "Start pulling ${IMAGE} on all target nodes."

for NODE in "${NODES[@]}"; do
  echo "Trigger ${NODE}..."
  ssh ${SSH_OPTS} root@"${NODE}" "k3s ctr images pull --plain-http ${IMAGE}" &
done

wait
echo "All image pull tasks finished."
```

保存为 `shareimages.sh` 后执行：

```bash
chmod +x shareimages.sh
./shareimages.sh
```

建议优先使用 SSH key 登录节点，不要把明文密码写进脚本或提交到仓库。

## 3. 配置 RayCluster

下面是整理后的核心配置。这里保留了最关键的字段，方便后续根据集群实际情况继续拆分成独立 YAML 文件。

配置重点如下：

- `metadata.namespace` 使用 `ray-demo`，后续 `kubectl` 命令需要保持一致。
- head 节点通过 `nodeSelector` 固定调度到 `server-00`，方便访问 Dashboard 和 Job Submission 服务。
- worker 节点通过 `nodeSelector` 调度到 910B3 NPU 节点。
- worker Pod 通过 `requests/limits` 申请 `huawei.com/Ascend910: "8"`，这是 Kubernetes 层面的设备分配。
- worker 通过 `rayStartParams.resources` 注册 `NPU: 8`，这是 Ray 层面的任务调度资源。
- worker 挂载宿主机 Ascend driver 和 DCMI 路径，让容器内程序能够访问 NPU 驱动和管理接口。
- worker 启动命令中显式加载 conda、CANN 和 ATB 环境，保证 Python 包与 NPU 运行库都在同一个进程环境中生效。

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: raycluster-npu-demo
  namespace: ray-demo
  labels:
    app.kubernetes.io/instance: raycluster-npu
spec:
  rayVersion: "2.10.0"
  enableInTreeAutoscaling: true
  autoscalerOptions:
    idleTimeoutSeconds: 60

  headGroupSpec:
    serviceType: ClusterIP
    rayStartParams:
      dashboard-host: "0.0.0.0"
      num-cpus: "0"
    template:
      spec:
        nodeSelector:
          kubernetes.io/hostname: server-00
        tolerations:
          - key: node-role.kubernetes.io/control-plane
            operator: Exists
            effect: NoSchedule
        containers:
          - name: ray-head
            image: crpi-gcyqahoi1kzpijkb.cn-hangzhou.personal.cr.aliyuncs.com/panxy1019/panxy:ray-2.10.0-py3100-amd64
            imagePullPolicy: IfNotPresent
            resources:
              requests:
                cpu: "2"
                memory: 8Gi
              limits:
                cpu: "2"
                memory: 8Gi
            volumeMounts:
              - name: log-volume
                mountPath: /tmp/ray
        volumes:
          - name: log-volume
            emptyDir: {}

  workerGroupSpecs:
    - groupName: npu-workers
      replicas: 1
      minReplicas: 1
      maxReplicas: 4
      numOfHosts: 1
      rayStartParams:
        resources: '"{\"NPU\": 8}"'
      scaleStrategy:
        workersToDelete: []
      template:
        metadata:
          annotations:
            ray.io/overwrite-container-cmd: "true"
            volcano.sh/network-topology-highest-tier: "1"
            volcano.sh/network-topology-mode: hard
        spec:
          nodeSelector:
            node.kubernetes.io/npu.chip.name: 910B3
          containers:
            - name: ray-worker
              image: 110.120.0.3:8889/demo:v2
              imagePullPolicy: IfNotPresent
              command:
                - /bin/bash
                - -lc
                - --
              args:
                - |
                  set -e
                  source /root/miniconda3/etc/profile.d/conda.sh
                  conda activate ms
                  source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
                  source /usr/local/Ascend/cann/nnal/atb/set_env.sh
                  ulimit -n 65536
                  eval "$KUBERAY_GEN_RAY_START_CMD"
              resources:
                requests:
                  cpu: "8"
                  memory: 32Gi
                  huawei.com/Ascend910: "8"
                limits:
                  cpu: "8"
                  memory: 32Gi
                  huawei.com/Ascend910: "8"
              volumeMounts:
                - name: log-volume
                  mountPath: /tmp/ray
                - name: ascend-driver
                  mountPath: /usr/local/Ascend/driver
                  readOnly: true
                - name: ascend-dcmi
                  mountPath: /usr/local/dcmi
                  readOnly: true
          volumes:
            - name: log-volume
              emptyDir: {}
            - name: ascend-driver
              hostPath:
                path: /usr/local/Ascend/driver
            - name: ascend-dcmi
              hostPath:
                path: /usr/local/dcmi
```

应用配置：

```bash
kubectl create namespace ray-demo
kubectl apply -f raycluster-npu-demo.yaml
```

查看启动状态：

```bash
kubectl get raycluster -n ray-demo
kubectl get pods -n ray-demo -o wide
kubectl logs -n ray-demo -l ray.io/node-type=head --tail=100
kubectl logs -n ray-demo -l ray.io/group=npu-workers --tail=100
```

## 4. 提交测试任务

Dashboard 默认在 head Pod 的 8265 端口上。可以通过 SSH 端口转发在本地访问，例如 head Pod IP 为 `10.42.0.23`：

```bash
ssh -L 8265:10.42.0.23:8265 admin@110.120.0.3
```

然后在浏览器打开：

```text
http://127.0.0.1:8265
```

提交任务前，可以准备一个简单的 `test_daft_env.py`，用来确认 Ray 能把任务调度到带 NPU 资源的 worker 上，并且容器内可以导入 `daft`。

```python
import subprocess

import ray


@ray.remote(resources={"NPU": 1})
def check_worker_env():
    import daft

    result = subprocess.run(
        ["bash", "-lc", "npu-smi info | head -40"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "daft_version": getattr(daft, "__version__", "unknown"),
        "npu_smi": result.stdout or result.stderr,
    }


ray.init()
print(ray.get(check_worker_env.remote()))
```

再通过 Ray Job Submission API 提交：

```python
from ray.job_submission import JobSubmissionClient


client = JobSubmissionClient("http://127.0.0.1:8265")

job_id = client.submit_job(
    entrypoint="python test_daft_env.py",
    runtime_env={"working_dir": "./"},
)

print(f"Job ID: {job_id}")
print("Streaming logs:")

try:
    for line in client.tail_job_logs(job_id):
        print(line, end="")
except KeyboardInterrupt:
    print()
    print("Local log streaming stopped. The Ray job may still be running in the cluster.")
    print(f"Stop it with: ray job stop {job_id} --address http://127.0.0.1:8265")

status = client.get_job_status(job_id)
print(f"Final status: {status}")
```

如果测试成功，通常能同时看到三类信息：

- Ray job 状态为 `SUCCEEDED`。
- 任务日志中能打印 `daft_version`。
- `npu-smi info` 能在 worker 容器内返回 NPU 信息。

## 5. 常见问题排查

### Pod 一直 Pending

优先检查 Kubernetes 是否能看到 NPU 扩展资源，以及 worker 的 `nodeSelector` 是否能匹配到节点：

```bash
kubectl describe pod -n ray-demo <worker-pod-name>
kubectl get nodes -L node.kubernetes.io/npu.chip.name
kubectl describe node <npu-node-name> | grep huawei.com/Ascend910 -A3
```

如果 `huawei.com/Ascend910` 不存在，通常是 NPU device plugin 未安装、未正常运行，或者节点驱动没有被正确识别。

### Worker 已启动，但 Ray Dashboard 看不到 NPU

检查 `workerGroupSpecs[].rayStartParams.resources` 是否存在，并确认转义格式正确：

```yaml
rayStartParams:
  resources: '"{\"NPU\": 8}"'
```

这里的 `NPU` 是 Ray 自定义资源名称，后续 Ray 任务也要用同一个名字申请资源：

```python
@ray.remote(resources={"NPU": 1})
def run_on_npu():
    ...
```

### 任务中无法导入 daft

确认 `daft` 安装到了 worker 实际激活的 conda 环境中：

```bash
/root/miniconda3/envs/ms/bin/python -m pip show daft
```

如果包安装在系统 Python 或其他 conda 环境里，Ray worker 启动后就可能找不到。

### 容器内找不到 Ascend 动态库

检查 hostPath 挂载和环境变量加载：

```bash
kubectl exec -n ray-demo -it <worker-pod-name> -- bash
ls /usr/local/Ascend/driver
ls /usr/local/dcmi
echo $ASCEND_HOME_PATH
```

如果路径存在但环境变量为空，重点检查 worker 启动命令中的：

```bash
source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
source /usr/local/Ascend/cann/nnal/atb/set_env.sh
```

### 镜像拉取失败

如果 Pod 报 `ImagePullBackOff`，需要检查私有仓库地址、节点网络连通性，以及 containerd 是否允许 HTTP 仓库：

```bash
k3s ctr images pull --plain-http 110.120.0.3:8889/demo:v2
```

## 6. 小结

这份配置的核心逻辑是：Kubernetes 负责把 worker Pod 放到真实 NPU 节点并分配设备，Ray 负责把需要 NPU 的任务调度到已经注册 `NPU` 自定义资源的 worker 上。镜像、设备申请、hostPath 挂载和 Ray 资源声明必须同时正确，NPU 任务才能稳定运行。
