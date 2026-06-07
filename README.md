# K8S 集群启动 NPU Worker 节点记录

本文档整理了在 K8S/K3s 集群中为 RayCluster 启动昇腾 NPU worker 节点的主要步骤，包括 worker 镜像准备、镜像导入、RayCluster 配置以及 NPU 任务验证。

## 1. 准备 Worker 镜像

Worker 镜像基于已有的 `ms_verl_ful:v1`，在其中安装 `daft`，并通过 entrypoint 自动加载昇腾 CANN/ATB 环境变量。

### Dockerfile

```dockerfile
FROM ms_verl_ful:v1

ENV MS_VENV=/root/miniconda3/envs/ms
ENV PATH="${MS_VENV}/bin:${PATH}"

# 确保安装到 ms conda 环境里
RUN ${MS_VENV}/bin/python -m pip install daft -i https://mirrors.aliyun.com/pypi/simple/

# 只对交互式 bash 有帮助，不作为核心依赖
RUN echo 'source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh' >> /etc/bash.bashrc && \
    echo 'source /usr/local/Ascend/cann/nnal/atb/set_env.sh' >> /etc/bash.bashrc

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
```

### entrypoint.sh

```bash
#!/bin/bash
set -e

# 激活昇腾环境
source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
source /usr/local/Ascend/cann/nnal/atb/set_env.sh

# 传递并执行主程序命令
exec "$@"
```

### 构建镜像

```bash
docker build -t ms_worker_daft:v2 .
docker images
```

确认镜像存在：

```bash
docker images | grep ms_worker_daft
```

## 2. 将镜像导入 K3s

如果 Ray worker 使用的是本地镜像，并且 `imagePullPolicy` 配置为 `IfNotPresent`，需要把镜像导入到 K3s 使用的 containerd 中。

```bash
docker save ms_worker_daft:v2 | k3s ctr images import -
```

如果有多个 NPU worker 节点，需要在每个可能调度 worker pod 的节点上执行导入操作。

## 3. 导出 RayCluster 配置

先导出现有 RayCluster 配置：

```bash
kubectl get raycluster raycluster-npu-pipeline -n ray-testfieldv2 -o yaml > raycluster-npu-pipeline.yaml
```

导出的 YAML 会包含 `status`、`resourceVersion`、`uid`、`creationTimestamp` 等运行时字段。重新应用前建议删除这些字段，只保留可维护的 `metadata` 和 `spec`。

## 4. RayCluster 核心配置示例

下面是整理后的关键配置。核心点包括：

- head 节点固定调度到 `server-00`
- worker 节点通过 `nodeSelector` 调度到 910B3 NPU 节点
- worker 声明 `huawei.com/Ascend910: "8"`
- Ray worker 通过 `resources: '"{\"NPU\": 8}"'` 向 Ray 注册 NPU 资源
- 挂载宿主机的 Ascend driver 和 DCMI 路径
- worker 启动时显式加载 conda、driver、CANN 和 ATB 环境

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: raycluster-npu-pipeline
  namespace: ray-testfieldv2
  labels:
    app.kubernetes.io/instance: raycluster-npu
spec:
  autoscalerOptions:
    idleTimeoutSeconds: 60
  enableInTreeAutoscaling: true
  rayVersion: 2.10.0
  headGroupSpec:
    serviceType: ClusterIP
    rayStartParams:
      dashboard-host: 0.0.0.0
      num-cpus: "0"
    template:
      spec:
        nodeSelector:
          kubernetes.io/hostname: server-00
        tolerations:
          - effect: NoSchedule
            key: node-role.kubernetes.io/control-plane
            operator: Exists
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
              image: docker.io/library/ms_worker_daft:v2
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

                  if [ -f /usr/local/Ascend/driver/bin/setenv.bash ]; then
                    source /usr/local/Ascend/driver/bin/setenv.bash
                  fi

                  source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
                  source /usr/local/Ascend/cann/nnal/atb/set_env.sh

                  which python
                  echo "$CONDA_DEFAULT_ENV"

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
kubectl apply -f raycluster-npu-pipeline.yaml
```

查看 RayCluster 和 Pod 状态：

```bash
kubectl get raycluster raycluster-npu-pipeline -n ray-testfieldv2
kubectl get pods -n ray-testfieldv2 -o wide
```

## 5. 进入 Worker 验证环境

找到 NPU worker pod：

```bash
kubectl get pods -n ray-testfieldv2 | grep npu-workers
```

进入 worker：

```bash
kubectl exec -it raycluster-npu-pipeline-npu-workers-worker-shkmc -n ray-testfieldv2 -- bash
```

加载 CANN 环境并检查动态库路径：

```bash
source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
echo "$LD_LIBRARY_PATH"
```

如果路径不存在，可以先查找：

```bash
find /usr/local/Ascend -name set_env.sh
```

## 6. 在 Head 节点提交 NPU 测试任务

进入 head pod：

```bash
kubectl get pods -n ray-testfieldv2 | grep head
kubectl exec -it raycluster-npu-pipeline-head-2nchk -n ray-testfieldv2 -- bash
```

创建测试脚本：

```bash
cat << 'EOF' > test_npu.py
import socket

import ray


ray.init(
    address="auto",
    runtime_env={
        "env_vars": {
            "LD_LIBRARY_PATH": "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/tools/aml/lib64:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/tools/aml/lib64/plugin:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64/plugin/opskernel:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64/plugin/nnengine:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/cann/nnal/atb/8.3.RC1/atb/cxx_abi_1/lib:/usr/local/lib"
        }
    },
)


@ray.remote(resources={"NPU": 1})
def npu_smoke(i: int):
    # 在 worker 进程内部导入，避免 head 节点缺失依赖
    import torch
    import torch_npu

    torch_npu.npu.set_device(0)

    dev_id = torch_npu.npu.current_device()
    host = socket.gethostname()

    a = torch.randn(1024, 1024, device="npu:0")
    b = torch.randn(1024, 1024, device="npu:0")
    c = torch.matmul(a, b)

    return {
        "task_id": i,
        "host": host,
        "npu_id": int(dev_id),
        "shape": tuple(c.shape),
    }


if __name__ == "__main__":
    print("开始向集群投递任务...")
    futures = [npu_smoke.remote(i) for i in range(4)]
    results = ray.get(futures)

    for res in results:
        print(
            f"任务 {res['task_id']} 完成 | "
            f"节点: {res['host']} | "
            f"NPU设备ID: {res['npu_id']} | "
            f"维度: {res['shape']}"
        )
EOF
```

运行测试：

```bash
python test_npu.py
```

如果任务成功，会看到多个 Ray task 在 worker 节点上完成矩阵乘法，并返回节点名、NPU 设备 ID 和输出矩阵维度。

## 7. 常见检查点

1. 确认 worker 镜像已经导入到 K3s containerd。
2. 确认 worker pod 调度到了带 910B3 NPU 的节点。
3. 确认 `/usr/local/Ascend/driver` 和 `/usr/local/dcmi` 在宿主机存在，并且 pod 内挂载成功。
4. 确认 worker 启动脚本中加载了 conda、driver、CANN 和 ATB 环境变量。
5. 确认 Ray 中已经注册 `NPU` 资源，可以通过 Ray dashboard 或 Ray API 查看资源。
6. 如果 `torch_npu` 导入失败，优先检查 conda 环境、CANN 版本、`LD_LIBRARY_PATH` 和镜像内依赖是否一致。

## 8. TODO

1. Ray 提交任务时，目前仍然需要手动注入昇腾相关环境变量，尤其是 `LD_LIBRARY_PATH`。后续需要把这部分环境变量固化到镜像、Ray runtime environment 或 worker 启动脚本中，减少每次提交任务时的手工配置。
2. 增加多 worker 场景测试，将 `npu-workers` 扩展到多个副本，验证 Ray task 是否能按 `NPU` 资源正确分发到不同 worker 节点，并观察调度、资源占用和任务执行结果。
3. 精简最开始的 worker 镜像，去掉无关依赖、缓存和临时文件，降低镜像体积，提升镜像分发、导入和 worker 启动速度。
