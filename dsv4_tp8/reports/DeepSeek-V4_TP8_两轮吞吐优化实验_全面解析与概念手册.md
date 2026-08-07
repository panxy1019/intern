# DeepSeek-V4 TP8 两轮吞吐优化实验：全面解析与概念手册

> 文档定位：这不是对原实验报告的简单改写，而是一份“**实验结果解析 + vLLM/Ascend 概念教程 + 性能归因指南**”。  
> 目标读者：希望能真正读懂 `C8`、`TP8/EP8`、`max_num_seqs`、`Chunked Prefill`、`FULL_DECODE_ONLY`、`NPUGraph Ex`、`FlashComm1`、`DSA-CP`、Prefix Cache、TTFT/TPOT 等概念，并能够解释为什么某个优化会在某类负载下生效。  
> 实验对象：DeepSeek-V4-Flash-0731-w8a8，vLLM 0.22.1 + vLLM-Ascend 0.22.1rc1，Ascend A3，TP8/EP8。  
> 文档日期：2026-08-07。

---

## 目录

1. [先给出最核心结论](#1-先给出最核心结论)
2. [如何阅读这套实验](#2-如何阅读这套实验)
3. [一次 LLM 请求到底经历了什么](#3-一次-llm-请求到底经历了什么)
4. [C8、C16 到底是什么意思](#4-c8c16-到底是什么意思)
5. [TP8、EP8、DP1 是什么](#5-tp8ep8dp1-是什么)
6. [Prefill、Decode 与 KV Cache](#6-prefilldecode-与-kv-cache)
7. [吞吐与延迟指标完整解释](#7-吞吐与延迟指标完整解释)
8. [调度器参数：max_num_seqs 与 max_num_batched_tokens](#8-调度器参数max_num_seqs-与-max_num_batched_tokens)
9. [Chunked Prefill 与 Async Scheduling](#9-chunked-prefill-与-async-scheduling)
10. [Prefix Cache 为什么能带来 3.86 倍收益](#10-prefix-cache-为什么能带来-386-倍收益)
11. [Graph、FULL_DECODE_ONLY 与 NPUGraph Ex](#11-graphfull_decode_only-与-npugraph-ex)
12. [FlashComm1 是什么](#12-flashcomm1-是什么)
13. [DSA-CP 是什么，为什么长上下文收益巨大](#13-dsa-cp-是什么为什么长上下文收益巨大)
14. [本次配置矩阵如何理解](#14-本次配置矩阵如何理解)
15. [逐类 workload 深入解读](#15-逐类-workload-深入解读)
16. [逐项优化的因果证据强弱](#16-逐项优化的因果证据强弱)
17. [为什么吞吐升高但 TPOT 可能变差](#17-为什么吞吐升高但-tpot-可能变差)
18. [为什么 AICore 降低反而吞吐更高](#18-为什么-aicore-降低反而吞吐更高)
19. [HBM 结果告诉了我们什么](#19-hbm-结果告诉了我们什么)
20. [目前实验中最重要的未决问题](#20-目前实验中最重要的未决问题)
21. [生产配置应该如何分 Profile](#21-生产配置应该如何分-profile)
22. [下一轮实验应怎样设计](#22-下一轮实验应怎样设计)
23. [从 AI Infra / 性能建模视角如何总结](#23-从-ai-infra--性能建模视角如何总结)
24. [概念速查表](#24-概念速查表)
25. [参考资料](#25-参考资料)

---

# 1. 先给出最核心结论

这两轮实验最重要的价值，不是简单得到“某个参数让 DeepSeek-V4 更快”，而是识别出了**不同 workload 下不同的主要瓶颈**。

可以把结果概括成下面这条链：

```text
并发增大
  ↓
原始 max_num_seqs=4 先形成调度容量墙
  ↓
扩大 sequence slot / token budget
  ↓
调度瓶颈减轻，设备能够同时推进更多请求
  ↓
新的瓶颈转移到 attention、MoE 通信和长上下文处理
  ↓
FlashComm1 / DSA-CP 开始体现价值
  ↓
如果请求存在大量重复前缀
  ↓
重复 Prefill 又成为主要浪费
  ↓
Prefix Cache 产生数量级收益
```

因此，最终结论不是：

> 所有优化开关都打开 = 最优。

而是：

> **workload 决定瓶颈，瓶颈决定应该打开什么优化。**

现有结果中：

- `max_num_seqs: 4 → 8` 是非常明确的调度容量收益；
- DSA-CP 是目前对长上下文最可信的底层优化之一；
- Prefix Cache 对“共享前缀”场景非常强，尤其适合 OpenCode/Agent/多轮对话，但不能把它的收益外推到无共享前缀流量；
- `optimized` 是高吞吐候选，不是所有 workload 的最优解；
- NPUGraph Ex 的真正净收益目前仍未被严格隔离；
- `batch8192` 有明显潜力，但重复观测方差过大，仍需统计闭环。

---

# 2. 如何阅读这套实验

## 2.1 实验固定条件

本次实验保持以下主要条件不变：

```text
模型：DeepSeek-V4-Flash-0731-w8a8
运行时：vLLM 0.22.1 + vLLM-Ascend 0.22.1rc1
并行：TP=8，DP=1，Expert Parallel=on
设备：a3-server-00，容器可见 8 个逻辑 NPU
最大上下文：1,048,576 token
KV block size：32
gpu_memory_utilization：0.88
Chunked Prefill：on
Async Scheduling：on
temperature：0
固定随机种子
Benchmark：闭环固定并发
```

这种设计的好处是：模型权重、设备、并行拓扑和大部分运行时条件保持稳定，能够更清楚地观察调度、缓存、图执行和通信优化的影响。

---

## 2.2 什么叫“单变量实验”

例如：

```text
baseline:
max_num_seqs = 4

seq8:
max_num_seqs = 8
```

如果除此之外其他配置都相同，那么：

```text
baseline vs seq8
```

就是比较干净的单变量 A/B。

但下面这种就不是：

```text
baseline:
seq4 / batch4096 / prefix off

prefix:
seq16 / batch10240 / prefix on
```

这里同时改变：

- sequence capacity；
- token budget；
- Prefix Cache。

所以即使结果从 36.75 提升到 141.76 tok/s，也不能说：

> Prefix Cache 单独带来了 285.7%。

准确说法应该是：

> 带 Prefix Cache 的该配置相对原 baseline 提升 285.7%；Prefix Cache 很可能是主要原因，但其纯因果增益尚需严格同底座 A/B。

这一区别非常重要。

---

# 3. 一次 LLM 请求到底经历了什么

理解所有优化前，先理解一次请求。

假设用户发送：

```text
Prompt: 16,000 tokens
要求生成: 512 tokens
```

大体经历：

```mermaid
flowchart LR
    A[请求到达] --> B[排队 / Admission]
    B --> C[Prefill]
    C --> D[建立 KV Cache]
    D --> E[生成第一个 token]
    E --> F[Decode step 1]
    F --> G[Decode step 2]
    G --> H[...]
    H --> I[生成结束]
```

从客户端看：

```text
请求提交
 |---------------- TTFT ----------------> 第一个 token
 |------------------------------------------------ E2E ------------------------------------------------> 最后一个 token
                                         |--TPOT--|--TPOT--|--TPOT--|
```

性能优化实际上在优化不同阶段：

| 优化 | 主要作用阶段 |
|---|---|
| `max_num_seqs` | 调度 / batching |
| `max_num_batched_tokens` | Prefill + Decode 调度预算 |
| Chunked Prefill | Prefill 与 Decode 混排 |
| Async Scheduling | CPU 调度与 NPU 计算 overlap |
| Prefix Cache | Prefill |
| FULL_DECODE_ONLY | Decode |
| NPUGraph Ex | 主要配合 graph 路径降低 kernel/dispatch 开销 |
| FlashComm1 | 分布式通信路径 |
| DSA-CP | DeepSeek DSA 长上下文 attention |
| EP | MoE expert 分布与执行 |

所以不存在“一个开关同时完美解决所有问题”。

---

# 4. C8、C16 到底是什么意思

这是整个实验里最容易混淆的概念之一。

## 4.1 C = Concurrency

例如：

```text
decode_c8
balanced_c16
long128k_c2
```

其中：

```text
C8  = benchmark 客户端保持 8 个并发请求
C16 = 保持 16 个并发请求
C2  = 保持 2 个并发请求
```

本实验使用的是**闭环固定并发（closed-loop concurrency）**。

闭环的含义是：

```text
始终保持 C 个请求在系统中
一个完成
   ↓
客户端立刻补一个新请求
   ↓
继续维持 C 个 in-flight requests
```

例如 C8：

```text
Req1 ────────────────┐
Req2 ─────────────┐  │
Req3 ───────────┐ │  │
...
Req8 ─────────┐ │ │  │
             完成
               ↓
             新 Req9
```

---

## 4.2 C8 不等于 max_num_seqs=8

这是必须明确区分的两个参数。

### C8

是**客户端施加给服务的并发压力**。

### `max_num_seqs=4`

是**服务器调度器一次 iteration 最多允许处理多少条 sequence**。

因此可以出现：

```text
客户端 C8
服务器 max_num_seqs=4
```

此时最多只有一部分请求同时进入实际 engine batch，其余请求需要等待。

近似理解：

```text
实际可调度 sequence 数
<= min(
    客户端并发 C,
    max_num_seqs,
    KV/内存约束,
    scheduler token budget,
    其他运行时约束
)
```

这就是为什么 C8/C16 baseline 的 TTFT 会非常高。

---

## 4.3 为什么 baseline C16 的吞吐没比 C8 高多少

Decode：

```text
baseline C8  = 103.48 output tok/s
baseline C16 = 104.43 output tok/s
```

C8 → C16，并发翻倍，但吞吐几乎没涨。

同时 TTFT P50：

```text
20.42 s → 58.28 s
```

这基本说明：

```text
系统已经达到一个服务容量墙
```

增加请求只是在增加：

```text
waiting / queuing
```

而不是增加：

```text
有效并行工作
```

因此 C8/C16 是外部负载，`max_num_seqs` 是内部处理能力，两者共同决定系统状态。

---

# 5. TP8、EP8、DP1 是什么

## 5.1 TP：Tensor Parallelism

TP8：

```text
Tensor Parallel Size = 8
```

表示一个模型计算被 8 个 rank 共同执行。

可以粗略理解为：

```text
一个大的矩阵计算
        ↓
在张量维度切成 8 份
        ↓
Rank0 ... Rank7 分别计算
        ↓
通过 Collective Communication 合并结果
```

TP 的好处：

- 单卡放不下的模型可以分布到多卡；
- 大矩阵计算可并行。

代价：

- AllReduce / AllGather / ReduceScatter 等通信；
- TP 越大，通信优化越重要。

因此后面 FlashComm1、Reduce Sample 等优化都与 TP 有很强关系。

---

## 5.2 EP：Expert Parallelism

DeepSeek-V4 是 MoE 模型。

MoE 可以理解为：

```text
输入 token
  ↓
Router / Gate
  ↓
选择部分 Expert
  ↓
只执行被选中的 Expert
```

如果有很多专家，没有必要让每个 NPU 都保存/执行所有专家。

EP8 表示专家分散在 8 个 expert-parallel rank 上。

概念上：

```text
Experts
 ├── 一部分放 Rank0
 ├── 一部分放 Rank1
 ├── ...
 └── 一部分放 Rank7
```

token 经过 router 后：

```text
token
 ↓
决定它需要哪些 expert
 ↓
如果 expert 不在当前 rank
 ↓
产生 token dispatch / all-to-all 类通信
 ↓
expert 计算
 ↓
combine
```

因此 MoE 推理不仅是“算矩阵”，还有：

```text
路由
+ dispatch
+ expert 计算
+ combine
```

这也是通信优化非常重要的原因。

---

## 5.3 DP：Data Parallelism

本实验：

```text
DP = 1
```

表示没有复制多份完整 serving replica 来处理独立请求。

当前主要拓扑可以理解为：

```text
一个模型实例
 ├── TP8
 └── EP8
```

不是：

```text
多个 DP replica
```

因此实验主要研究的是**单实例内部吞吐**。

---

# 6. Prefill、Decode 与 KV Cache

## 6.1 Prefill 是什么

Prompt：

```text
token1 token2 token3 ... token32000
```

第一次处理整个 Prompt 时，模型需要计算这些 token 的表示和 attention，并建立后续 Decode 需要的 KV Cache。

这叫：

```text
Prefill
```

特点：

- 一次可以处理很多 token；
- 计算密集；
- Prompt 越长，Prefill 越重；
- 与 TTFT 高度相关。

---

## 6.2 Decode 是什么

Prefill 后开始生成：

```text
第 1 个输出 token
第 2 个输出 token
第 3 个输出 token
...
```

标准自回归生成每一步通常只产生下一个 token。

```text
Decode step t
  ↓
输入当前 token + 历史 KV
  ↓
Attention
  ↓
MoE
  ↓
logits
  ↓
sample
  ↓
token t+1
```

因此 Decode 是大量重复的小 step。

这就是 Graph 很适合 Decode 的原因：

```text
小而重复的计算流程
```

特别容易通过 capture/replay 降低 CPU dispatch 和 kernel launch overhead。

---

## 6.3 KV Cache 是什么

如果每生成一个 token 都重新计算之前所有 token：

```text
成本非常高
```

所以 Transformer serving 保存历史 token 对应的 Key / Value：

```text
KV Cache
```

下一步只需：

```text
新 query
+
历史 KV
```

而不用重新算整个历史。

上下文越长：

```text
KV Cache 越大
```

并发越高：

```text
多个请求同时占 KV
```

所以：

```text
长上下文 × 高并发
```

是 serving 最危险的内存组合之一。

---

## 6.4 block_size=32 是什么

vLLM 不是把 KV Cache 当一个无结构的大数组管理，而是按 block/page 管理。

本实验：

```text
block_size = 32
```

可以概念化理解为：

```text
一个 KV block 对应 32 个 token 的管理粒度
```

这样更容易：

- 分配；
- 回收；
- Prefix Cache；
- Paged KV 管理。

注意：DeepSeek V4 是更复杂的混合/专用 KV 路径，底层真实布局可能比这个教学模型复杂；但从 vLLM 调度和缓存管理角度，“block_size 是 KV 分页粒度”这一理解是正确的。

---

# 7. 吞吐与延迟指标完整解释

## 7.1 output tok/s

定义：

```text
所有成功请求生成的 output tokens 总数
------------------------------------------------
              benchmark 总时间
```

vLLM benchmark 中本质上是：

```text
output_throughput = total_output_tokens / duration
```

它回答：

> 整台服务每秒生成多少个 token？

这是衡量**生成吞吐能力**最重要的指标之一。

---

## 7.2 total tok/s

定义：

```text
input tokens + output tokens
-----------------------------
         总时间
```

所以长 Prompt 场景可能出现：

```text
output tok/s 很低
total tok/s 很高
```

例如 baseline 128K：

```text
output tok/s = 2.77
total tok/s  = 5681.32
```

这并不意味着模型每秒生成 5681 个 token。

它意味着大部分 token throughput 来自：

```text
Prefill 输入 token
```

因此报告里正确地强调：

> 长输入场景 total tok/s 很高，不等价于生成吞吐很高。

---

## 7.3 TTFT：Time To First Token

TTFT：

```text
请求发出
  ↓
等待
  ↓
调度
  ↓
Prefill
  ↓
第一步 Decode
  ↓
收到第一个 token
```

TTFT 包含的不只是 Prefill。

非常重要：

```text
TTFT = 排队时间 + Prefill + 首 token 产生/传输等
```

所以 baseline Decode C16 TTFT P50 = 58.28 s，不能简单说：

> 模型 Prefill 花了 58 秒。

因为很大一部分可能是：

```text
max_num_seqs=4 导致的排队
```

---

## 7.4 TPOT：Time Per Output Token

vLLM benchmark 的典型计算是：

```text
TPOT = (E2E - TTFT) / (output_tokens - 1)
```

它近似回答：

> 第一个 token 出来以后，平均每生成下一个 token 需要多久？

单位：

```text
ms/token
```

越小越好。

粗略转换成单 sequence token rate：

```text
tokens/s ≈ 1000 / TPOT_ms
```

例如：

```text
TPOT = 40 ms
≈ 25 token/s
```

但注意这只是单请求平均 cadence，不是整个服务器 aggregate throughput。

---

## 7.5 ITL：Inter-Token Latency

ITL 是：

```text
相邻两个输出 token 的真实时间间隔
```

TPOT 是一个请求的平均生成速度；

ITL 可以暴露：

```text
突然的 latency spike
```

例如长 Prefill chunk 插入 Decode 时可能让某一步 ITL 突然变大。

本报告当前主要保存 TPOT；以后如果研究 tail jitter，ITL 很有价值。

---

## 7.6 E2E：End-to-End Latency

```text
E2E = 请求发送 → 最后一个 token 收完
```

近似：

```text
E2E ≈ TTFT + Decode 时间
```

它最接近用户最终感知的“这次请求多久完成”。

---

## 7.7 P50 / P95 / P99

例如：

```text
TTFT = 2.0 / 5.3 / 5.3
```

代表：

```text
P50 = 50% 请求 TTFT ≤ 2.0 s
P95 = 95% 请求 TTFT ≤ 5.3 s
P99 = 99% 请求 TTFT ≤ 5.3 s
```

P50：

```text
典型用户
```

P95/P99：

```text
尾延迟 / 最倒霉的一批用户
```

生产系统经常更看重 P95/P99，而不是平均值。

---

## 7.8 Goodput

Throughput 只问：

> 做完多少请求/多少 token？

Goodput 则问：

> 在 SLO 范围内完成了多少？

例如规定：

```text
TTFT P/request < 2 s
TPOT < 80 ms
```

只有同时满足的请求才算 good request。

因此：

```text
goodput = 满足 SLO 的完成请求 / 秒
```

本轮没有预先定义 SLO，所以报告没有“补造 goodput”，这是正确做法。

---

# 8. 调度器参数：max_num_seqs 与 max_num_batched_tokens

这两个参数是本次最核心的概念。

---

## 8.1 max_num_seqs

官方定义：

> 单次 scheduler iteration 可以处理的最大 sequence 数。

例如：

```text
max_num_seqs = 4
```

即使外面来了 C16：

```text
16 个请求
```

同一 iteration 内实际活跃处理 sequence 仍受到 4 的限制。

概念图：

```text
C16 workload

Req1 ─┐
Req2 ─┤
Req3 ─┤ → running / scheduled
Req4 ─┘

Req5  ┐
Req6  │
...   │ → waiting
Req16 ┘
```

所以 `max_num_seqs` 很像：

```text
“同时允许多少条 sequence 上计算流水线”
```

但它不是严格的线程数，也不是独立进程数。

---

## 8.2 max_num_batched_tokens

官方定义：

> 单次 iteration 最大可以处理多少 token。

本实验 baseline：

```text
max_num_batched_tokens = 4096
```

可以粗略写成约束：

```text
Σ 本 iteration 被调度的 token 数 ≤ 4096
```

假设当前有：

```text
Decode 请求 8 条
+
一个长 Prefill
```

Decode 每条通常只需要推进少量新 token，剩余 budget 可以给 Prefill chunk。

例如教学化理解：

```text
budget = 4096

Decode:
8 sequences × 1 token ≈ 8

剩余 Prefill budget:
≈ 4088 tokens
```

实际 DeepSeek V4、调度器和特殊 attention 路径会更复杂，但这个预算模型非常适合理解参数意义。

---

## 8.3 为什么两个参数必须一起看

只提高：

```text
max_num_seqs
```

会让更多 sequence 进入 batch。

但如果：

```text
max_num_batched_tokens
```

仍然太小，就可能出现：

```text
请求更多了
但每轮 token budget 不够
```

反过来，只提高 token budget，但 seq slot 太少：

```text
也无法把更多 Decode 请求塞进 batch
```

所以两者共同决定：

```text
scheduler batch 的“宽度”和“token 容量”
```

可以理解成：

```text
max_num_seqs           = 最多装多少条请求
max_num_batched_tokens = 一轮最多处理多少 token
```

---

# 9. Chunked Prefill 与 Async Scheduling

## 9.1 为什么需要 Chunked Prefill

假设：

```text
Prompt = 32K
max_num_batched_tokens = 4096
```

如果不 chunk，32K Prefill 无法直接塞进一个 4096 budget 的 iteration。

Chunked Prefill 会拆成：

```text
Chunk 1: ~4096
Chunk 2: ~4096
...
```

更重要的是，Chunk 之间可以插 Decode：

```text
Prefill chunk
↓
Decode
↓
Prefill chunk
↓
Decode
```

避免一个超长 Prompt 独占 engine 很久。

---

## 9.2 Chunk 越大越好吗

不是。

大 chunk：

```text
优点：
Prefill 效率高
scheduler 次数少

缺点：
一次占用 engine 时间长
Decode 更容易被阻塞
ITL / TPOT tail 可能变差
```

小 chunk：

```text
优点：
更容易插入 Decode
交互 latency 好

缺点：
调度次数多
kernel / scheduler overhead 增加
总吞吐可能下降
```

所以：

```text
4096 → 8192 → 10240
```

不是简单越大越好。

本实验 seq16/batch10240 出现较高 TPOT，就是这种 trade-off 的一个信号。

---

## 9.3 Async Scheduling

同步模式可以概念化为：

```text
CPU 做 scheduler
↓
NPU 执行
↓
CPU 再调度
↓
NPU 再执行
```

可能存在 CPU/NPU 串行气泡。

Async Scheduling 目标：

```text
NPU 正在计算 step t
       ||
CPU 同时准备 step t+1
```

即：

```text
CPU scheduling
      ↘ overlap
       NPU compute
```

这样减少 host-side 调度成为瓶颈的概率。

本实验所有 case 都保持 Async Scheduling 开启，因此没有对它做 on/off 因果分析。

---

# 10. Prefix Cache 为什么能带来 3.86 倍收益

## 10.1 核心思想

假设两个请求：

```text
Request A:
[共同 16K prefix] + Question A

Request B:
[共同 16K prefix] + Question B
```

没有 Prefix Cache：

```text
A: 重新计算 16K prefix
B: 又重新计算 16K prefix
```

有 Prefix Cache：

```text
A:
计算 16K
↓
保存对应 KV block

B:
发现 prefix hash 命中
↓
直接复用已有 KV
↓
只计算新的 suffix
```

因此大量 Prefill 被省掉。

---

## 10.2 vLLM 的基本机制

vLLM Automatic Prefix Caching 使用 block hash。

概念：

```text
Block1 hash = token 内容
Block2 hash = parent hash + 本 block token
Block3 hash = parent hash + 本 block token
...
```

如果新请求有完全相同的 prefix block：

```text
hash match
↓
KV block reuse
```

Prefix Cache 主要减少的是：

```text
重复 Prefill 计算
```

不会让同一个已经进入 Decode 的 token magically 计算得更快。

---

## 10.3 为什么 output tok/s 也会提高

很多人会问：

> Prefix Cache 不是只降低 TTFT 吗？为什么 output throughput 也提高？

因为 Prefill 和 Decode 共用服务器资源。

没有 cache：

```text
大量 NPU 时间 / token budget
用于重复 Prefill
```

启用 cache：

```text
重复 Prefill 消失
↓
更多 scheduler budget 和设备时间
可以留给 Decode
↓
单位墙钟时间生成更多 output token
```

所以 aggregate output tok/s 会显著上升。

---

## 10.4 本实验数据

```text
baseline shared16k C8:
36.75 output tok/s
TTFT P95 = 21.28 s

prefix shared16k C8:
141.76 output tok/s
TTFT P95 = 3.83 s
```

配置级提升：

```text
141.76 / 36.75 ≈ 3.86×
```

即约：

```text
+285.7%
```

这是非常大的收益。

---

## 10.5 为什么特别适合 OpenCode / Agent

代码 Agent 请求通常不是完全独立的。

可能反复包含：

```text
system prompt
tool definitions
repository rules
AGENTS.md
历史对话
项目上下文
大量相同代码片段
```

后续请求只增加少量新内容。

这正是 Prefix Cache 最理想的 workload。

---

## 10.6 为什么不能外推

如果每个请求都是：

```text
完全不同的 Prompt
```

则：

```text
cache hit ≈ 0
```

此时 Prefix Cache 不会产生 3.86× 的收益。

因此生产上真正应该关注：

```text
Prefix Cache Hit Ratio
```

而不是简单：

```text
Prefix Cache ON/OFF
```

---

# 11. Graph、FULL_DECODE_ONLY 与 NPUGraph Ex

这是本实验最容易产生误解的一组概念。

---

## 11.1 Eager execution 是什么

Eager 可以简单理解为：

```text
每一个 step
CPU 按 Python/框架执行流
↓
逐个发起算子
↓
NPU 执行 kernel
```

重复 Decode 中有很多：

```text
Python / dispatch / kernel launch
```

开销。

---

## 11.2 Graph execution 是什么

Decode 结构高度重复：

```text
step 1:
Attention → MoE → Norm → LM Head ...

step 2:
Attention → MoE → Norm → LM Head ...

step 3:
Attention → MoE → Norm → LM Head ...
```

如果 shape 合适，可以把整条执行路径：

```text
capture
```

然后后续：

```text
replay
```

减少 host dispatch。

---

## 11.3 FULL_DECODE_ONLY 是什么意思

配置：

```json
{"cudagraph_mode":"FULL_DECODE_ONLY"}
```

在 Ascend 当前 graph 路径中，意思可以理解为：

> **重点让纯 Decode batch 使用 full ACLGraph capture/replay，而不是把整个 Prefill + Decode 的所有动态场景都强制 full graph 化。**

为什么这么做？

Prefill 的 shape 很动态：

```text
128 tokens
4096 tokens
32K chunk
不同 batch
```

而 Decode 更规则：

```text
每个 active sequence 每步推进 token
```

因此 Decode 更适合 full graph。

官方 DeepSeek-V4 文档也明确把 `FULL_DECODE_ONLY` 描述为：

```text
在 decode 阶段启用完整 ACL 图执行，以降低调度/执行开销
```

---

## 11.4 ACLGraph 与 NPUGraph Ex 不是同一个东西

在 Ascend graph 路径里可以分成两个层次：

### NPUGraph Ex

偏**编译期 FX graph 优化**：

```text
FX graph
↓
算子融合 / 图优化
↓
例如多个小 op 尽量融合
```

目标：

```text
减少 kernel 数
减少 launch overhead
```

### ACLGraph

偏**运行时 capture/replay**：

```text
优化后的计算图
↓
捕获
↓
后续直接 replay
```

因此可以理解为：

```text
NPUGraph Ex = 先把图改得更适合跑
ACLGraph    = 再把它捕获起来重复执行
```

当前 vLLM-Ascend 文档说明，在 `FULL` / `FULL_DECODE_ONLY` 模式下 NPUGraph Ex 默认启用。

---

## 11.5 cudagraph_capture_sizes 是什么

Graph 往往不是“任意 shape 都能 replay”。

例如可能捕获：

```text
batch size = 1
batch size = 2
batch size = 4
```

如果运行时正好是：

```text
running sequences = 4
```

可以命中 graph。

如果运行时是：

```text
running sequences = 7
```

可能需要：

- padding；
- 匹配另一个 capture size；
- fallback；
- 或走其他 graph/eager 路径。

所以：

```text
capture sizes
```

必须和真实 scheduler batch size 分布匹配。

---

## 11.6 为什么本实验 graph 结论还不能下

结果：

```text
baseline decode C8     = 103.48
graph_off decode C8    = 188.49
```

如果只看数字，会误以为：

> Graph 让性能下降了 45%。

但两组配置还同时改变：

```text
baseline:
seq4 / batch4096

graph_off:
seq16 / batch10240
```

所以不是单变量。

目前只能提出假设：

```text
真实 batch shape
可能和 graph capture set 不匹配
```

或者：

```text
动态 MoE / DSA 路径导致 graph fallback
```

但不能定论。

下一轮必须严格：

```text
所有参数完全相同
只改 NPUGraph Ex on/off
```

并采：

```text
graph hit
graph replay
fallback
running batch size histogram
```

---

# 12. FlashComm1 是什么

## 12.1 为什么 TP8 需要大量通信

TP8 把计算分布到 8 个 rank。

很多层之间需要：

```text
AllReduce
AllGather
ReduceScatter
```

如果每一层：

```text
计算 1 ms
通信 1 ms
```

那总时间并不只是算力问题。

因此：

```text
更快 kernel
```

并不一定带来更高 throughput，因为可能已经变成：

```text
communication-bound
```

---

## 12.2 FlashComm1 的核心思想

vLLM-Ascend 官方把 Flash Comm V1 描述为 NPU 上针对 Sequence Parallelism 的增强通信优化。

两个特别关键的优化方向：

### MLA 路径

传统可能较早 AllGather。

FlashComm1 尽量：

```text
先本地做 QKV projection
↓
再做 AllGather
```

这样通信的数据量可能更小。

### MoE 路径

传统：

```text
较早 AllGather
↓
Gating
↓
Quant
```

FlashComm1 尽量推迟到：

```text
Gating + DynamicQuant
之后
```

再进行必要通信。

核心原则就是：

> **能晚通信就晚通信，先在本地把数据变小/筛掉无用部分。**

---

## 12.3 为什么它不是“开了就一定很快”

如果 workload 本身计算很重，而通信占比很小：

```text
优化通信收益有限
```

如果并发很低：

```text
可能也无法充分体现 communication overlap / sequence parallel 的收益
```

此外 FlashComm1 会改变 sequence-parallel 相关 shape 约束，所以此前实验中 `TP8 + max_num_seqs=1` 曾经遇到 graph capture size 与 TP size 不匹配的问题。

因此它属于：

```text
分布式执行优化
```

不是纯粹的 scheduler 开关。

---

## 12.4 本实验 FlashComm1 的直接证据

32K C8：

```text
batch8192  = 27.01
flashcomm  = 28.38
```

表面约：

```text
+5.1%
```

但是注意两者底座并不完全等同于“只改变 FlashComm1”的理想严格设计，因此当前更适合说：

> FlashComm1 本轮表现为温和正收益，但其独立贡献还没有像 DSA-CP 那么清楚。

---

# 13. DSA-CP 是什么，为什么长上下文收益巨大

这是当前最值得深入理解的概念。

---

## 13.1 DSA 是什么

DSA 在这里指 DeepSeek 系列的 Sparse Attention 路径。

概念上，传统 full attention：

```text
当前 Query
↓
看全部历史 KV
```

上下文越长，attention 工作量越重。

Sparse Attention 的思想：

```text
先通过 indexer / selector
找出更相关的一部分历史位置
↓
只对选中的部分做主要 attention
```

在 DeepSeek DSA 结构中，官方 vLLM 模型文档描述了类似：

```text
MLA
+
Lightning Indexer
+
top-k token selection
+
sparse attention
```

DeepSeek V4 的 Ascend 实现也包含专用 DSA attention backend。

---

## 13.2 CP：Context Parallel

Context Parallel 的基本想法：

```text
一个超长 sequence
↓
沿 sequence/context 维度拆给多个设备
↓
每个设备处理一部分上下文相关工作
↓
再合并结果
```

与 TP 按张量维度拆模型不同：

```text
TP：主要拆 tensor / layer 内矩阵
CP：主要拆 sequence/context 相关工作
```

---

## 13.3 DSA-CP 不是普通 DCP

vLLM-Ascend 官方文档明确区分：

```text
Decode Context Parallel (DCP)
```

与：

```text
DSA-CP
```

DSA-CP 是针对 DeepSeek V4 等 DSA architecture 的专用 sparse-attention CP 优化。

配置：

```json
"enable_dsa_cp": true
```

并且当前官方配置说明：

```text
DSA-CP 依赖 FlashComm1
```

所以需要：

```json
"enable_flashcomm1": true,
"enable_dsa_cp": true
```

不能只开 DSA-CP。

---

## 13.4 为什么 128K 时特别有效

短上下文：

```text
sequence work 较少
```

CP 自己的：

```text
通信
同步
metadata
index handling
```

会占较明显比例。

长上下文：

```text
128K
```

可并行化的 attention/index 相关工作明显增加。

于是：

```text
可并行工作增长
      ↓
固定通信/协调成本被摊薄
      ↓
CP 更有价值
```

这就是一种典型的：

```text
parallel efficiency 随问题规模增大而提高
```

---

## 13.5 本实验最干净的 DSA-CP 证据

32K C8：

```text
FlashComm1:
28.38 output tok/s

FlashComm1 + DSA-CP:
43.78 output tok/s
```

两者在配置矩阵中最接近：

```text
只增加 DSA-CP
```

提升约：

```text
+54.3%
```

而且延迟同时改善：

```text
TTFT P95:
28.90 s → 15.72 s

TPOT P95:
243.5 ms → 152.1 ms
```

这比“只看吞吐提高”更有说服力。

---

## 13.6 128K 数据怎么理解

```text
baseline:
2.77 output tok/s

DSA-CP:
7.18 output tok/s
```

按表格中四舍五入后的数值直接计算：

```text
约 +159.2%
```

原报告写 `+158.9%`，很可能是基于未四舍五入的原始 `result.json` 计算，因此两者并不矛盾。

但：

```text
baseline → dsa_cp
```

并不是严格单变量，因为 DSA 配置还包含更大的 scheduler 配置和 FlashComm1。

所以严谨结论是：

> 128K 场景中，含 DSA-CP 的配置比原始 baseline 快约 2.6 倍；结合 32K 上较干净的 FlashComm→DSA A/B，可以较强地判断 DSA-CP 是长上下文收益的核心来源。

---

## 13.7 为什么 optimized 128K 只比 DSA-CP 高一点

```text
DSA-CP:
7.18

optimized:
7.33
```

仅约：

```text
+2.1%
```

这说明在无共享前缀的 128K workload 上：

```text
DSA-CP 已经解决了主要瓶颈
```

继续叠加：

```text
Prefix Cache
其他优化
```

已经没有大量剩余空间。

这是非常重要的“瓶颈归因”证据。

---

# 14. 本次配置矩阵如何理解

| 变体 | seq | batch tokens | Prefix | Graph/NPUGraph | FC1 | DSA-CP | 主要想回答的问题 |
|---|---:|---:|---|---|---|---|---|
| baseline | 4 | 4096 | off | on | off | off | 原始性能 |
| seq8 | 8 | 4096 | off | on | off | off | sequence slot 是否是瓶颈 |
| batch8192 | 8 | 8192 | off | on | off | off | token budget 是否不足 |
| batch10240 | 16 | 10240 | off | on | off | off | 更大的调度容量 |
| prefix | 16 | 10240 | on | on | off | off | 共享前缀复用潜力 |
| graph_off | 16 | 10240 | off | off | off | off | Graph 路径影响（但与 baseline 不可直接单因果比较） |
| flashcomm | 16 | 10240 | off | on | on | off | 通信优化 |
| dsa_cp | 16 | 10240 | off | on | on | on | DSA 长上下文并行 |
| optimized | 16 | 10240 | on | on | on | on | 组合候选 |

注意一个实验学上的重要问题：

```text
配置矩阵是“优化演进树”
```

而不是每一行都能和 baseline 做严格单变量归因。

真正适合严格 A/B 的比较关系是：

```text
baseline → seq8
```

以及较接近：

```text
flashcomm → dsa_cp
```

而：

```text
baseline → optimized
```

只能回答：

> 最终组合配置比原始配置快多少？

不能回答：

> 其中每一个开关分别贡献多少？

---

# 15. 逐类 workload 深入解读

> 原始实验报告没有给出 `decode`、`balanced` 等 workload 的精确输入/输出 token 配比，因此本文不擅自补造具体长度。下面只基于 workload 名称和已给结果解释其性能特征。

---

## 15.1 Decode-heavy

### C8

```text
baseline:
103.48 tok/s
TTFT P50 = 20.42 s
TPOT P50 = 37.4 ms

optimized:
156.18 tok/s
TTFT P50 = 0.75 s
TPOT P50 = 47.5 ms
```

最值得注意：

```text
TTFT 大幅下降
```

但：

```text
TPOT 变差
```

说明优化后的调度器让更多请求更早进入 service，但同时更多 active sequences 分享计算资源。

这不是失败，而是：

```text
queueing latency ↓↓↓
per-sequence service cadence 略慢
aggregate throughput ↑
```

---

## 15.2 Decode C16

```text
baseline = 104.43
optimized = 275.84
```

提升：

```text
+164.1%
```

TTFT P50：

```text
58.28 s → 0.82 s
```

这是非常强的“容量墙被打开”的证据。

但 TPOT：

```text
37.1 ms → 51.9 ms
```

再次说明：

> 高吞吐配置并不是让单条 sequence 每个 token 都更快，而是让服务器同时推进更多 sequence。

---

## 15.3 Balanced C8

```text
baseline  = 73.03
seq8      = 99.21
batch8192 = 146.65
```

`max_num_seqs: 4 → 8`：

```text
+35.8%
```

这是很干净的 scheduler slot 证据。

`seq8 → batch8192`：

```text
约 +47.8%
```

表面说明增加 token budget 也非常有效。

但是辅助复验只有：

```text
83.45 tok/s
```

所以 `146.65` 不能直接当稳定生产容量。

---

## 15.4 Balanced C16

```text
baseline       = 83.59
batch10240     = 111.54
optimized      = 200.23
```

batch10240 相对 baseline：

```text
+33.4%
```

optimized 相对 baseline：

```text
+139.5%
```

但 batch10240：

```text
TPOT P95 = 150.2 ms
```

非常高。

这说明单纯扩大：

```text
seq + token budget
```

会产生更大的 iteration / contention 成本。

后续 FlashComm + DSA 等优化把新的通信/attention 瓶颈又往后推，才让 aggregate throughput 上到 200 tok/s。

---

## 15.5 Prefill 32K C8

```text
baseline    = 22.45
batch8192   = 27.01
flashcomm   = 28.38
dsa_cp      = 43.78
optimized   = 50.43
```

这是很漂亮的一条“优化阶梯”。

可以理解成：

```text
先扩大 scheduler budget
        ↓
解决部分 Prefill 调度限制

再通信优化
        ↓
小幅收益

再 DSA-CP
        ↓
长 sequence attention 并行
        ↓
大幅收益

再组合
        ↓
继续小幅增加
```

其中最明显跳跃：

```text
FlashComm 28.38
→ DSA-CP 43.78
```

约 +54.3%。

---

## 15.6 Long 128K C2

```text
baseline  = 2.77
DSA-CP    = 7.18
optimized = 7.33
```

这组结果揭示：

```text
上下文达到 128K 后
主要瓶颈已经不是简单 scheduler slot
而是长序列 attention/通信路径
```

DSA-CP 一项已经吃掉绝大多数优化空间。

因此：

```text
Long Context Profile
```

应该重点围绕 DSA-CP，而不是一味继续增大 `max_num_seqs`。

---

## 15.7 Shared 16K Prefix C8

```text
baseline  = 36.75
prefix    = 141.76
optimized = 120.88
```

Prefix 配置相对 baseline：

```text
+285.7%
```

但更有意思的是：

```text
prefix only > optimized
```

optimized 反而比 prefix 低：

```text
约 -14.7%
```

这证明：

> 优化不是简单的线性加法。

当 Prefix Cache 已经消掉主要 Prefill：

```text
DSA-CP / FlashComm1 等针对长 Prefill/communication 的额外收益变小
```

而它们自身：

```text
同步
通信
metadata
stream
graph shape
```

开销仍然存在。

因此：

```text
全部开启
```

可能比：

```text
只开启最匹配 workload 的功能
```

更慢。

---

# 16. 逐项优化的因果证据强弱

| 优化 | 当前证据 | 证据评级 | 原因 |
|---|---|---|---|
| `max_num_seqs 4→8` | balanced C8 73.03→99.21 | **强** | 基本是单变量 |
| batch 4096→8192 | 99.21→146.65 | 中 | 本轮高收益但复验波动巨大 |
| seq16/batch10240 | baseline C16→111.54 | 中 | 确有容量提升，但 latency trade-off 明显 |
| Prefix Cache | shared16K 36.75→141.76 | 中强（场景相关） | 机制与结果高度一致，但 baseline 还同时变了 scheduler |
| FlashComm1 | 32K 27.01→28.38 | 中低 | 独立提升不大，仍需严格同底座复验 |
| DSA-CP | 32K 28.38→43.78 | **很强** | 最接近严格单变量，吞吐与延迟同时改善 |
| DSA-CP 长上下文 | 128K 2.77→7.18 | 强但非纯单变量 | 与 32K 的因果证据互相支持 |
| NPUGraph Ex | graph_off 出现反常高值 | **未决** | 比较受到 seq/batch 混杂 |
| optimized | 多 workload 高吞吐 | 强（配置整体） | 能证明组合候选快，但不能拆分各开关贡献 |

---

# 17. 为什么吞吐升高但 TPOT 可能变差

这是 serving 优化最重要的思想之一。

假设一张 NPU 每次只服务 1 条 sequence：

```text
单请求非常快
TPOT = 30 ms
```

但外面有 16 个请求：

```text
1 个跑
15 个等
```

服务器总吞吐不一定高。

如果改成一次处理很多 sequence：

```text
Req1 Req2 Req3 ... Req16
       ↓
更大 batch
```

每个 step 可能从：

```text
30 ms → 50 ms
```

也就是单条 sequence token cadence 变慢。

但一次 step 同时推进更多请求：

```text
总 output tok/s 反而大幅升高
```

所以：

```text
TPOT ↑
不一定代表 aggregate throughput ↓
```

本实验 Decode C16：

```text
baseline:
TPOT P50 = 37.1 ms
throughput = 104.43

optimized:
TPOT P50 = 51.9 ms
throughput = 275.84
```

就是典型案例。

更关键的是 TTFT：

```text
58.28 s → 0.82 s
```

说明以前用户主要在排队。

所以系统优化不是追求单一指标：

```text
max throughput
```

而是寻找：

```text
throughput
+
TTFT
+
TPOT
+
E2E
```

之间的可接受平衡。

---

# 18. 为什么 AICore 降低反而吞吐更高

128K：

```text
baseline:
AICore avg = 86.9%
throughput = 2.77

DSA-CP:
AICore avg = 53.3%
throughput = 7.18
```

如果错误地把 AICore 当“效率”，会得到：

```text
53% 比 87% 更快
```

看起来矛盾。

其实不矛盾。

---

## 18.1 利用率不等于有效吞吐

设备可能：

```text
100% 忙
```

但忙在低效率执行、等待相关 kernel、数据搬运、重复计算等路径。

优化后：

```text
做更少的无效/重复工作
```

即使平均 AICore 数值低，也能更早完成任务。

---

## 18.2 采样窗口污染

本实验 `npu-smi` 是低频外部采样。

例如 case 只跑 18 秒：

```text
启动边界
结束边界
```

会占很多 sample。

优化后 case 更短：

```text
边界 idle sample 占比可能反而更大
```

从而拉低平均 AICore。

---

## 18.3 5 秒采样看不到毫秒级 bubble

真正的：

```text
kernel
communication
all-to-all
graph replay
同步
```

是微秒/毫秒量级。

5 秒采样只能判断：

```text
长期是不是明显闲
```

无法解释某个 kernel 为什么慢。

所以要做微观归因，需要：

```text
msprof / CANN profiler
```

而不是只看 `npu-smi`。

---

# 19. HBM 结果告诉了我们什么

本实验 HBM 峰值：

```text
约 57.4 ~ 58.4 GiB/卡
```

非常稳定。

例如：

```text
baseline balanced C16:
83.59 tok/s
57.7 GiB

optimized balanced C16:
200.23 tok/s
57.9 GiB
```

吞吐：

```text
+139.5%
```

HBM：

```text
只增加约 0.2 GiB
```

这说明大部分收益不是靠：

```text
“暴力吃更多显存”
```

得到的。

主要来自：

```text
调度效率
通信路径
attention 并行
Prefix 复用
```

这是很好的工程性质。

---

# 20. 目前实验中最重要的未决问题

## 20.1 batch8192 重复性

```text
正式：146.65
辅助复验：83.45
```

差异过大。

下一轮必须排查：

- compile cache；
- warmup；
- 第一个请求效应；
- NPU frequency；
- expert routing；
- workload phase；
- case 执行顺序；
- 是否存在残留 cache。

---

## 20.2 NPUGraph Ex

目前：

```text
graph_off decode C8 = 188.49
```

看起来很高，但不是严格同配置 A/B。

必须固定：

```text
seq16
batch10240
Prefix off
FlashComm1 on
DSA-CP on
```

只切：

```text
Graph ON/OFF
```

---

## 20.3 Prefix 的纯因果值

需要固定底座后人为构造：

```text
0% hit
50% hit
100% hit
```

而不是只测一个 shared16K。

---

## 20.4 1M 并未真正进行 1M request 验证

当前：

```text
max_model_len = 1,048,576
```

只说明：

```text
服务以 1M 上限配置
```

正式 workload 最大：

```text
128K
```

所以准确表述应是：

> 服务以 1M max_model_len 成功运行，并完成至 128K 的稳定负载实验。

不能说：

> 已完成真实 1M 性能验证。

后续应该：

```text
256K C1
512K C1
768K C1
~1M C1
```

逐步推进。

---

# 21. 生产配置应该如何分 Profile

基于现有实验，不建议“一个配置打所有 workload”。

---

## 21.1 Profile A：Interactive / OpenCode

特点：

```text
多人/多轮交互
重复 system prompt
重复 repo context
对 TTFT 敏感
```

优先：

```text
Prefix Cache = ON
seq = 8~16
batch = 8192 起步
```

Graph / DSA 是否开启应通过同 workload A/B 决定。

重点指标：

```text
TTFT P95
TPOT P95
cache hit ratio
output tok/s
```

---

## 21.2 Profile B：General Throughput

当前候选：

```text
max_num_seqs = 16
max_num_batched_tokens = 10240
FlashComm1 = ON
DSA-CP = ON
```

Prefix 是否开启：

```text
取决于共享前缀比例
```

Graph：

```text
待严格 A/B 决定
```

---

## 21.3 Profile C：Long Context

对于 32K / 128K：

```text
核心：
FlashComm1 + DSA-CP
```

Prefix Cache：

```text
只有真实共享前缀才有价值
```

并发不一定要很高，因为：

```text
长上下文单请求已经很重
```

重点：

```text
TTFT
HBM
KV occupancy
preemption
DSA-CP scaling
```

---

# 22. 下一轮实验应怎样设计

## 22.1 第一步：先解决统计重复性

每个 case：

```text
启动服务
↓
health ready
↓
固定 warmup
↓
不计入统计
↓
等待稳定
↓
正式 Run 1
↓
Run 2
↓
Run 3
```

报告：

```text
mean
std
CV = std / mean
95% CI
```

不要只报告最高值。

---

## 22.2 第二步：随机化 case 顺序

不要总是：

```text
baseline
→ seq8
→ batch8192
→ optimized
```

因为：

```text
设备温度
频率
compile cache
runtime cache
```

可能跟执行顺序相关。

应该随机或采用 Latin-square 风格平衡顺序。

---

## 22.3 第三步：严格 Graph A/B

固定所有条件：

```text
seq16
batch10240
FlashComm1 ON
DSA-CP ON
Prefix OFF
```

测试：

```text
G0 NPUGraph Ex OFF
G1 NPUGraph Ex ON
```

每组 3 次。

并采：

```text
真实 running batch histogram
graph capture shape
graph hit
fallback
```

---

## 22.4 第四步：严格 Prefix Cache A/B

配置完全相同。

构造：

```text
P0: 0% shared prefix
P1: 50%
P2: 100%
```

每种：

```text
Prefix OFF / ON
```

最终画：

```text
hit ratio
   ↓
TTFT
output tok/s
HBM/KV occupancy
```

---

## 22.5 第五步：开放环 QPS

闭环只能告诉：

```text
固定并发下系统表现
```

生产流量更像：

```text
每秒来了多少请求
```

即 open-loop：

```text
1 QPS
2 QPS
4 QPS
8 QPS
...
```

找到：

```text
waiting 持续增长的点
```

即 saturation knee。

然后定义例如：

```text
TTFT P95 < X
TPOT P95 < Y
```

计算 SLO goodput。

---

## 22.6 第六步：长上下文阶梯

```text
128K
256K
512K
768K
~1M
```

先 C1。

再在安全范围：

```text
C2
```

记录：

```text
KV cache utilization
HBM
TTFT
output throughput
preemption
OOM
```

---

## 22.7 第七步：Profiler

不需要每个 case 都 profiler。

选择最有解释力的：

```text
32K C8:
FlashComm
vs
DSA-CP

128K C2:
baseline-like
vs
DSA-CP
```

抓短窗口。

分析：

```text
Attention kernel
Lightning/indexer path
MoE dispatch/combine
HCCL communication
FlashComm
DSA overlap
host gap
graph replay/fallback
```

---

## 22.8 第八步：正确性

temperature=0 + seed 固定还不够。

增加：

```text
response text SHA256
token IDs hash
finish_reason
output length
```

这样才能说：

```text
性能优化没有改变输出
```

否则只能说：

```text
请求成功且长度符合预期
```

---

# 23. 从 AI Infra / 性能建模视角如何总结

这套实验最后应该抽象成：

```text
Workload state
    ↓
System bottleneck
    ↓
Configuration
    ↓
Performance
```

例如：

```text
高并发 Balanced
↓
scheduler slot 不够
↓
提高 max_num_seqs
↓
throughput ↑ / TTFT ↓
```

```text
128K long context
↓
attention / communication 成为主瓶颈
↓
FlashComm1 + DSA-CP
↓
throughput 大幅 ↑
```

```text
OpenCode shared prefix
↓
重复 Prefill
↓
Prefix Cache
↓
TTFT 和有效 throughput 大幅改善
```

因此最终不是训练一个：

```text
“哪个配置最快？”
```

的简单模型。

而是：

```text
输入：
prompt length distribution
output length distribution
concurrency/QPS
prefix hit ratio
SLO

输出：
max_num_seqs
max_num_batched_tokens
Prefix
Graph
FlashComm
DSA-CP
```

然后优化目标：

```text
maximize goodput
subject to:
TTFT P95 <= SLA_TTFT
TPOT P95 <= SLA_TPOT
HBM <= limit
error_rate <= limit
```

这就从：

```text
人工调参
```

上升成：

```text
SLA-constrained workload-aware serving control
```

也是这两轮实验最有延展性的研究价值。

---

# 24. 概念速查表

| 概念 | 一句话解释 |
|---|---|
| C8 | Benchmark 客户端保持 8 个并发 in-flight 请求 |
| C16 | 保持 16 个并发请求 |
| Closed-loop | 一个请求完成后立即补一个，以保持固定并发 |
| Open-loop | 按固定 QPS/到达率发送，不等待之前请求完成 |
| TP8 | 一个模型的张量计算分到 8 个 rank |
| EP8 | MoE experts 分布在 8 个 expert-parallel rank |
| DP1 | 只有一个数据并行 replica |
| Prefill | 处理 Prompt 并建立 KV Cache |
| Decode | 逐 token 自回归生成 |
| KV Cache | 保存历史 Key/Value，避免每步重算整个 Prompt |
| block_size=32 | KV cache 的主要分页/管理 token 粒度 |
| max_model_len | 单请求 input + output 的最大 token 上限 |
| max_num_seqs | 一次 scheduler iteration 最多处理的 sequence 数 |
| max_num_batched_tokens | 一次 scheduler iteration 最多处理的 token 数 |
| Chunked Prefill | 将长 Prompt 拆成多个 chunk，允许与 Decode 混排 |
| Async Scheduling | CPU 准备下一步时与 NPU 当前计算 overlap |
| Prefix Cache | 相同前缀直接复用已经算好的 KV blocks |
| TTFT | 请求提交到收到第一 token 的时间 |
| TPOT | 第一 token 后平均每个输出 token 的时间 |
| ITL | 相邻两个输出 token 的真实时间间隔 |
| E2E | 请求发出到最后一个 token 完成 |
| output tok/s | 全服务每秒生成的 output token |
| total tok/s | input + output token 的总处理速率 |
| P50 | 中位数 |
| P95/P99 | 尾延迟指标 |
| Goodput | 满足 SLO 的有效完成吞吐 |
| Eager | 每次按正常框架路径动态 dispatch |
| Graph | 捕获重复执行图并 replay |
| FULL_DECODE_ONLY | 主要在纯 Decode 阶段使用 full ACLGraph |
| NPUGraph Ex | Ascend 的 FX graph 编译期优化/融合层 |
| ACLGraph | Ascend 上运行时 graph capture/replay 机制 |
| capture size | Graph 可直接匹配的 batch/shape 规模 |
| fallback | shape/条件不匹配时退回其他执行路径 |
| FlashComm1 | Ascend 针对 SP/TP 通信的增强优化，尽量推迟 AllGather 降低通信 |
| DSA | DeepSeek Sparse Attention 路径 |
| CP | 沿 context/sequence 维度做并行 |
| DSA-CP | 针对 DeepSeek DSA attention 的 Context Parallel 优化 |
| AICore | NPU AI Core 的粗粒度利用率观测 |
| HBM | NPU 高带宽显存 |
| Warmup | 正式计时前先运行以消除编译、allocator、cache 冷启动 |
| Saturation knee | QPS/并发继续提高后 waiting 开始持续增长的容量拐点 |
| SLA/SLO | 对 TTFT/TPOT/E2E 等服务质量的约束 |

---

# 25. 参考资料

以下资料用于补充概念解释；实验数值与实验结论来自本次用户提供的两轮实验报告。

1. **vLLM SchedulerConfig**  
   https://docs.vllm.ai/en/latest/api/vllm/config/scheduler/  
   主要用于 `max_num_seqs`、`max_num_batched_tokens`、Chunked Prefill 等定义。

2. **vLLM Benchmark Serve**  
   https://docs.vllm.ai/en/latest/api/vllm/benchmarks/serve/  
   用于 output throughput、total token throughput、TTFT、TPOT、E2E、goodput 的计算口径。

3. **vLLM Automatic Prefix Caching**  
   https://docs.vllm.ai/en/latest/design/prefix_caching/  
   用于 Prefix Cache block hash、KV block reuse、cache isolation 等机制。

4. **vLLM Ascend Graph Mode**  
   https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/graph_mode.html  
   用于 ACLGraph、Npugraph_ex、FULL/FULL_DECODE_ONLY/PIECEWISE/NONE 路径解释。

5. **vLLM Ascend Additional Configuration**  
   https://docs.vllm.ai/projects/ascend/en/latest/user_guide/configuration/additional_config.html  
   用于 `enable_flashcomm1`、`enable_dsa_cp`、`enable_npugraph_ex` 等配置定义。

6. **vLLM Ascend Sequence Parallelism / Flash Comm V1**  
   https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/sequence_parallelism.html  
   用于 FlashComm1 对 MLA/MoE 通信路径的解释。

7. **vLLM Ascend Context Parallel**  
   https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/context_parallel.html  
   用于 DCP 与独立 DSA-CP 路径的区分。

8. **vLLM Ascend DeepSeek-V4-Flash**  
   https://docs.vllm.ai/projects/ascend/en/latest/tutorials/models/DeepSeek-V4-Flash.html  
   用于 DeepSeek-V4 的 `FULL_DECODE_ONLY`、Async Scheduling、FlashComm 等官方部署说明。

9. **vLLM DeepSeek DSA model architecture reference**  
   https://docs.vllm.ai/en/stable/api/vllm/models/deepseek_v32/  
   用于 DSA、Lightning Indexer、top-k sparse attention 的架构背景。

---

# 附录 A：原始关键结果表

| Case | output tok/s | total tok/s | TTFT s P50/P95/P99 | TPOT ms P50/P95/P99 | E2E s P50/P95/P99 | AICore % avg/P95/max | HBM peak GiB/card |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline__decode_c8 | 103.48 | 209.59 | 20.42 / 20.56 / 20.70 | 37.4 / 38.0 / 38.0 | 39.56 / 39.68 / 39.82 | 70.7 / 77.0 / 78 | 57.7 |
| graph_off__decode_c8 | 188.49 | 381.76 | 1.13 / 3.53 / 3.53 | 38.1 / 43.7 / 44.1 | 21.69 / 22.99 / 22.99 | 69.7 / 78.0 / 78 | 57.4 |
| optimized__decode_c8 | 156.18 | 316.34 | 0.75 / 3.15 / 3.15 | 47.5 / 52.7 / 52.9 | 26.18 / 27.42 / 27.42 | 53.8 / 65.0 / 67 | 57.6 |
| baseline__decode_c16 | 104.43 | 211.51 | 58.28 / 60.99 / 60.99 | 37.1 / 37.1 / 40.3 | 77.24 / 79.96 / 79.96 | 71.9 / 76.0 / 77 | 57.7 |
| optimized__decode_c16 | 275.84 | 558.68 | 0.82 / 5.58 / 5.58 | 51.9 / 57.0 / 60.5 | 29.64 / 32.10 / 32.10 | 53.7 / 66.0 / 86 | 57.7 |
| baseline__balanced_c8 | 73.03 | 1244.72 | 14.90 / 20.63 / 21.77 | 44.5 / 60.3 / 60.8 | 25.64 / 32.46 / 32.78 | 64.3 / 100.0 / 100 | 57.7 |
| seq8__balanced_c8 | 99.21 | 1690.76 | 2.29 / 12.38 / 14.04 | 58.7 / 88.4 / 89.7 | 20.52 / 26.62 / 26.96 | 57.2 / 93.5 / 97 | 57.8 |
| batch8192__balanced_c8 | 146.65 | 2499.38 | 2.61 / 4.17 / 4.17 | 42.7 / 51.4 / 52.1 | 13.88 / 15.00 / 15.01 | 66.2 / 100.0 / 100 | 58.1 |
| baseline__balanced_c16 | 83.59 | 1424.56 | 37.18 / 40.09 / 40.62 | 41.3 / 49.9 / 51.3 | 47.73 / 50.43 / 51.10 | 75.7 / 100.0 / 100 | 57.7 |
| batch10240__balanced_c16 | 111.54 | 1900.97 | 7.73 / 26.48 / 29.96 | 102.4 / 150.2 / 159.6 | 36.53 / 48.63 / 49.43 | 44.2 / 100.0 / 100 | 58.4 |
| optimized__balanced_c16 | 200.23 | 3412.44 | 1.99 / 5.30 / 5.30 | 70.4 / 78.5 / 79.0 | 20.38 / 22.92 / 22.93 | 67.6 / 95.0 / 97 | 57.9 |
| baseline__prefill32k_c8 | 22.45 | 5770.93 | 27.43 / 37.58 / 41.59 | 130.1 / 149.1 / 151.7 | 45.06 / 55.80 / 58.43 | 79.3 / 100.0 / 100 | 57.7 |
| batch8192__prefill32k_c8 | 27.01 | 6943.69 | 19.54 / 31.85 / 32.80 | 140.6 / 238.0 / 246.8 | 37.40 / 37.85 / 37.89 | 89.9 / 100.0 / 100 | 58.1 |
| flashcomm__prefill32k_c8 | 28.38 | 7295.57 | 14.08 / 28.90 / 30.87 | 170.3 / 243.5 / 248.8 | 35.71 / 36.04 / 36.06 | 64.7 / 100.0 / 100 | 58.1 |
| dsa_cp__prefill32k_c8 | 43.78 | 11255.97 | 8.76 / 15.72 / 16.82 | 111.2 / 152.1 / 155.6 | 22.88 / 23.33 / 23.36 | 49.0 / 90.0 / 95 | 57.9 |
| optimized__prefill32k_c8 | 50.43 | 12966.55 | 5.11 / 12.26 / 13.08 | 106.8 / 138.6 / 145.0 | 19.99 / 25.87 / 26.76 | 69.0 / 100.0 / 100 | 57.9 |
| baseline__long128k_c2 | 2.77 | 5681.32 | 28.20 / 42.76 / 43.88 | 278.8 / 384.4 / 384.7 | 45.58 / 53.81 / 54.93 | 86.9 / 100.0 / 100 | 57.7 |
| dsa_cp__long128k_c2 | 7.18 | 14707.55 | 11.37 / 14.49 / 14.77 | 97.7 / 142.9 / 147.0 | 17.52 / 17.80 / 17.82 | 53.3 / 100.0 / 100 | 57.9 |
| optimized__long128k_c2 | 7.33 | 15018.46 | 11.09 / 14.86 / 15.01 | 96.3 / 144.8 / 144.9 | 17.15 / 17.97 / 18.04 | 73.0 / 100.0 / 100 | 57.9 |
| baseline__shared16k_c8 | 36.75 | 4743.09 | 16.36 / 21.28 / 23.93 | 79.6 / 98.9 / 101.2 | 27.59 / 33.14 / 34.40 | 69.3 / 100.0 / 100 | 57.7 |
| prefix__shared16k_c8 | 141.76 | 18294.24 | 0.97 / 3.83 / 3.83 | 39.1 / 62.6 / 64.2 | 7.15 / 8.75 / 8.75 | 40.0 / 77.0 / 79 | 58.2 |
| optimized__shared16k_c8 | 120.88 | 15599.53 | 0.79 / 3.79 / 3.79 | 49.8 / 71.4 / 72.7 | 8.38 / 10.11 / 10.11 | 27.9 / 66.0 / 100 | 57.9 |

---

# 附录 B：一句话读懂本次实验

如果只记住一句话，可以记成：

> **这次实验不是证明“某个开关最快”，而是证明 DeepSeek-V4 Serving 的瓶颈会随 workload 变化：高并发先受 scheduler capacity 限制，长上下文转向 DSA attention/通信瓶颈，共享前缀则转向重复 Prefill；因此正确的生产策略是 workload-aware profile，而不是全局唯一配置。**
