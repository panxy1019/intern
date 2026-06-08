# Ray 基础知识整理

Ray 是一个面向 Python 的分布式计算框架。它的核心价值是：尽量保留本地 Python 编程体验，同时把函数、类、数据处理、训练和在线服务扩展到多机集群。

<img width="1620" height="971" alt="ChatGPT Image 2026年6月8日 19_02_00" src="https://github.com/user-attachments/assets/668a62f2-e6aa-42d1-9ca1-d17579f05fed" />



## 1. Ray 解决什么问题

单机 Python 程序通常会遇到三个瓶颈：CPU/GPU/NPU 算力不够、内存放不下中间数据、任务之间缺少统一的调度和容错机制。Ray 的作用是把这些问题抽象成更容易使用的分布式语言：

- 用 task 表示无状态并行函数。
- 用 actor 表示有状态的长期服务或模型实例。
- 用 object store 管理跨进程、跨节点传递的数据对象。
- 用 resource scheduler 按 CPU、GPU、NPU 等资源约束调度任务。
- 用 Dashboard、Job Submission、KubeRay 等工具管理集群运行。

换句话说，Ray 不只是负责“把代码跑起来”，还负责把分布式程序中最容易出错的调度、对象传递、资源标记和运行状态管理统一起来。

Ray 的优势主要体现在以下几个方面：

- 编程模型简单：开发者可以用普通 Python 函数和类扩展出分布式 task/actor，不需要从一开始就手写复杂的 RPC、队列或多进程通信逻辑。
- 资源调度统一：同一套程序可以同时声明 CPU、GPU、NPU、内存和自定义资源需求，由 Ray 根据资源约束选择合适 worker。
- 适合异构集群：在同时存在 CPU 节点、GPU 节点、NPU 节点的场景中，可以通过自定义资源把不同任务准确投放到不同硬件上。
- 异步执行效率高：远程调用会先返回 `ObjectRef`，程序可以继续提交后续任务，再统一等待结果，从而更容易把集群资源跑满。
- 生态完整：Ray Core 负责分布式执行，Ray Data、Ray Train、Ray Tune、Ray Serve 等库继续覆盖数据处理、训练、调参和在线服务。
- 迁移成本低：很多本地 Python 代码只需要在关键函数或类上增加 `@ray.remote`，就可以逐步改造成分布式程序。

## 2. 核心概念

| 概念 | 含义 | 为什么重要 |
| --- | --- | --- |
| Driver | 提交 Ray 程序的入口进程 | 创建 task/actor，并通过 `ray.get()` 获取结果 |
| Head node | 集群控制节点 | 保存集群元数据、Dashboard、Job Submission 入口 |
| Worker node | 执行计算的节点 | 运行 Ray worker 进程，真正执行 task/actor |
| Task | 用 `@ray.remote` 标记的无状态函数 | 适合批量并行、数据预处理、独立推理任务 |
| Actor | 用 `@ray.remote` 标记的有状态类 | 适合模型常驻内存、参数服务器、队列消费者 |
| ObjectRef | Ray 对远程结果的引用 | 任务提交后立即返回，结果可以异步获取 |
| Object store | 节点上的共享对象存储 | 减少进程间复制，支持跨任务传递大对象 |
| Runtime env | 任务运行环境声明 | 分发代码、pip 依赖、环境变量等轻量运行配置 |
| Custom resources | 自定义资源，例如 `NPU` | 让 Ray 按特殊硬件或业务资源调度任务 |

## 3. Task 和 Actor

Task 适合“输入明确、执行完就结束”的计算。Ray 会把每次调用调度到集群中可用的 worker 上。

```python
import ray


@ray.remote
def square(x):
    return x * x


ray.init()
refs = [square.remote(i) for i in range(10)]
print(ray.get(refs))
```

Actor 适合“需要长期保存状态”的计算，例如加载一次模型，然后反复处理请求。

```python
import ray


@ray.remote
class Counter:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1
        return self.value


ray.init()
counter = Counter.remote()
print(ray.get(counter.inc.remote()))
```

Task 和 Actor 的区别可以简单理解为：task 像一次性函数调用，actor 像运行在集群里的长期对象。

## 4. Ray 的执行流程

一个 Ray 程序从提交到执行，大致经过以下步骤：

1. Driver 创建远程 task 或 actor。
2. Ray 立即返回 `ObjectRef`，调用方不用阻塞等待结果。
3. Ray scheduler 根据资源需求选择合适节点。
4. Worker 进程执行实际 Python 代码。
5. 结果写入 object store。
6. Driver 或下游任务通过 `ray.get()` 或依赖引用读取结果。

这种方式的好处是，业务代码只需要表达“要做什么”和“需要什么资源”，任务放到哪台机器、对象如何传递、多个任务如何排队由 Ray 统一处理。

## 5. 资源模型

Ray 调度任务时会读取资源声明。常见资源包括 CPU、GPU，也可以使用自定义资源，例如 NPU。

```python
import ray


@ray.remote(num_cpus=2, resources={"NPU": 1})
def run_inference(batch):
    return batch
```

这里的 `resources={"NPU": 1}` 只告诉 Ray “这个任务需要一个名为 NPU 的资源”。Ray 本身不会安装 NPU 驱动，也不会自动创建 Kubernetes 设备资源。因此在 K8s/KubeRay 场景中需要同时满足两件事：

- Kubernetes Pod 申请真实设备，例如 `huawei.com/Ascend910: "8"`。
- Ray worker 启动时注册自定义资源，例如 `resources: '{"NPU": 8}'`。

这也是 README 中同时配置 Kubernetes `resources` 和 Ray `rayStartParams.resources` 的原因。

## 6. Ray 生态

Ray 的生态可以分为两层：

- Ray Core：提供 task、actor、object store、resource scheduling 等底层分布式能力。
- Ray Libraries：基于 Ray Core 构建的数据处理、训练、调参和服务框架。

常见库包括：

| 模块 | 主要用途 |
| --- | --- |
| Ray Data | 分布式数据读取、转换、批处理 |
| Ray Train | 分布式模型训练 |
| Ray Tune | 超参数搜索和实验管理 |
| Ray Serve | 在线推理服务部署 |
| RLlib | 强化学习训练 |
| KubeRay | 在 Kubernetes 上管理 RayCluster |

## 7. Ray 与 Kubernetes

Kubernetes 负责容器生命周期和硬件设备分配，Ray 负责 Python 分布式任务调度。KubeRay 把两者连接起来：用户提交 `RayCluster` 资源后，KubeRay Operator 会创建 head Pod、worker Pod、Service，并在需要时协助扩缩容。


<img width="1536" height="1024" alt="ChatGPT Image 2026年6月8日 18_55_31" src="https://github.com/user-attachments/assets/25cdf9d7-1cac-4a39-98ed-95d563c08597" />

在 Kubernetes 中使用 Ray 时，可以把责任边界理解为：

- Kubernetes 决定 Pod 在哪台机器上运行。
- Device plugin 决定容器能看到哪些硬件设备。
- KubeRay 决定 Ray head 和 worker 如何创建。
- Ray 决定 task/actor 在哪些 worker 进程上执行。

RayCluster 的优点是把 Ray 集群的生命周期和 Kubernetes 的资源管理能力结合起来，适合长期运行、可复现、可扩缩的生产环境：

- 资源自动分配：在 `workerGroupSpecs` 中声明 CPU、内存、GPU/NPU 等资源后，Kubernetes 会根据请求为 worker Pod 分配节点和设备，Ray 再根据 `rayStartParams.resources` 把这些资源注册到 Ray 调度器中。
- 调度更准确：Kubernetes 的 `nodeSelector`、taint/toleration、device plugin 负责把 Pod 放到真实具备硬件的节点上，Ray 的自定义资源负责把 task/actor 放到具备对应资源的 worker 上。
- 弹性扩缩容：RayCluster 可以配置 `minReplicas`、`maxReplicas` 和 autoscaling 选项，在任务压力变化时增加或减少 worker，减少人工扩容和空闲资源浪费。
- 环境可复现：head 和 worker 都由镜像、启动命令、挂载路径和资源声明描述，集群重建时不依赖手工登录节点逐项配置。
- 运维入口统一：通过 Kubernetes 查看 Pod、Service、日志和事件，通过 Ray Dashboard 查看任务、actor、对象和 Ray 资源，两层状态可以互相定位问题。
- 故障恢复更方便：当 worker Pod 异常退出时，Kubernetes 可以重新拉起 Pod；Ray 也能感知 worker 状态变化，并继续调度后续任务。
- 适合异构硬件管理：对于 NPU/GPU 混合集群，可以把不同 worker group 绑定到不同节点标签和资源类型，避免任务落到错误硬件上。

对于 NPU 场景，最容易混淆的是“Pod 拿到 NPU”和“Ray task 使用 NPU”不是同一件事。前者依赖 Kubernetes 扩展资源，后者依赖 Ray 自定义资源。两层资源声明都正确，任务才能稳定落到 NPU worker 上。
<img width="1536" height="1024" alt="ChatGPT Image 2026年6月8日 19_16_21" src="https://github.com/user-attachments/assets/43ec9340-4b5f-483a-8771-bd83da315aed" />


## 8. 常用命令

本地或容器中启动一个 head 节点：

```bash
ray start --head --dashboard-host=0.0.0.0
```

查看集群资源：

```bash
ray status
```

通过 Job Submission 提交任务：

```bash
ray job submit --address http://127.0.0.1:8265 -- python app.py
```

在 Kubernetes 中查看 RayCluster：

```bash
kubectl get raycluster -A
kubectl get pods -n ray-demo -o wide
kubectl logs -n ray-demo -l ray.io/node-type=head --tail=100
```
