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
CMD ["/bin/bash"]
```




### 构建镜像

```bash
docker build -t demo:v2 .
docker images
```

如果 Ray worker 使用的是本地镜像，需要把镜像导入到 K3s 使用的 containerd 中。通过将已有的镜像打包发送至私有仓库后，通过脚本分发到各个server节点上
docker tag demo:v1 110.120.0.3:8889/demo:v2
docker push 110.120.0.3:8889/demo:v2
```
#!/bin/bash

# 私有仓库的镜像地址
IMAGE="110.120.0.3:8889/demo:v2"

# 目标节点列表
NODES=("110.129.0.12" "110.129.0.14" "110.129.0.5")

# 统一密码
PASS=""
SSH_OPTS="-o StrictHostKeyChecking=no"
echo "=== 开始通知所有节点并发拉取镜像 ==="
# 循环遍历每个节点，下发拉取指令
for NODE in "${NODES[@]}"; do
  echo "正在触发节点 $NODE 的下载任务..."

  # 注意句末的 & 符号！它让这个 SSH 命令在后台静默执行，不阻塞下一个循环
  sshpass -p "$PASS" ssh $SSH_OPTS root@$NODE "k3s ctr images pull --plain-http $IMAGE" &
done
echo "=== 所有节点已开始疯狂下载，请耐心等待... ==="
# wait 命令是并发控制的灵魂，它会卡在这里，直到上面 3 个后台下载任务全部跑完
wait
echo "=== 所有节点的镜像拉取任务均已成功完成！ ==="
```
chmod +x shareimages.sh
./shareimages.sh






## 3. RayCluster 核心配置示例

下面是整理后的关键配置。核心点包括：

- head 节点固定调度到 `server-00`
- 集群名以及命名空间metadata:
  name: raycluster-npu-demo
  namespace: ray-demo
- worker 节点通过 `nodeSelector` 调度到 910B3 NPU 节点
- worker 声明 `huawei.com/Ascend910: "8"`
- Ray worker 通过 `resources: '"{\"NPU\": 8}"'` 向 Ray 注册 NPU 资源
- 挂载宿主机的 Ascend driver 和 DCMI 路径
- worker 启动时显式加载 conda、driver、CANN 和 ATB 环境
- head镜像默认配置 ray-2.10.0-py3100-amd64
- worker镜像为上文分发到server节点上的镜像 110.120.0.3:8889/demo:v2
- 相关配置信息workerGroupSpecs:
    - groupName: npu-workers
      replicas: 1#worker 个数
      minReplicas: 1
      maxReplicas: 4
      numOfHosts: 1
      rayStartParams:
        resources: '"{\"NPU\": 8}"' 

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: raycluster-npu-demo
  namespace: ray-demo
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

新建一个namespace并应用配置：

```bash
kubectl create ns rat-demo
kubectl apply -f raycluster-npu-demo.yaml
```
## 3. 提交测试任务
通过ssh -L 8265:10.42.0.23:8265 admin@110.120.0.3可以dashboard,其中10.42.0.23为head节点的ip
通过python api提交测试任务

```
import time
from ray.job_submission import JobSubmissionClient

# 1. 连接到 Head 节点的 Dashboard 端口
client = JobSubmissionClient("http://10.42.0.23:8265")

print("🔄 正在打包并提交任务到 Ray 集群...")

# 2. 提交任务
job_id = client.submit_job(
    # 集群执行的命令
    entrypoint="python test_daft_env.py",
    # runtime_env 的 working_dir 会把当前目录 (包括 test_npu.py) 打包传给集群
    runtime_env={
        "working_dir": "./"
    }
)

print(f"✅ 任务已成功提交！")
print(f"🆔 Job ID: {job_id}")
print("-" * 50)
print("📜 以下是集群实时传回的运行日志：\n")

# 3. 实时跟踪并打印集群的日志输出
try:
    for line in client.tail_job_logs(job_id):
        print(line, end="")
except KeyboardInterrupt:
    print("\n\n  你在本地按下了 Ctrl+C。")
    print("  任务仍然在集群上继续运行。如果想停止它，请使用：")
    print(f"    ray job stop {job_id} --address http://10.42.0.21:8265")

# 4. 获取最终状态
status = client.get_job_status(job_id)
print("\n" + "-" * 50)
print(f"🏁 任务最终状态: {status}")
```


