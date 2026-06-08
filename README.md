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

如果有多个 NPU worker 节点，需要在每个可能调度 worker pod 的节点上执行导入操作。多个NPU worker 的话只需要在一个上构建好了images，即可并行分发到各个worker所在服务器上
```
#!/bin/bash

# 填写你要传输的镜像名
IMAGE="demo:v1"

# 填写目标节点 IP
NODE1="110.129.0.12"
NODE2="110.129.0.14"
NODE3="110.129.0.5"

# 填写对应的密码 
PASS1=''
PASS2=''
PASS3=''

# ssh 附加参数：禁止主机指纹验证
SSH_OPTS="-o StrictHostKeyChecking=no"

echo "=== 开始从 Docker 单次读取磁盘，并行向 3 个 K3s 节点传输镜像 ==="

# 【核心修改点】增加了一个 >(...) 分支。
# pv 监控 21G -> tee 复制给 NODE1 -> tee 复制给 NODE2 -> 主管道直连 NODE3
docker save $IMAGE | \
  pv -s 21G | \
  tee >(sshpass -p "$PASS1" ssh $SSH_OPTS root@$NODE1 "k3s ctr images import -") \
      >(sshpass -p "$PASS2" ssh $SSH_OPTS root@$NODE2 "k3s ctr images import -") \
      | sshpass -p "$PASS3" ssh $SSH_OPTS root@$NODE3 "k3s ctr images import -"

echo "=== 所有节点并行传输完成 ==="
```



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

## 9. 使用 Ray Jobs API提交任务
只需要把脚本“打包”扔给 Head 节点，Head 节点会自己去执行，你随时可以断开连接或查询状态。
提交的任务
```
import os
import socket
import ray
from collections import Counter

ray.init(
    runtime_env={
        "env_vars": {
            # 保持你的底层依赖路径不变
            "LD_LIBRARY_PATH": "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/tools/aml/lib64:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/tools/aml/lib64/plugin:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64/plugin/opskernel:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64/plugin/nnengine:/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/cann/nnal/atb/8.3.RC1/atb/cxx_abi_1/lib:/usr/local/lib"
        }
    }
)

@ray.remote(resources={"NPU": 1})
def npu_smoke(i: int):
    import torch_npu
    import torch

    # 1. 获取 Ray 分配给当前 Task 的物理 NPU 资源 ID
    assigned_npus = ray.get_runtime_context().get_resource_ids().get("NPU", [])
    if assigned_npus:
        # Ray 返回格式通常是 [('0', 1.0)], 取出卡号
        ray_npu_id = int(assigned_npus[0][0])
    else:
        ray_npu_id = 0

    # 2. 判断 Ray 是否做了环境变量隔离
    # 如果系统环境变量中已经被 Ray 注入了隔离变量，逻辑设备号固定为 0
    # 否则，我们使用 Ray 分配的物理 ID 作为当前设备的 ID
    if "ASCEND_RT_VISIBLE_DEVICES" in os.environ:
        local_dev_id = 0
    else:
        local_dev_id = ray_npu_id

    # 3. 昇腾设备设置
    torch_npu.npu.set_device(local_dev_id)
    dev_id = torch_npu.npu.current_device()
    host = socket.gethostname()

    # 4. 在正确绑定的 NPU 上进行矩阵运算验证
    a = torch.randn(1024, 1024, device=f"npu:{local_dev_id}")
    b = torch.randn(1024, 1024, device=f"npu:{local_dev_id}")
    c = torch.matmul(a, b)

    return {
        "task_id": i,
        "host": host,
        "ray_npu_id": ray_npu_id,
        "shape": tuple(c.shape)
    }

if __name__ == "__main__":
    # 总共有 2台机器 * 8张卡 = 16张 NPU。
    # 我们投递 32 个任务，这样可以确保每张卡分到 2 个任务，完整测试集群的调度和计算能力。
    TOTAL_TASKS = 32
    print(f"🚀 开始向集群投递 {TOTAL_TASKS} 个分布式 NPU 任务...")

    futures = [npu_smoke.remote(i) for i in range(TOTAL_TASKS)]
    results = ray.get(futures)

    # 统计数据
    host_counter = Counter()
    npu_usage = Counter()

    print("\n" + "="*60)
    print("📊 任务执行明细:")
    for res in results:
        host = res['host']
        npu_id = res['ray_npu_id']
        host_counter[host] += 1
        npu_usage[f"{host} -> NPU:{npu_id}"] += 1
        print(f"✅ 任务 {res['task_id']:>2d} 完成 | 节点: {host:<30} | 物理NPU ID: {npu_id} | 维度: {res['shape']}")

    print("\n" + "="*60)
    print("📈 节点负载统计:")
    for host, count in host_counter.items():
        print(f"  - 机器 [{host}]: 执行了 {count} 个任务")

    print("\n📈 每张 NPU 卡负载统计:")
    for key, count in sorted(npu_usage.items()):
        print(f"  - {key}: 执行了 {count} 个任务")
    print("="*60 + "\n")
```
通过python执行
```
from ray.job_submission import JobSubmissionClient

# 1. 连接到 Head 节点的 Dashboard 端口 (不是 6379 也不是 10001)
client = JobSubmissionClient("http://10.42.0.21:8265")

# 2. 提交任务python submit_job.py
job_id = client.submit_job(
    # entrypoint 是集群将要执行的命令
    entrypoint="python test_npu.py",
    # runtime_env 的 working_dir 会自动把 serve00 上的代码文件打包传到集群上
    runtime_env={
        "working_dir": "./",  # 假设 test_npu.py 和提交脚本在同一个目录
    }
)

print(f"✅ 任务已成功提交！Job ID: {job_id}")
```


使用 SSH 本地端口转发
ssh -L 8265:10.42.0.21:8265 root@110.120.0.3

输入密码登录成功后，保持这个终端窗口不要关闭。在地址栏输入：http://localhost:8265 或者 http://127.0.0.1:8265
即可打开Ray Dashboard 查看或监控已提交的任务。






