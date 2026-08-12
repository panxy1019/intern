# Haidass / LightEval Ascend 910B 评估 Worker 技术手册

## 1. 文档范围

本文记录当前 `server-00 -> Ray Head -> gpu-server-00/Ascend 910B3 Worker`
评估链路的真实部署状态、代码改动、镜像边界、LightEval 兼容方式、迁移方法、
执行命令、PIQA/HellaSwag 全量结果以及 bad-case 分析方法。

关键结论：当前方案可以迁移和复用，但目前不是一个“所有依赖均已固化”的新评估
镜像。基础 NPU 环境来自既有镜像，LightEval 运行时、离线 benchmark 和模型缓存由
Ray 任务在 Pod 启动后注入。若要长期生产复用，建议在验证完成后构建不可变
`lighteval-ascend-worker` 镜像。

## 2. 当前拓扑

```text
server-00 / amd64
├── K3s API / KubeRay / Volcano
├── Ray Head
│   ├── Ray 2.10.0
│   ├── num-cpus=0
│   ├── 不申请 NPU
│   ├── 接受提交、保存结果
│   └── HTTP 8081 暴露只读模型缓存
└── /home/admin/models/Haidass-143M-v1
    └── 固定 revision + SHA256SUMS

gpu-server-00 / arm64 / Ascend 910B3
└── Ray Worker x 1
    ├── 申请 huawei.com/Ascend910=1
    ├── Ray: CPU=12, NPU=1, HAIDASS_EVAL=1
    ├── Transformers + Accelerate + torch_npu
    ├── LightEval 0.9.2 隔离运行时
    ├── 直接执行 benchmark 推理
    └── 将 JSON/details/bad cases 返回 Head
```

Kubernetes 对象：

```text
Namespace:  haidass-eval
RayCluster: raycluster-haidass-910b
Head node:  server-00
Worker node: gpu-server-00
```

## 3. 镜像与精确版本

### 3.1 Head 镜像

```text
crpi-gcyqahoi1kzpijkb.cn-hangzhou.personal.cr.aliyuncs.com/
panxy1019/panxy:ray-2.10.0-py3100-amd64

digest:
sha256:f83723b3213434f2ada98987cf5111cc7cf32aa46178937138bb5c5989fc334d
```

### 3.2 Worker 镜像

```text
110.120.0.3:8889/demo:v2

digest:
sha256:1ec90a9d8202cceb0f89b575b0d9773b3e18a92bdb00a855a6a2fc375f0dcee3
```

Worker 镜像的已验证栈：

```text
Architecture  aarch64
Python        3.10.0
Ray           2.10.0
Driver        25.5.1（宿主机挂载）
CANN          8.3.RC1
torch         2.7.1
torch_npu     2.7.1
Transformers  4.57.1
Accelerate    1.10.1
datasets      3.6.0
Device        Ascend910B3
```

### 3.3 是否构建了新镜像

没有。本次没有执行 `docker build`，也没有向仓库推送新的评估镜像。

以下内容不在 `demo:v2` 镜像层中：

- LightEval 0.9.2；
- LightEval 的补充纯 Python 依赖；
- ARC-Easy、PIQA、HellaSwag 离线数据；
- Haidass 模型权重；
- 本项目 runner、dataset router 和 bad-case analyzer；
- 评估结果。

这些内容分别位于 Worker `emptyDir` 缓存、Ray `working_dir` 和 server-00
持久目录。因此重建 Worker 后，模型和运行时缓存会丢失，但一键 runner 会重新注入。

## 4. 对 LightEval 做了什么修改

### 4.1 没有修改 LightEval wheel 源码

使用官方 `lighteval==0.9.2` wheel：

```text
wheel SHA256:
24905ae81dbce1b9e1fa71d9ef0d1de6cf07772be7efacf3442fbff11d4cb988
```

没有 fork、重新打 wheel、修改 `TransformersModel`、修改 metric、修改 prompt、
修改 request batching，也没有使用 CUDA/vLLM backend。

### 4.2 使用的官方路径

```text
lighteval accelerate
-> TransformersModel
-> Hugging Face Accelerate
-> device=npu
-> torch_npu
```

验证日志明确包含：

```text
gathered_tensor tensor([0], device='npu:0')
Using Data Parallelism, putting model on device npu
```

### 4.3 外部兼容层

项目提供 `offline_dataset_router.py`。LightEval 0.9.2 的 custom-task loader 会导入
该模块，模块只替换 `lighteval.tasks.lighteval_task.download_dataset_worker` 的数据
传输实现：

```text
ai2_arc / ARC-Easy -> 本地 Parquet
ybisk/piqa          -> 本地 JSONL
hellaswag           -> 本地 Parquet
其他 dataset        -> 调回 LightEval 原始 downloader
```

`TASKS_TABLE=[]`，因此 router 不注册或覆盖任何 task。以下均仍是 LightEval 0.9.2
默认 registry 中的官方定义：

- `lighteval|arc:easy|0|0`
- `lighteval|piqa|0|0`
- `leaderboard|hellaswag|0|0`

保留的语义包括 prompt、split、few-shot 策略、metric、normalization 和 stop sequence。

### 4.4 为什么必须离线数据 router

910B Worker 访问 Hugging Face 代理时持续 connect timeout，而 server-00 代理链路
可用。若让 Worker 在线下载 benchmark，任务会在模型已加载后长时间等待网络。

现在链路变为：

```text
server-00 下载并校验 benchmark
-> Ray working_dir 压缩上传
-> Worker 本地 datasets.load_dataset()
-> NPU 评估
```

这不是评估逻辑修改，只是将数据获取从在线 Hub 改成固定离线文件。

## 5. 代码改动清单

### 5.1 Kubernetes

`k8s/raycluster.yaml`：

- Head 固定 `server-00`、`num-cpus=0`；
- Worker 固定 `gpu-server-00` 和 `910B3`；
- 每个 Worker 申请一张 `huawei.com/Ascend910`；
- Worker 注册 `NPU=1`、`HAIDASS_EVAL=1`；
- 挂载宿主机 Ascend driver/DCMI；
- 注入 CANN 环境和代理；
- Head 提供模型 HTTP cache。

`k8s/npu-image-preflight.yaml`：

- Volcano 调度的单卡一次性诊断 Pod；
- 检查设备映射、Driver/CANN、torch_npu；
- 执行 BF16 NPU matmul。

### 5.2 评估执行

`phase2/run_phase2.sh`：

- 找到 Head Pod；
- 使用唯一临时目录上传任务，防止旧代码缓存；
- 将参数传给 Head；
- 从 Head 取回结果 tarball 并解压。

`phase2/submit_phase2.py`：

- 连接现有 Ray；
- 上传 `working_dir`；
- 提交资源约束任务：

```python
@ray.remote(num_cpus=8, resources={"NPU": 1, "HAIDASS_EVAL": 1})
```

`phase2/worker_eval.py`：

- 校验并缓存模型；
- 从 wheelhouse 离线安装 LightEval；
- 运行 NPU generation smoke；
- 调用官方 `python -m lighteval accelerate`；
- 收集 LightEval 主 JSON 与 details Parquet；
- 生成 bad-case JSON/Markdown；
- 打包结果返回 Head。

`phase2/offline_dataset_router.py`：

- 仅路由 benchmark 数据源；
- 不定义或修改 task/metric/prompt。

### 5.3 离线依赖

LightEval 运行时安装到：

```text
/cache/models/lighteval-runtime-0.9.2
```

通过 `PYTHONPATH` 优先加载，不修改 `/root/miniconda3/envs/ms`。wheelhouse 包括：

- lighteval 0.9.2；
- pytablewriter 及 dataproperty/typepy 等依赖；
- colorlog、aenum、termcolor、httpx；
- latex2sympy2_extended 1.0.6 和 antlr runtime；
- more-itertools；
- chardet 5.2.0。

没有安装新的 torch、torch_npu、Transformers、Accelerate、datasets 或 NumPy，避免
覆盖已验证的 NPU 栈。

## 6. 模型路径与命令映射

用户原始命令：

```bash
lighteval accelerate \
  "model_name=/home/models/188000,batch_size=16" \
  "leaderboard|hellaswag|0|0" \
  --output-dir ./hellaswag_result \
  --save-details
```

在当前 Worker 内的直接等价命令为：

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate ms
source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
source /usr/local/Ascend/cann/nnal/atb/set_env.sh

export TORCH_DEVICE_BACKEND_AUTOLOAD=0
export PYTHONPATH=/cache/models/lighteval-runtime-0.9.2:$PYTHONPATH
export LIGHTEVAL_DATA_ROOT=/path/to/phase2/datasets

python -m lighteval accelerate \
  "model_name=/cache/models/Haidass-143M-v1,dtype=bfloat16,batch_size=16,model_parallel=false,compile=false" \
  "leaderboard|hellaswag|0|0" \
  --custom-tasks /path/to/phase2/offline_dataset_router.py \
  --dataset-loading-processes 1 \
  --output-dir ./hellaswag_result \
  --save-details
```

注意：LightEval 0.9.2 实际会将主 JSON/details 保存到模型目录，`worker_eval.py`
已负责将这些文件归集到指定 run 目录。

## 7. 推荐的一键执行方式

在 server-00：

```bash
sudo -i
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

### 7.1 全量 PIQA

```bash
LIGHTEVAL_MAX_SAMPLES=0 \
LIGHTEVAL_BATCH_SIZE=32 \
LIGHTEVAL_RUN_NAME=piqa-full \
LIGHTEVAL_TASKS='lighteval|piqa|0|0' \
bash /home/admin/haidass_eval/phase2/run_phase2.sh
```

### 7.2 全量 HellaSwag

```bash
LIGHTEVAL_MAX_SAMPLES=0 \
LIGHTEVAL_BATCH_SIZE=32 \
LIGHTEVAL_RUN_NAME=hellaswag-full \
LIGHTEVAL_TASKS='leaderboard|hellaswag|0|0' \
bash /home/admin/haidass_eval/phase2/run_phase2.sh
```

### 7.3 指定其他模型

`MODEL_DIR` 必须是 Worker 容器内可见路径：

```bash
MODEL_DIR=/cache/models/0806haida_anneal_ckpt188000 \
LIGHTEVAL_MAX_SAMPLES=0 \
LIGHTEVAL_BATCH_SIZE=32 \
LIGHTEVAL_RUN_NAME=piqa-ckpt188000 \
LIGHTEVAL_TASKS='lighteval|piqa|0|0' \
bash /home/admin/haidass_eval/phase2/run_phase2.sh
```

当前 runner 的自动下载函数固定缓存 Haidass-143M-v1。若指定其他模型，应先通过
PVC、对象存储下载或扩展模型 manifest 将该目录放入 Worker。不要直接填写只在
server-00 存在、Worker 不可见的 `/home/models/...` 路径。

### 7.4 Smoke 与全量

```text
LIGHTEVAL_MAX_SAMPLES=16  -> smoke
LIGHTEVAL_MAX_SAMPLES=0   -> 不传 --max-samples，完整 benchmark
```

## 8. 本次全量结果

模型：`DALabCommunity/Haidass-143M-v1`，固定 revision
`6f668e57712b756024425dff07c931b55636091f`。

### 8.1 PIQA

```text
samples                 1,838
batch_size              32
acc                     0.6708378672
acc_norm                0.6741022851
LightEval wall          48.165 s
reported eval           24.233 s
end-to-end              72.673 s
```

模型卡 PIQA 为 67.25，本次 `acc_norm=67.41%`，差异约 0.16 个百分点。

### 8.2 HellaSwag

```text
samples                 10,042
batch_size              32
acc                     0.3235411273
acc_norm                0.3799044015
LightEval wall          323.881 s
reported eval           283.620 s
end-to-end              354.044 s
```

模型卡 HellaSwag 为 37.91，本次 `acc_norm=37.990%`，差异约 0.08 个百分点。

结果高度接近模型卡，说明 NPU/Transformers/LightEval 评估链路与发布口径基本一致。

## 9. Bad-case 分析

`--save-details` 生成每样本 Parquet，包含：

- prompt/example；
- choices；
- gold index；
- 每个 continuation 的 log-likelihood；
- input/continuation token IDs；
- `acc` 和 `acc_norm`；
- truncation/padding 元数据。

分析器输出：

```text
BAD_CASES.md      人工阅读的前 50 条 normalized 高置信错误
bad_cases.json    前 100 条 raw/normalized 错误及 normalization 翻转样本
details_*.parquet 全部样本原始记录
```

### 9.1 PIQA bad cases

```text
raw incorrect               605 / 1,838 = 32.9162%
normalized incorrect        599 / 1,838 = 32.5898%
normalization fixed         188
normalization hurt          182
```

### 9.2 HellaSwag bad cases

```text
raw incorrect               6,793 / 10,042 = 67.6459%
normalized incorrect        6,227 / 10,042 = 62.0096%
normalization fixed         1,879
normalization hurt          1,313
```

HellaSwag 的 continuation 长度差异大，raw log-likelihood 强烈偏向短选项。
LightEval 0.9.2 的 `acc_norm` 使用字符长度归一化：

```text
normalized_score = continuation_log_likelihood / len(choice_text)
```

不是 token-length normalization。分析器按 LightEval 源码重建 normalized 预测，
与 details 中 `acc_norm` 的 mismatch 为 0。

建议对 HellaSwag bad cases 重点分组：

1. raw 错、norm 对：典型短答案偏置被修正；
2. raw 对、norm 错：归一化对长短选择产生反向影响；
3. raw/norm 均错且 margin 大：模型语义/常识失败；
4. 所有 scores 接近：模型不确定性高；
5. prompt 或 endings 含清洗噪声：数据质量型 bad case；
6. continuation token/字符长度异常：tokenizer 或文本格式敏感样本。

## 10. 结果目录

server-00：

```text
/home/admin/haidass_eval/results/piqa-full
/home/admin/haidass_eval/results/hellaswag-full
```

每个目录包含：

```text
phase2_summary.json
lighteval.log
lighteval-artifacts/results_*.json
lighteval-artifacts/<timestamp>/details_*.parquet
BAD_CASES.md
bad_cases.json
```

## 11. 迁移能力与步骤

### 11.1 可以迁移的部分

- `haidass_eval/k8s` 清单；
- `phase2/*.py` 和 `run_phase2.sh`；
- `phase2/wheelhouse`；
- `phase2/datasets`；
- 模型目录和 SHA256SUMS；
- 结果与报告。

### 11.2 目标集群要求

- arm64 Ascend 910B/910B3 Worker；
- Driver 与 CANN 8.3.RC1/torch_npu 2.7.1 兼容；
- Ascend device plugin 能分配 `huawei.com/Ascend910`；
- KubeRay 与 Worker Ray 版本均为 2.10.0；
- Worker 能挂载 driver/DCMI；
- Volcano 集成开启时必须走 Volcano 调度；
- Head 与 Worker 网络可互通；
- 至少约 64 GiB Worker 内存，当前请求 32 GiB、limit 64 GiB。

### 11.3 迁移注意事项

1. 不要只复制 RayCluster YAML 而忽略镜像 digest；
2. 不要让 Head/Worker 使用不同 Ray 小版本；
3. 不要在新环境直接升级 torch/torch_npu；
4. 先运行 `npu-image-preflight.yaml`；
5. 先做 BF16 matmul 和 16 样本 smoke；
6. 再做全量 benchmark；
7. 重新计算模型和 benchmark SHA256；
8. 新节点如果能稳定访问 Hub，可关闭 router，但需验证数据 revision 一致。

## 12. 推荐的正式评估 Worker 镜像

当前运行时注入适合验证，但生产建议构建：

```text
110.120.0.3:8889/eval/lighteval-ascend-worker:
ray2.10.0-py310-torch2.7.1-cann8.3-lighteval0.9.2
```

建议镜像包含：

- `demo:v2` 作为严格基线；
- wheelhouse 中 LightEval 纯 Python 包；
- `offline_dataset_router.py`；
- runner 和 bad-case analyzer；
- 不包含模型权重；
- benchmark 数据可放镜像、小型 PVC 或对象存储缓存；
- OCI labels 记录 git commit、LightEval wheel SHA、CANN/torch_npu 版本。

推荐使用 `pip install --no-index --no-deps`，严禁让 pip 自动替换 torch、
Transformers、Accelerate、datasets 和 NumPy。构建后必须重新执行本手册中的
preflight、generation smoke、PIQA 和 HellaSwag 对照。

## 13. 已知限制

- 当前模型自动缓存逻辑只内置 Haidass-143M-v1；
- Worker `emptyDir` 在 Pod 重建后清空；
- Head 结果目录当前由脚本管理，不是对象存储；
- LightEval 0.9.2 会探测镜像中已有 vLLM，但本轮不使用其 vLLM backend；
- `lighteval_sha` 在 wheel 安装模式下显示 `?`，版本由 wheel 文件名和 SHA 固定；
- bad-case 分类是统计与排序工具，不自动判断数据标注是否错误；
- 多卡评估尚未执行；当前每次只使用一张 910B。

## 14. 最终结论

当前链路已经证明：官方 LightEval 0.9.2 的 Accelerate/Transformers backend 可以在
Ascend 910B3 上通过 torch_npu 完成 PIQA 与 HellaSwag 全量评估，结果与模型卡接近。
LightEval 核心没有被修改，主要工程工作集中在 NPU 环境启动、Ray 资源调度、离线
依赖、离线数据传输、结果归集和 bad-case 分析。该方案可以迁移；长期复用时应将
已验证运行时固化为独立评估 Worker 镜像，并继续把模型权重与结果留在外部存储。
