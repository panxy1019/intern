# DeepSeek-V4 TP8 两轮吞吐优化实验报告

## 1. 结论摘要

本次在同一 DeepSeek-V4-Flash-0731-w8a8、同一 TP8/EP8 Worker、同一模型权重和固定请求生成器上完成两轮实验。第一轮建立负载曲线，第二轮筛选 batching、Prefix Cache、NPUGraph Ex、FlashComm1 和 DSA-CP，并回放组合配置。正式第二轮 16/16 case 成功，HTTP 错误数为 0；实验结束后原始基线已恢复且 `/health` 返回 200。

- 混合负载最明显的调度收益：`max_num_seqs 4 -> 8` 后 balanced C8 从 73.03 提升到 99.21 output tok/s（+35.8%）。
- 组合配置 balanced C16 达到 200.23 output tok/s，相对基线 C16 为 +139.5%。
- DSA-CP 对长上下文最有效：128K C2 从 2.77 提升到 7.18 output tok/s（+158.9%）。
- 共享 16K 前缀启用 Prefix Cache 后从 36.75 提升到 141.76 output tok/s（+285.7%），但该收益不能外推到无共享前缀流量。
- 组合配置 Decode C16 达到 275.84 output tok/s，相对基线为 +164.1%。
- 不建议立即把组合配置设为唯一生产默认值。Graph、Prefix 与通信优化的部分 case 并非严格单变量成对实验，且 `batch8192` 两次观测波动较大；应再做 3 次固定次序重复和输出文本哈希检查。

## 2. 实验环境与固定条件

```text
模型：DeepSeek-V4-Flash-0731-w8a8
运行时：vLLM 0.22.1 + vLLM-Ascend 0.22.1rc1
并行：TP=8，DP=1，Expert Parallel=on
设备：a3-server-00 物理 NPU 2..9（容器内 8 个逻辑设备）
上下文：max_model_len=1,048,576
KV：block_size=32，gpu_memory_utilization=0.88
固定项：chunked prefill=on，async scheduling=on，temperature=0，固定随机种子
请求方式：闭环固定并发；流式接口统计 TTFT、TPOT 与 E2E
```

吞吐口径：`output tok/s` 只计算生成 token；`total tok/s` 计算输入与输出 token 之和。长输入场景的 total tok/s 很高并不等价于生成吞吐高。

## 3. 配置矩阵

| 变体 | max_num_seqs | max_num_batched_tokens | Prefix Cache | NPUGraph Ex | FlashComm1 | DSA-CP |
|---|---:|---:|---|---|---|---|
| baseline | 4 | 4096 | off | on | off | off |
| seq8 | 8 | 4096 | off | on | off | off |
| batch8192 | 8 | 8192 | off | on | off | off |
| batch10240 | 16 | 10240 | off | on | off | off |
| prefix | 16 | 10240 | on | on | off | off |
| graph_off | 16 | 10240 | off | off | off | off |
| flashcomm | 16 | 10240 | off | on | on | off |
| dsa_cp | 16 | 10240 | off | on | on | on |
| optimized | 16 | 10240 | on | on | on | on |

## 4. 主要结果

延迟列均为 P50 / P95 / P99。AICore 为 case 采样窗口内八卡样本合并后的 avg / P95 / max；它包含请求开始和结束附近的短空闲样本。

| Case | output tok/s | total tok/s | TTFT s | TPOT ms | E2E s | AICore % | HBM峰值 GiB/卡 | 错误 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline__decode_c8 | 103.48 | 209.59 | 20.42 / 20.56 / 20.70 | 37.4 / 38.0 / 38.0 | 39.56 / 39.68 / 39.82 | 70.7 / 77.0 / 78 | 57.7 | 0 |
| graph_off__decode_c8 | 188.49 | 381.76 | 1.13 / 3.53 / 3.53 | 38.1 / 43.7 / 44.1 | 21.69 / 22.99 / 22.99 | 69.7 / 78.0 / 78 | 57.4 | 0 |
| optimized__decode_c8 | 156.18 | 316.34 | 0.75 / 3.15 / 3.15 | 47.5 / 52.7 / 52.9 | 26.18 / 27.42 / 27.42 | 53.8 / 65.0 / 67 | 57.6 | 0 |
| baseline__decode_c16 | 104.43 | 211.51 | 58.28 / 60.99 / 60.99 | 37.1 / 37.1 / 40.3 | 77.24 / 79.96 / 79.96 | 71.9 / 76.0 / 77 | 57.7 | 0 |
| optimized__decode_c16 | 275.84 | 558.68 | 0.82 / 5.58 / 5.58 | 51.9 / 57.0 / 60.5 | 29.64 / 32.10 / 32.10 | 53.7 / 66.0 / 86 | 57.7 | 0 |
| baseline__balanced_c8 | 73.03 | 1244.72 | 14.90 / 20.63 / 21.77 | 44.5 / 60.3 / 60.8 | 25.64 / 32.46 / 32.78 | 64.3 / 100.0 / 100 | 57.7 | 0 |
| seq8__balanced_c8 | 99.21 | 1690.76 | 2.29 / 12.38 / 14.04 | 58.7 / 88.4 / 89.7 | 20.52 / 26.62 / 26.96 | 57.2 / 93.5 / 97 | 57.8 | 0 |
| batch8192__balanced_c8 | 146.65 | 2499.38 | 2.61 / 4.17 / 4.17 | 42.7 / 51.4 / 52.1 | 13.88 / 15.00 / 15.01 | 66.2 / 100.0 / 100 | 58.1 | 0 |
| baseline__balanced_c16 | 83.59 | 1424.56 | 37.18 / 40.09 / 40.62 | 41.3 / 49.9 / 51.3 | 47.73 / 50.43 / 51.10 | 75.7 / 100.0 / 100 | 57.7 | 0 |
| batch10240__balanced_c16 | 111.54 | 1900.97 | 7.73 / 26.48 / 29.96 | 102.4 / 150.2 / 159.6 | 36.53 / 48.63 / 49.43 | 44.2 / 100.0 / 100 | 58.4 | 0 |
| optimized__balanced_c16 | 200.23 | 3412.44 | 1.99 / 5.30 / 5.30 | 70.4 / 78.5 / 79.0 | 20.38 / 22.92 / 22.93 | 67.6 / 95.0 / 97 | 57.9 | 0 |
| baseline__prefill32k_c8 | 22.45 | 5770.93 | 27.43 / 37.58 / 41.59 | 130.1 / 149.1 / 151.7 | 45.06 / 55.80 / 58.43 | 79.3 / 100.0 / 100 | 57.7 | 0 |
| batch8192__prefill32k_c8 | 27.01 | 6943.69 | 19.54 / 31.85 / 32.80 | 140.6 / 238.0 / 246.8 | 37.40 / 37.85 / 37.89 | 89.9 / 100.0 / 100 | 58.1 | 0 |
| flashcomm__prefill32k_c8 | 28.38 | 7295.57 | 14.08 / 28.90 / 30.87 | 170.3 / 243.5 / 248.8 | 35.71 / 36.04 / 36.06 | 64.7 / 100.0 / 100 | 58.1 | 0 |
| dsa_cp__prefill32k_c8 | 43.78 | 11255.97 | 8.76 / 15.72 / 16.82 | 111.2 / 152.1 / 155.6 | 22.88 / 23.33 / 23.36 | 49.0 / 90.0 / 95 | 57.9 | 0 |
| optimized__prefill32k_c8 | 50.43 | 12966.55 | 5.11 / 12.26 / 13.08 | 106.8 / 138.6 / 145.0 | 19.99 / 25.87 / 26.76 | 69.0 / 100.0 / 100 | 57.9 | 0 |
| baseline__long128k_c2 | 2.77 | 5681.32 | 28.20 / 42.76 / 43.88 | 278.8 / 384.4 / 384.7 | 45.58 / 53.81 / 54.93 | 86.9 / 100.0 / 100 | 57.7 | 0 |
| dsa_cp__long128k_c2 | 7.18 | 14707.55 | 11.37 / 14.49 / 14.77 | 97.7 / 142.9 / 147.0 | 17.52 / 17.80 / 17.82 | 53.3 / 100.0 / 100 | 57.9 | 0 |
| optimized__long128k_c2 | 7.33 | 15018.46 | 11.09 / 14.86 / 15.01 | 96.3 / 144.8 / 144.9 | 17.15 / 17.97 / 18.04 | 73.0 / 100.0 / 100 | 57.9 | 0 |
| baseline__shared16k_c8 | 36.75 | 4743.09 | 16.36 / 21.28 / 23.93 | 79.6 / 98.9 / 101.2 | 27.59 / 33.14 / 34.40 | 69.3 / 100.0 / 100 | 57.7 | 0 |
| prefix__shared16k_c8 | 141.76 | 18294.24 | 0.97 / 3.83 / 3.83 | 39.1 / 62.6 / 64.2 | 7.15 / 8.75 / 8.75 | 40.0 / 77.0 / 79 | 58.2 | 0 |
| optimized__shared16k_c8 | 120.88 | 15599.53 | 0.79 / 3.79 / 3.79 | 49.8 / 71.4 / 72.7 | 8.38 / 10.11 / 10.11 | 27.9 / 66.0 / 100 | 57.9 | 0 |

## 5. 分项技术分析

### 5.1 Batching 与调度容量

`seq8` 相对 baseline 只提高序列上限，balanced C8 从 73.03 到 99.21 output tok/s。这说明原来的 4 个 sequence slot 无法同时容纳足够多的 Prefill chunk 和 Decode 序列，调度器经常无法形成更大的有效批次。

在 seq8 基础上把 token budget 提到 8192，balanced C8 本轮达到 146.65 output tok/s；但一次先前辅助复验仅为 83.45 tok/s，变异幅度过大。可能来源包括首次编译缓存、专家路由分布、请求到达相位及 NPU 频率状态。因此 146.65 应视为峰值观测，不是稳定容量承诺。

继续提高到 seq16/batch10240 后，balanced C16 为 111.54 tok/s。它高于基线 C16，但没有证明更大上限总是更优：更大的 waiting 集合会增加排队和单步调度成本，P95 TPOT 也升至 150.2 ms。

### 5.2 Chunked Prefill

Chunked Prefill 在全部变体中保持开启，因此本次没有 on/off 因果对照。它的价值是把长 Prompt 切成 token budget 可容纳的块，使 Decode 能插入块间执行，控制尾延迟和 KV 峰值。32K/128K 结果证明长输入可以稳定推进，但不能据此量化 Chunked Prefill 自身增益。下一轮应固定其余参数做 `enable/disable` 或比较 2048/4096/8192 chunk budget。

### 5.3 Prefix Cache

共享 16K 前缀 case 从 36.75 到 141.76 output tok/s，TTFT P95 从 21.28s 降至 3.83s。机制上，后续请求复用已计算的前缀 KV block，跳过大段重复 Prefill，释放 token budget 给 Decode。

这个对照同时改变了调度上限，因此 3.86x 不是纯 Prefix Cache 因果值。生产启用前还要关注 block hash/eviction、租户隔离和低命中率负载的管理开销。

### 5.4 NPUGraph Ex

`graph_off/decode_c8` 观测到 188.49 output tok/s，高于原基线开启图时的 103.48。但 graph_off 同时使用 seq16/batch10240，不能把差值全部归因于关闭图。

从机制上看，图执行只有在 shape 命中捕获集合、重放开销低于 eager dispatch、且 MoE 动态路由没有频繁触发 fallback 时才获益。当前 `FULL_DECODE_ONLY` 捕获 `[1,2,4]`，而 C8/C16 下真实 running sequence 数可能经常落在捕获集合之外。严格结论需要同一 seq/batch 下补 `NPUGraph Ex on/off`，并统计 graph hit、fallback 和 replay 次数。

### 5.5 FlashComm1 与 DSA-CP

FlashComm1 配置的 32K C8 为 28.38 output tok/s。DSA-CP 在相同 seq16/batch10240、FlashComm1=on 的基础上只增加 DSA-CP，32K C8 进一步到 43.78，这是本轮最接近严格单变量的 DSA-CP 证据。

128K C2 的 output tok/s 从基线 2.77 到 DSA-CP 7.18，TTFT P95 从 42.76s 降到 14.49s。DSA-CP 将 DeepSeek 稀疏注意力相关计算/通信按序列维度并行化，长序列时可摊薄同步和索引通信固定成本，因此收益随上下文长度放大。

### 5.6 组合配置

组合配置在 balanced C16 达到 200.23 output tok/s，在 32K C8 达到 50.43，在 128K C2 达到 7.33。它是本轮最高吞吐候选，而不是每类请求的最优点：例如共享前缀纯 prefix 变体高于 optimized，说明通信/图/缓存组合存在非线性交互。

## 6. 资源与队列观测

每个 case 保存了 1 秒级 cgroup/vLLM 指标和 5 秒级 `npu-smi`。报告表中的 HBM 峰值按单卡统计；详细原始样本位于各 case 的 `worker_metrics/samples.jsonl`。

CPU 采集器记录了内存、CPU throttling 次数/时间，但本轮 cgroup v1 路径没有保存 `cpuacct.usage` 差分，因此不能客观给出 CPU 平均利用率。报告不会用 throttling 代替 CPU 利用率。下一版采集器应同时保存 `cpuacct.usage`、`cpu.stat usage_usec` 和已知 vLLM PID 的 `/proc/<pid>/stat`。

AICore 采样是低频外部采样，不足以解释毫秒级 kernel 气泡；它适合判断长期供给不足，不适合代替 CANN timeline。要定位图 fallback、all-to-all 等待和 DSA-CP overlap，应追加 msprof/torch profiler 的短窗口。

## 7. 正确性、稳定性与实验限制

- 第一轮 13/13、正式第二轮 16/16 请求 case 均无 HTTP 失败；正式第二轮结束后原始配置恢复健康。
- 固定 temperature=0、固定随机种子，且服务返回了预期 token 数；本轮未对每个输出执行文本哈希或语义等价比较，因此不能宣称生成内容逐字一致。
- 未预先定义 TTFT/TPOT SLO，故不能补造 SLO goodput。原始延迟分位数已保留，可在确定 SLO 后离线重算 goodput。
- case 采用闭环并发，不代表开放环到达下的排队稳定性。生产容量应再做固定 QPS 阶梯和过载恢复。
- 第二轮每个变体只正式运行一次；`batch8192` 的辅助复验显示较大波动，应至少重复三轮并报告均值、标准差和置信区间。
- `graph_off`、`prefix` 相对最初 baseline 同时包含调度参数变化，不能作为严格单变量结论。

## 8. 建议配置与下一轮顺序

建议把用途拆成两个 profile，而不是一套参数覆盖所有流量：

```text
通用高吞吐候选：max_num_seqs=16, max_num_batched_tokens=10240,
                  chunked prefill=on, async scheduling=on,
                  FlashComm1=on, DSA-CP=on
共享前缀场景：在命中率监控和租户隔离成立时额外启用 Prefix Cache
NPUGraph Ex：暂不做最终定论，完成严格 on/off 复验后决定
```

下一轮按以下顺序执行：

1. 固定 seq16/batch10240/FlashComm1/DSA-CP，严格测试 NPUGraph Ex on/off，各重复 3 次。
2. 固定同一配置，测试 Prefix Cache on/off；分别使用 0%、50%、100% 共享前缀命中率。
3. 对 seq8/batch8192 与 seq16/batch10240 各重复 3 次，随机化执行顺序，排除温度和编译缓存偏差。
4. 加入开放环 QPS 阶梯，报告 waiting 增长点、SLO goodput 和恢复时间。
5. 用 CANN profiler 对 32K/128K 各抓一个短窗口，拆分 attention、MoE all-to-all、FlashComm1 和 DSA-CP 重叠。
6. 增加输出哈希、首个请求与稳态请求分层，防止性能优化掩盖生成一致性回退。

## 9. 产物与复现

- 第一轮原始目录：`infralearning/dsv4_tp8/benchmarks/tp8_max_throughput/runs/tp8-perf-20260807T-baseline-opt`
- 第二轮原始目录：`infralearning/dsv4_tp8/benchmarks/tp8_max_throughput/runs/tp8-perf-20260807T-round2c`
- 每个 case：`result.json`、`client.log`、`worker_metrics/samples.jsonl`、`npu-smi.log`。
- 手动查看进度：`./show_progress.sh <run_id>`。
- 生命周期脚本已修复：显式 IPv4 port-forward、Pod 内健康检查、重启后按需重建转发、Zombie PID 判定、恢复阶段忽略 STOP 标记。

## 10. 最终状态

```text
Round 1：13/13 case 完成，0 个请求错误
Round 2：16/16 case 完成，0 个请求错误
模型服务：已恢复原始 baseline 配置
健康检查：HTTP 200
```
