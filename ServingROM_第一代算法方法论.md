# ServingROM 第一代算法方法论

> **副标题：基于 POD–DMDc–MPC 的 1P2D LLM 推理系统伴随式降阶数字孪生**  
> 版本：POC v1.0  
> 日期：2026-08-05  
> 适用对象：固定拓扑的 1 Prefill + 2 Decode 分离式推理系统  
> 目标：构建一个伴随真实推理系统运行、能够预测短期状态演化并在线给出调度参数的经典降阶动力系统

---

## 1. 文档目的

本文给出 ServingROM 第一代算法的完整方法论。其核心不是再建立一个“输入配置到延迟”的静态性能回归器，而是把整个 1P2D 推理服务抽象为一个受外部请求流驱动、受调度参数控制的离散时间动力系统；随后从高维请求分布状态中提取低维主导坐标，识别低维受控状态转移，并在该低维模型上实时求解有限时域控制问题。

算法采用经典而清晰的技术链路：

\[
\boxed{
\text{高维请求分布状态}
\xrightarrow{\text{POD}}
\text{低维状态}
\xrightarrow{\text{DMDc}}
\text{线性受控动力学}
\xrightarrow{\text{MPC}}
\text{在线调度参数}
}
\]

ServingROM 作为旁路控制面组件运行。它不参与 Transformer 前向计算，不修改模型参数，也不取代 vLLM-Ascend 或现有 Proxy 的执行逻辑。它读取 Proxy、Prefill、Decode、KV 传输和设备监控数据，构建系统状态，预测未来若干控制周期的队列、KV 和 SLO 风险，并向现有调度器下发可执行参数。

---

## 2. 研究问题与 POC 验证目标

第一代 POC 需要回答以下五个基础问题。

### 2.1 推理服务是否存在可利用的低维状态结构

原始系统在任意时刻包含数量可变的请求，每个请求又具有输入长度、等待时间、生成进度、上下文长度、KV 占用和 SLO 余量等属性。将这些请求表示为固定网格上的分布状态后，维度可达到数百甚至上千。需要验证这些高维分布快照是否集中在一个明显低维的线性子空间附近，即 POD 奇异值是否快速衰减，以及有限数量模态是否能保留与 TTFT、TPOT、KV 容量和 goodput 相关的动态信息。

### 2.2 低维坐标是否具有有限时域可预测性

单步预测准确并不意味着可用于控制。需要检验：给定当前低维状态、调度控制和未来请求到达估计，线性 DMDc 模型是否能够在若干控制周期内稳定预测队列压力转移、Prefill 到 Decode 的负载传递、KV 累积和恢复过程。

### 2.3 ROM 是否比完整请求事件模拟更适合在线滚动优化

现有 LLM serving MPC 通常保留完整请求队列，并逐批次模拟未来执行。ServingROM 希望将高维请求集合压缩为固定维数低维状态，使控制器的预测和优化成本不随活动请求数线性增长，从而能在较短控制周期内反复求解。

### 2.4 ROM-MPC 是否优于固定配置和反应式策略

POC 不只评价预测误差，还需要闭环评价：在到达率突变、输入长度分布变化和 D1/D2 负载不均衡时，ROM-MPC 是否能在相同硬件条件下提高 SLO attainment 和 goodput，并减少参数抖动、KV 峰值和过载持续时间。

### 2.5 低维模态是否具有可解释的系统意义

理想情况下，前几个 POD 模态应对应能够解释的系统运动，例如总负载模态、Prefill–Decode 压力转移模态、D1–D2 失衡模态、KV 积累模态和 SLO 风险传播模态。该解释性是 ServingROM 区别于纯黑箱预测器的重要价值。

---

## 3. 与现有 LLM serving 预测控制结构的关系

### 3.1 BiScale 的结构

BiScale 在 PD 分离系统中采用双层控制：粗粒度层负责 placement、实例配置和基准频率，细粒度层针对 Prefill 使用有限时域 MPC、针对 Decode 使用逐批次频率调整。其 Prefill MPC保留当前 waiting/running 请求及其输入长度，投影未来若干 batch，并使用离线训练的批次延迟模型评估候选频率序列。其预测对象主要是“给定 batch 形状与硬件配置时的单批执行时间”，队列演化由显式事件投影得到。

### 3.2 SynergySched/NexusSched 的结构

该框架建立结构感知的单 iteration 性能函数，以 batch size 和 scheduled tokens 为核心输入，在线拟合表示硬件能力和短期漂移的参数。引擎层根据预测延迟搜索下一 iteration 的 batch 配置，集群层读取预测延迟、pending work、空闲显存等低维手工状态进行路由。

### 3.3 ServingROM 的结构差异

ServingROM 不仅预测单个 batch 需要多长时间，而是直接学习完整服务状态的低维转移：

\[
(z_k,u_k,d_k)\longmapsto z_{k+1}.
\]

其中，\(z_k\) 由高维请求分布状态通过 POD 得到，\(u_k\) 是控制参数，\(d_k\) 是外部请求到达。通过反复迭代低维状态方程，可以在不保留每个请求对象的情况下进行多步 rollout。这使其更接近传统 ROM 数字孪生，而不是静态延迟代理模型。

---

## 4. 系统边界与时间离散

### 4.1 受控系统

POC 面向以下固定执行拓扑：

```text
Client requests
      │
      ▼
Token-aware Proxy / Admission Controller
      │
      ▼
Prefill Worker P
      │ KV transfer
      ├──────────────────────┐
      ▼                      ▼
Decode Worker D1        Decode Worker D2
```

系统边界包括：

- Proxy 中的请求接收、token 计数、准入和 P-to-D 路由；
- Prefill waiting/running 状态及 chunked prefill 执行；
- Prefill 完成后的 KV 传输；
- 两个 Decode worker 的 active/waiting 请求、生成进度和 KV block；
- 端到端请求时间戳和 SLO；
- 可由控制器动态修改的 token budget、chunk size、路由比例和并发上限。

### 4.2 控制周期

定义统一控制周期 \(\Delta t_c\)，在时刻

\[
t_k=k\Delta t_c
\]

构造系统快照。POC 推荐首先测试：

\[
\Delta t_c\in\{100\text{ ms},200\text{ ms},500\text{ ms},1\text{ s}\}.
\]

最终周期应满足两项条件：

1. 能分辨队列增长、KV 转移和 Decode 累积等主要瞬态；
2. 控制器在一个周期内能够完成状态构造、POD 投影、ROM rollout、QP 求解和参数下发。

离散动力系统记为：

\[
x_{k+1}=F(x_k,u_k,d_k)+\xi_k,
\]

\[
y_k=G(x_k,u_k)+\nu_k,
\]

其中 \(x_k\) 是高维全阶状态，\(u_k\) 是控制输入，\(d_k\) 是外部请求到达扰动，\(y_k\) 是 SLO、吞吐和资源输出，\(\xi_k,\nu_k\) 表示未建模因素和测量噪声。

---

## 5. 全阶状态：从变长请求集合到分布场

### 5.1 为什么必须使用分布状态

只使用 queue length、GPU utilization、KV usage 等少数标量，会丢失决定未来服务演化的关键信息。例如，队列中 16 个 256-token 请求与 16 个 8192-token 请求具有相同请求数，但 Prefill 服务需求完全不同；Decode 中同样的 active sequence 数量，在上下文长度和 SLO slack 不同时具有完全不同的 TPOT 风险。

因此，将变长请求集合表示为固定维数的直方图或网格分布。该表示与队列流体模型中的 measure-valued state 思想一致：状态不是单个队长，而是任务属性在长度、年龄和剩余服务维度上的分布。

### 5.2 Prefill 等待状态

对每个尚未进入 Prefill 执行的请求 \(q\)，定义：

- 输入 token 数 \(L_q^{\mathrm{in}}\)；
- 当前等待年龄 \(a_q^P=t_k-t_q^{\mathrm{arrival}}\)；
- TTFT 剩余 slack：

\[
s_q^P=\tau_q^{\mathrm{TTFT}}-a_q^P.
\]

第一代状态建议同时构造两个互补直方图。

#### 长度–等待年龄直方图

\[
n_{P,\mathrm{wait}}^{i,j}(k)
=
\sum_{q\in Q_P^{\mathrm{wait}}(k)}
\mathbf 1\{L_q^{\mathrm{in}}\in\mathcal L_i^P\}
\mathbf 1\{a_q^P\in\mathcal A_j^P\}.
\]

它描述 Prefill 队列的工作量和排队年龄结构。

#### 长度–TTFT slack 直方图

\[
h_{P,\mathrm{slack}}^{i,j}(k)
=
\sum_{q\in Q_P^{\mathrm{wait}}(k)}
\mathbf 1\{L_q^{\mathrm{in}}\in\mathcal L_i^P\}
\mathbf 1\{s_q^P\in\mathcal S_j^P\}.
\]

它直接保留即将违约和已经违约的请求分布。

除了请求数直方图，还应构造 token 质量直方图：

\[
m_{P,\mathrm{wait}}^{i,j}(k)
=
\sum_{q\in Q_P^{\mathrm{wait}}(k)}
L_q^{\mathrm{remaining\ prefill}}
\mathbf 1_{i,j}(q).
\]

请求数描述并发和调度对象规模，token 质量描述实际计算需求。二者都应进入全阶状态。

### 5.3 Prefill 运行状态

对于正在执行或已被分片但尚未完成的请求，记录：

- 原始输入长度；
- 已处理 Prefill token；
- 剩余 Prefill token；
- 当前 chunk 大小；
- 本轮开始时间；
- 已累计服务时间。

构造剩余 Prefill token 的长度–服务进度直方图：

\[
n_{P,\mathrm{run}}^{i,j}(k)
=
\sum_{q\in Q_P^{\mathrm{run}}(k)}
\mathbf 1\{L_q^{\mathrm{remaining\ prefill}}\in\mathcal R_i^P\}
\mathbf 1\{\pi_q^P\in\Pi_j^P\},
\]

其中

\[
\pi_q^P=
\frac{L_q^{\mathrm{processed\ prefill}}}
{L_q^{\mathrm{in}}}
\]

是 Prefill 进度。

### 5.4 KV 传输状态

Prefill 完成后，请求进入 KV transfer 阶段。对每个传输任务记录：

- KV 字节数或 block 数；
- 目标 Decode；
- 已传输字节数；
- 传输等待年龄；
- 当前有效带宽。

对目标 Decode \(m\in\{1,2\}\)，构造：

\[
n_{K\to D_m}^{i,j}(k)
=
\sum_{q\in Q_{K\to D_m}(k)}
\mathbf 1\{B_q^{KV,\mathrm{remaining}}\in\mathcal B_i\}
\mathbf 1\{a_q^{KV}\in\mathcal A_j^{KV}\}.
\]

该部分能够表示 Prefill 和 Decode 之间的中间库存与网络压力。

### 5.5 Decode 活动状态

对每个 Decode worker \(D_m\)，对活动请求 \(q\) 定义：

- 当前上下文长度：

\[
L_q^{\mathrm{ctx}}=L_q^{\mathrm{in}}+L_q^{\mathrm{generated}};
\]

- 已生成 token 数；
- 最近一次 token 时间；
- 当前 token 等待年龄：

\[
a_q^D=t_k-t_q^{\mathrm{last\ token}};
\]

- TPOT slack：

\[
s_q^D=\tau_q^{\mathrm{TPOT}}-a_q^D;
\]

- KV block 数；
- 预测或上限剩余输出 token。

构造上下文长度–token slack 直方图：

\[
h_{D_m,\mathrm{slack}}^{i,j}(k)
=
\sum_{q\in Q_{D_m}^{\mathrm{active}}(k)}
\mathbf 1\{L_q^{\mathrm{ctx}}\in\mathcal L_i^D\}
\mathbf 1\{s_q^D\in\mathcal S_j^D\}.
\]

构造上下文长度–生成进度直方图：

\[
n_{D_m,\mathrm{prog}}^{i,j}(k)
=
\sum_{q\in Q_{D_m}^{\mathrm{active}}(k)}
\mathbf 1\{L_q^{\mathrm{ctx}}\in\mathcal L_i^D\}
\mathbf 1\{\pi_q^D\in\Pi_j^D\}.
\]

其中生成进度可基于请求的 `max_new_tokens` 定义：

\[
\pi_q^D=
\frac{L_q^{\mathrm{generated}}}
{L_q^{\mathrm{max\ output}}}.
\]

### 5.6 Decode waiting 与调度阻塞状态

如果 Decode worker 存在等待进入 active batch 的请求，构造等待年龄–KV 长度分布。还需显式记录：

- waiting request 数；
- running request 数；
- swapped/preempted request 数；
- 本轮 scheduled token 数；
- preemption 或 recomputation 次数；
- 当前 batch 中上下文长度的 sum、mean、std、max；
- 本轮 decode iteration latency。

这些标量可与分布状态拼接。

### 5.7 KV Cache 状态

对每个 Decode worker，记录总 block、used block、free block、reserved block 和碎片信息。推荐按上下文长度构造 KV 占用分布：

\[
v_{D_m}^{i}(k)
=
\sum_{q\in Q_{D_m}^{\mathrm{active}}(k)}
B_q^{KV}
\mathbf 1\{L_q^{\mathrm{ctx}}\in\mathcal L_i^{KV}\}.
\]

还应记录：

\[
r_{D_m}^{KV}(k)
=
\frac{B_{D_m}^{\mathrm{used}}(k)}
{B_{D_m}^{\mathrm{total}}},
\]

以及最大可接受的新请求 KV 预算、block allocator 失败次数和 prefix cache 命中占用。

### 5.8 全阶状态向量

将所有分布块和标量按固定顺序拼接：

\[
x_k=
\begin{bmatrix}
\operatorname{vec}(n_{P,\mathrm{wait}})\\
\operatorname{vec}(m_{P,\mathrm{wait}})\\
\operatorname{vec}(h_{P,\mathrm{slack}})\\
\operatorname{vec}(n_{P,\mathrm{run}})\\
\operatorname{vec}(n_{K\to D_1})\\
\operatorname{vec}(n_{K\to D_2})\\
\operatorname{vec}(h_{D_1,\mathrm{slack}})\\
\operatorname{vec}(h_{D_2,\mathrm{slack}})\\
\operatorname{vec}(n_{D_1,\mathrm{prog}})\\
\operatorname{vec}(n_{D_2,\mathrm{prog}})\\
 v_{D_1}\\
 v_{D_2}\\
 x_k^{\mathrm{scalar}}
\end{bmatrix}
\in\mathbb R^n.
\]

推荐的初始 POC 维度约为 \(n=300\sim1000\)。维度的目的不是人为做大，而是保留请求集合的分布结构，使状态更接近马尔可夫表示。

---

## 6. 控制输入、外部扰动和参数

### 6.1 快速控制输入

定义：

\[
u_k=
\begin{bmatrix}
B_P(k)\\
C_P(k)\\
\rho_1(k)\\
N_{D_1}^{\max}(k)\\
N_{D_2}^{\max}(k)
\end{bmatrix}.
\]

其中：

- \(B_P\)：一个控制周期或调度轮次允许准入/处理的 Prefill token budget；
- \(C_P\)：chunked prefill 的最大单请求 chunk size；
- \(\rho_1\)：新完成 Prefill 请求路由到 D1 的目标比例，D2 比例为 \(1-\rho_1\)；
- \(N_{D_m}^{\max}\)：Decode worker 的最大活动序列数或可执行并发上限。

为使线性 DMDc 识别有效，控制量应数值标准化：

\[
\widetilde u_{k,j}
=
\frac{u_{k,j}-\mu_{u,j}}{\sigma_{u,j}}.
\]

### 6.2 外部请求到达扰动

将不可控的新请求流定义为 \(d_k\)。若输入长度划分为 \(N_L\) 个区间，定义：

\[
d_k=
\begin{bmatrix}
A_1(k),\ldots,A_{N_L}(k),
T_1(k),\ldots,T_{N_L}(k)
\end{bmatrix}^{\top},
\]

其中：

- \(A_i(k)\)：控制周期 \([t_k,t_{k+1})\) 内到达且输入长度属于第 \(i\) 个 bin 的请求数；
- \(T_i(k)\)：同一 bin 内到达的输入 token 总数。

还可拼接：

- `max_new_tokens` 的分布；
- TTFT/TPOT SLO 类别分布；
- prefix-cache hit/miss 到达量；
- 请求优先级分布。

将请求到达作为显式扰动，而不是仅依赖历史状态，可以区分系统内部演化和外部负载注入。

### 6.3 固定部署参数

模型类型、精度、TP 度、设备型号和 KV block size 作为一次 POC 资产的固定元数据 \(\mu\)，不随控制周期变化：

\[
\mu=
(	ext{model},\text{precision},TP_P,TP_D,
\text{device},\text{KV block size}).
\]

不同 \(\mu\) 对应不同的 POD–DMDc 资产版本。

---

## 7. 输出与性能指标

### 7.1 即时输出

定义控制周期内的输出向量：

\[
y_k=
\begin{bmatrix}
G_k\\
R_k\\
V_k^{TTFT}\\
V_k^{TPOT}\\
M_{D_1,k}^{KV}\\
M_{D_2,k}^{KV}\\
Q_{P,k}^{tokens}\\
Q_{D_1,k}^{work}\\
Q_{D_2,k}^{work}
\end{bmatrix}.
\]

其中：

- \(G_k\)：周期内完成且满足 SLO 的请求数或 token 数，即局部 goodput；
- \(R_k\)：拒绝请求数；
- \(V_k^{TTFT}\)：TTFT 已违约或预计 imminent violation 的请求量；
- \(V_k^{TPOT}\)：TPOT 已违约或 imminent violation 的活动请求量；
- \(M_{D_m,k}^{KV}\)：KV block 使用量；
- \(Q_P^{tokens}\)：Prefill 剩余 token 工作量；
- \(Q_D^{work}\)：Decode 估计剩余 token 工作量。

### 7.2 从 slack 分布线性提取 SLO 风险

若全阶状态已经包含 slack 直方图，则违约量可由固定线性算子获得。例如，设 \(c_P\) 在所有 \(s^P\le0\) 的 bin 上取 1，其他为 0，则：

\[
V_k^{TTFT}=c_P^{\top}x_k.
\]

对未来一个控制周期内可能违约的请求，可对 \(s^P\le\Delta t_c\) 的 bin 求和。Decode 同理：

\[
V_k^{TPOT}=c_D^{\top}x_k.
\]

该设计避免直接回归 p99，并使 MPC 的状态约束具有更清晰的物理含义。

### 7.3 周期指标与端到端指标的关系

控制器使用周期级输出做优化，最终实验仍需按请求报告：

- TTFT p50/p95/p99；
- TPOT p50/p95/p99；
- E2E latency；
- request goodput；
- output token throughput；
- SLO attainment；
- rejection rate；
- KV peak 和 worker imbalance。

---

## 8. 状态预处理与加权内积

### 8.1 中心化和缩放

不同状态块的数量级差异很大。例如请求数可能为十几，token 工作量为数万，KV 字节数可达 GB。直接 SVD 会让大数值块支配 POD。

定义训练集均值 \(\bar x\) 和对角尺度矩阵 \(S_x\)：

\[
\widehat x_k=S_x^{-1}(x_k-\bar x).
\]

推荐尺度选择：

- 对计数直方图使用训练集标准差或稳健尺度 IQR；
- 对 token/KV 质量使用容量归一化；
- 对比例变量使用固定 \([0,1]\) 尺度；
- 对长期为零的维度剔除或合并 bin。

### 8.2 加权内积

定义对角权重矩阵 \(W\succ0\)：

\[
\langle x_1,x_2\rangle_W=x_1^{\top}Wx_2.
\]

初始 POC 可按状态块分配等总权重。例如 Prefill waiting、Prefill slack、D1、D2、KV transfer 五个大块各获得相同总权重，再在块内均匀分配。这样能够防止某个高维块仅因 bin 数更多而支配 POD。

组合后使用：

\[
\widetilde x_k=W^{1/2}S_x^{-1}(x_k-\bar x).
\]

---

## 9. POD 降阶

### 9.1 快照矩阵

从完整训练轨迹中收集：

\[
X=
[\widetilde x_1,\widetilde x_2,\ldots,\widetilde x_M]
\in\mathbb R^{n\times M}.
\]

进行薄 SVD：

\[
X=U\Sigma V^{\top},
\qquad
\Sigma=\operatorname{diag}(\sigma_1,\ldots,\sigma_p).
\]

选择前 \(r\) 个左奇异向量：

\[
U_r=[u_1,\ldots,u_r].
\]

在标准化坐标中的低维状态为：

\[
z_k=U_r^{\top}\widetilde x_k.
\]

高维重构为：

\[
\widehat x_k=
\bar x+S_xW^{-1/2}U_rz_k.
\]

### 9.2 阶数选择

累计快照能量：

\[
E_r=
\frac{\sum_{i=1}^{r}\sigma_i^2}
{\sum_{i=1}^{p}\sigma_i^2}.
\]

POC 可以从满足 \(E_r\ge99\%\)、\(99.5\%\)、\(99.9\%\) 的候选阶数出发，但最终阶数由验证轨迹上的四类误差共同决定：

1. 全状态加权重构误差；
2. Prefill/Decode slack 分布重构误差；
3. KV 分布重构误差；
4. DMDc 多步 rollout 和闭环控制性能。

### 9.3 模态解释

对第 \(i\) 个 POD 模态 \(\phi_i=S_xW^{-1/2}u_i\)，按状态块计算模态质量：

\[
e_{i,b}=\|\phi_i^{(b)}\|_2^2.
\]

并观察模态正负结构与时间系数 \(z_i(t)\)。可能的解释包括：

- Prefill waiting 和 Decode active 同号增长：总负载模态；
- Prefill 减少、KV transfer 和 Decode 增加：阶段转移模态；
- D1 正、D2 负：Decode 失衡模态；
- 长上下文 KV bin 增长：KV 累积模态；
- 负 slack bin 增长：SLO 风险模态。

---

## 10. DMDc 低维受控动力学

### 10.1 仿射离散模型

第一代模型采用仿射线性 DMDc：

\[
z_{k+1}=A_rz_k+B_ru_k+E_rd_k+c_r+\varepsilon_k.
\]

将常数项并入扩展输入：

\[
\omega_k=
\begin{bmatrix}
z_k\\u_k\\d_k\\1
\end{bmatrix},
\qquad
z_{k+1}=K_r\omega_k+\varepsilon_k,
\]

其中

\[
K_r=[A_r\;B_r\;E_r\;c_r].
\]

### 10.2 训练矩阵

构造：

\[
Z_-=[z_1,z_2,\ldots,z_{M-1}],
\]

\[
Z_+=[z_2,z_3,\ldots,z_M],
\]

\[
\Omega_-=
\begin{bmatrix}
Z_-\\U_-\\D_-\\\mathbf 1^{\top}
\end{bmatrix}.
\]

通过正则化最小二乘求解：

\[
K_r=
\arg\min_K
\|Z_+-K\Omega_-\|_F^2
+\lambda_K\|K\|_F^2.
\]

闭式解为：

\[
K_r=Z_+\Omega_-^{\top}
(\Omega_-\Omega_-^{\top}+\lambda_K I)^{-1}.
\]

也可使用截断 SVD 伪逆，截断阈值和岭参数由完整验证轨迹选择。

### 10.3 控制激励与可辨识性

如果训练期间控制参数长期不变或高度相关，则无法区分 \(A_r\) 与 \(B_r\) 的作用。数据采集必须使：

\[
\operatorname{rank}(\Omega_-)
\]

足够高，并覆盖各控制量的主要范围、组合和瞬态。控制输入需要使用阶跃、分段常数随机序列或受约束伪随机二进制序列进行主动激励。

### 10.4 稳定性诊断

计算 \(A_r\) 的谱半径：

\[
\rho(A_r)=\max_i|\lambda_i(A_r)|.
\]

由于系统受持续到达扰动驱动，\(\rho(A_r)>1\) 不一定意味着识别错误，但在无到达、保守控制条件下，队列应具有排空趋势。建议构造“零到达恢复实验”，检验模型是否预测：

\[
d_k=0\quad\Rightarrow\quad
Q_P,Q_D,M^{KV}\text{ 随时间下降}.
\]

还应检查：

- 不同预测时域的状态范数是否无物理爆炸；
- 重构后请求数、token 和 KV 是否产生大量负值；
- D1/D2 对称实验是否得到近似对称响应；
- 控制方向是否符合基本单调性，例如更高 Prefill budget 在短期提高 Prefill 排空速率。

### 10.5 控制与观测诊断

对低维系统检查可控矩阵：

\[
\mathcal C=[B_r,A_rB_r,\ldots,A_r^{r-1}B_r],
\]

以及输出矩阵 \(C_r\) 的可观测矩阵：

\[
\mathcal O=
\begin{bmatrix}
C_r\\C_rA_r\\\vdots\\C_rA_r^{r-1}
\end{bmatrix}.
\]

POC 中不要求严格满秩，但应报告数值秩和奇异值，识别哪些低维方向无法被当前控制量影响，哪些状态方向与 SLO 输出弱相关。

---

## 11. 输出模型

### 11.1 线性输出映射

从低维状态预测输出：

\[
y_k=C_rz_k+D_ru_k+F_rd_k+b_y+\eta_k.
\]

若输出能够直接由重构状态线性计算，则优先使用物理定义：

\[
\widehat y_k=L_y\widehat x_k.
\]

例如 queue token、KV used blocks、负 slack 请求量均可由固定求和矩阵 \(L_y\) 得到。对于周期 goodput、拒绝数等流量输出，可单独拟合线性输出模型。

### 11.2 守恒与流量一致性检查

请求生命周期满足近似库存平衡：

\[
N_{\mathrm{system}}(k+1)
=
N_{\mathrm{system}}(k)
+N_{\mathrm{admit}}(k)
-N_{\mathrm{complete}}(k)
-N_{\mathrm{drop}}(k).
\]

Prefill、KV transfer 和 Decode 之间也满足阶段流量关系。虽然 DMDc 不显式强制守恒，但数据处理和模型评价应检查预测轨迹是否严重违反这些关系。可以将库存误差作为额外诊断：

\[
e_{\mathrm{mass}}(k)=
\widehat N_{\mathrm{system}}(k+1)
-
\widehat N_{\mathrm{system}}(k)
-N_{\mathrm{admit}}(k)
+\widehat N_{\mathrm{complete}}(k)
+N_{\mathrm{drop}}(k).
\]

---

## 12. ROM 多步预测

### 12.1 给定控制序列的 rollout

从实测状态投影得到 \(z_k\)，给定控制序列

\[
U_k=(u_k,u_{k+1},\ldots,u_{k+H-1})
\]

和扰动预测

\[
\widehat D_k=(\widehat d_k,\ldots,\widehat d_{k+H-1}),
\]

递推：

\[
\widehat z_{k+j+1}
=A_r\widehat z_{k+j}
+B_ru_{k+j}
+E_r\widehat d_{k+j}
+c_r.
\]

每一步得到：

\[
\widehat x_{k+j}
=\bar x+S_xW^{-1/2}U_r\widehat z_{k+j},
\]

以及 \(\widehat y_{k+j}\)。

### 12.2 扰动预测

第一代 POC 可比较三个朴素预测器：

1. Last value：\(\widehat d_{k+j}=d_{k-1}\)；
2. Moving average：最近 \(L\) 个周期均值；
3. Seasonal/trace-known replay：实验中已知未来到达轨迹，用作 oracle 上界。

通过 oracle 与非 oracle 的差异，可以区分 ROM 状态预测误差和 workload forecast 误差。

### 12.3 预测时域

若 \(\Delta t_c=200\) ms，可测试：

\[
H\in\{5,10,20,40\},
\]

即 1、2、4、8 秒的预测窗口。预测时域应覆盖至少一个明显的队列增长或恢复过程，同时保证线性模型 rollout 不被长期误差主导。

---

## 13. 线性 ROM-MPC

### 13.1 控制目标

MPC 的目标是在有限预测时域内提高 goodput，并抑制 TTFT/TPOT 风险、拒绝、KV 超载和控制抖动。

定义目标函数：

\[
\begin{aligned}
J_k=&\sum_{j=1}^{H}
\Big(
q_P\|\widehat V_{k+j}^{TTFT}\|_2^2
+q_D\|\widehat V_{k+j}^{TPOT}\|_2^2\\
&\qquad
+q_{KV}\|\widehat M_{k+j}^{KV}-M_{\mathrm{ref}}^{KV}\|_{+}^2
-q_G\widehat G_{k+j}
+q_R\widehat R_{k+j}
\Big)\\
&+\sum_{j=0}^{H-1}
\left(
\|u_{k+j}-u_{\mathrm{ref}}\|_{Q_u}^2
+\|u_{k+j}-u_{k+j-1}\|_{R_{\Delta u}}^2
\right).
\end{aligned}
\]

其中 \(\|a\|_+=\max(a,0)\)。如果所有输出和约束都使用线性映射，且正负部分通过松弛变量表达，该问题可以写成标准二次规划。

### 13.2 控制约束

控制边界：

\[
u_{\min}\le u_{k+j}\le u_{\max}.
\]

变化率约束：

\[
-\Delta u_{\max}
\le u_{k+j}-u_{k+j-1}
\le\Delta u_{\max}.
\]

路由比例：

\[
0\le\rho_1(k+j)\le1.
\]

KV 容量：

\[
\widehat M_{D_m,k+j}^{KV}
\le M_{D_m}^{KV,\max}-\epsilon_{KV}.
\]

SLO 风险软约束：

\[
\widehat V_{k+j}^{TTFT}\le\epsilon_P+\sigma_{P,j},
\quad \sigma_{P,j}\ge0,
\]

\[
\widehat V_{k+j}^{TPOT}\le\epsilon_D+\sigma_{D,j},
\quad \sigma_{D,j}\ge0,
\]

并对松弛变量设置高惩罚，避免优化不可行时无解。

### 13.3 Receding-horizon 执行

在时刻 \(t_k\)：

1. 读取实时遥测并构造 \(x_k\)；
2. 投影得到 \(z_k\)；
3. 预测未来扰动；
4. 求解 \(u_{k:k+H-1}^{\star}\)；
5. 只执行第一步 \(u_k^{\star}\)；
6. 在 \(t_{k+1}\) 使用真实状态重新初始化预测。

每周期的实测反馈能够持续纠正 ROM 的长期漂移。

### 13.4 整数参数处理

\(B_P,C_P,N_D^{\max}\) 是离散或整数参数。POC 可采用两种实现：

- 连续 QP 求解后投影到允许值集合；
- 枚举少量离散候选组合，对每个组合求解连续路由比例或直接计算目标。

由于控制维度很小，候选集合枚举通常足够快且易调试。

---

## 14. ServingROM 数字孪生插件架构

```text
┌──────────────────────────────────────────────────────────┐
│                  Real 1P2D Serving System                │
│                                                          │
│ Proxy ── Prefill ── KV transfer ── Decode D1 / Decode D2 │
└──────────────┬───────────────────────────────────────────┘
               │ telemetry/events
               ▼
┌──────────────────────────────────────────────────────────┐
│                ServingROM Sidecar / Service              │
│                                                          │
│ 1. Event Joiner & Clock Aligner                          │
│ 2. Full-order Snapshot Builder                           │
│ 3. POD Projector                                         │
│ 4. DMDc Forecaster                                       │
│ 5. Disturbance Forecaster                                │
│ 6. ROM-MPC Optimizer                                     │
│ 7. Control Validator & Actuator                          │
│ 8. Shadow/Closed-loop Logger                             │
└──────────────┬───────────────────────────────────────────┘
               │ control command
               ▼
┌──────────────────────────────────────────────────────────┐
│ Proxy / Scheduler Runtime Configuration                  │
│ B_P, C_P, routing ratio, D1/D2 max active sequences      │
└──────────────────────────────────────────────────────────┘
```

### 14.1 离线资产

一个可部署资产目录应包含：

```text
asset/
├── metadata.yaml
├── state_schema.json
├── bin_edges.json
├── state_mean.npy
├── state_scale.npy
├── state_weight.npy
├── pod_basis.npy
├── singular_values.npy
├── dmdc_A.npy
├── dmdc_B.npy
├── dmdc_E.npy
├── dmdc_c.npy
├── output_model.npz
├── mpc_config.yaml
└── validation_report.json
```

### 14.2 在线模块接口

```python
class FullOrderStateBuilder:
    def build(self, telemetry_window) -> np.ndarray:
        """将一个控制周期内的请求和 worker 遥测转换成固定维状态 x_k。"""

class PODProjector:
    def project(self, x: np.ndarray) -> np.ndarray:
        """x_k -> z_k。"""

    def reconstruct(self, z: np.ndarray) -> np.ndarray:
        """z_k -> x_hat_k。"""

class DMDcModel:
    def step(self, z, u, d) -> np.ndarray:
        """执行一步低维状态转移。"""

    def rollout(self, z0, U, D) -> np.ndarray:
        """返回有限时域低维轨迹。"""

class ROMMPCController:
    def solve(self, z0, disturbance_forecast, previous_u):
        """求解候选控制序列并返回第一步动作及预测轨迹。"""

class ControlActuator:
    def apply(self, u):
        """将控制参数写入 Proxy/调度器热更新接口。"""
```

---

## 15. 完整算法

### 15.1 离线训练算法

```text
输入：完整训练运行的事件日志与遥测
输出：POD–DMDc–MPC 资产

1. 对齐所有时间戳，按控制周期 Δt_c 划分窗口。
2. 对每个 t_k：
   2.1 重建系统中的 waiting/running/transferring/decoding 请求集合；
   2.2 构造 Prefill、KV transfer、D1、D2 分布直方图；
   2.3 拼接标量遥测，得到全阶状态 x_k；
   2.4 汇总周期内控制 u_k 和到达扰动 d_k；
   2.5 计算周期输出 y_k。
3. 仅使用训练轨迹估计状态均值、尺度和权重。
4. 对训练状态矩阵执行 POD，生成候选阶数 r。
5. 对每个 r 和正则参数 λ：
   5.1 投影训练状态得到 z_k；
   5.2 拟合 DMDc 矩阵 A_r,B_r,E_r,c_r；
   5.3 在验证轨迹上做开环多步 rollout；
   5.4 评价状态、SLO、KV 和库存一致性误差。
6. 选择满足预测精度和在线成本要求的资产。
7. 拟合或构造输出映射。
8. 配置 MPC 时域、权重、边界和离散动作集合。
9. 生成资产与验证报告。
```

### 15.2 在线控制算法

```text
每个控制周期 t_k：

1. State Builder 从事件流构造当前全阶状态 x_k。
2. 计算 z_k = POD.project(x_k)。
3. 根据最近到达数据生成未来 H 步扰动预测 D_hat。
4. MPC 调用 DMDc rollout 评估控制序列。
5. 求解目标函数，得到 U*。
6. 取第一步 u*_k，经运行边界校验后写入调度器。
7. 保存真实状态、预测轨迹、控制决策、求解时间和残差。
8. 下一个控制周期重新读取真实状态并重复。
```

---

## 16. Shadow mode 与闭环部署

### 16.1 Shadow mode

插件读取真实数据并运行完整 POD–DMDc–MPC，但不改变系统参数。每个周期记录：

- 当前全阶和低维状态；
- 未来 \(H\) 步预测；
- 建议控制动作；
- 实际固定控制动作；
- 下一周期真实状态；
- 单步和多步预测误差；
- QP 求解耗时。

Shadow mode 用于验证模型、动作范围和运行开销，并发现状态构造或时间对齐错误。

### 16.2 闭环模式

闭环时，控制动作通过热更新接口生效。需要记录：

- command issue time；
- worker acknowledge time；
- effective-from iteration；
- 实际生效值；
- 失败或延迟原因。

控制参数不是在发出命令时立即进入系统动力学，因此训练数据中的 \(u_k\) 应使用“实际生效参数”，而不是仅使用期望参数。

---

## 17. 模型评价

### 17.1 POD 重构

加权相对重构误差：

\[
e_{\mathrm{rec}}
=
\frac{
\left(\sum_k\|x_k-\widehat x_k\|_W^2\right)^{1/2}}
{
\left(\sum_k\|x_k-\bar x\|_W^2\right)^{1/2}}.
\]

同时按 Prefill、D1、D2、KV、slack 等状态块分别报告。

### 17.2 DMDc 单步误差

\[
e_{1}
=
\frac{
\left(\sum_k\|z_{k+1}-\widehat z_{k+1}\|_2^2\right)^{1/2}}
{
\left(\sum_k\|z_{k+1}-\bar z\|_2^2\right)^{1/2}}.
\]

### 17.3 多步 rollout

从测试轨迹中的真实状态初始化，使用真实未来控制和到达扰动进行 \(H\) 步 rollout：

\[
e_{H}^{x}
=
\frac{
\left(\sum_{j=1}^{H}\|x_{k+j}-\widehat x_{k+j}\|_W^2\right)^{1/2}}
{
\left(\sum_{j=1}^{H}\|x_{k+j}-\bar x\|_W^2\right)^{1/2}}.
\]

还应分别报告：

- Prefill token backlog MAE；
- D1/D2 active sequence MAE；
- KV block MAE；
- TTFT/TPOT risk count MAE；
- completion/goodput MAE；
- 预测峰值和峰值发生时间误差。

### 17.4 闭环评价

与相同 trace、相同初态和相同硬件上的策略比较：

1. 当前固定 1P2D 配置；
2. 基于阈值的反应式控制；
3. 单步性能模型或 myopic 搜索；
4. ServingROM-MPC；
5. 使用已知未来到达的 ROM-MPC oracle。

报告：

- request/token goodput；
- TTFT/TPOT SLO attainment；
- p50/p95/p99；
- rejection rate；
- D1/D2 generation token 差异；
- KV peak 和超限次数；
- 参数切换次数和总变化量；
- 控制决策开销；
- 高负载恢复时间。

---

## 18. 关键消融实验

### 18.1 状态表示消融

比较：

- 仅聚合标量；
- 长度直方图；
- 长度–年龄二维分布；
- 长度–slack 二维分布；
- 完整 ServingROM 状态。

目标是证明降阶前的高维状态表示确实提供了多步可预测信息。

### 18.2 POD 阶数消融

比较多个 \(r\)，绘制：

- 累计能量；
- 重构误差；
- H-step rollout；
- MPC 求解时间；
- 闭环 goodput/SLO。

### 18.3 控制输入消融

依次启用：

- 仅 Prefill token budget；
- 加 chunk size；
- 加 D1/D2 routing；
- 加 Decode concurrency。

观察各控制通道的边际收益和可控性。

### 18.4 扰动信息消融

比较：

- 无显式 \(d_k\)；
- 只使用到达请求数；
- 使用长度分布；
- 使用长度和 SLO 分布。

### 18.5 时域与采样周期消融

联合测试 \(\Delta t_c\) 和 \(H\)，识别实时开销、短期可预测性和控制效果之间的折中。

---

## 19. 常见失败模式与诊断

### 19.1 POD 能量高但 SLO 预测差

原因可能是高方差模态主要描述总负载，而 slack 边界附近的低方差方向被截断。先检查每个状态块的权重和缩放，再增加阶数，避免直接归因于 DMDc。

### 19.2 单步准确但 rollout 漂移

检查：

- \(A_r\) 谱半径；
- 输入时间对齐；
- 实际生效控制与日志控制是否错位；
- 请求到达是否使用了 \([t_k,t_{k+1})\) 的正确区间；
- 状态是否缺少剩余服务和年龄信息；
- 训练激励是否覆盖瞬态。

### 19.3 重构出现负请求数或负 KV

线性 POD 允许局部负值。评价时可保留原始线性重构用于误差计算，输出到控制器前对物理量做非负投影：

\[
\widehat x^{\mathrm{phys}}=\max(\widehat x,0).
\]

如果负值大量出现，说明阶数、中心化或线性子空间不足。

### 19.4 控制参数频繁抖动

增加 \(R_{\Delta u}\)、变化率约束和最小保持周期；检查控制周期是否小于系统响应时间。

### 19.5 D1/D2 路由控制无效

检查路由命令到实际请求分配之间的延迟，以及控制训练数据中 \(\rho_1\) 是否具有足够变化。仅记录目标比例而不记录实际路由结果，会导致错误辨识。

### 19.6 高负载下模型突然失效

检查训练数据是否覆盖接近容量边界、429 准入拒绝、KV 高水位和 Decode 饱和区间。DMDc 只能在已有激励和状态覆盖范围内可靠工作。

---

## 20. POC 成功判据

第一代算法的 POC 成功不要求一次达到最终论文效果，但应至少证明以下链路成立：

1. 高维请求分布快照存在显著奇异值衰减；
2. 中等阶数 POD 能保留主要 queue/KV/slack 输出；
3. DMDc 在独立完整测试轨迹上具有可用的 1–5 秒多步预测能力；
4. ROM rollout 和 MPC 求解开销显著小于控制周期；
5. Shadow mode 下建议动作与真实未来风险具有一致方向；
6. 闭环运行中，ServingROM-MPC 相比固定配置至少在部分动态负载上提高 goodput 或 SLO attainment，且不会导致系统性过载；
7. 前几个 POD 模态能够给出合理的系统解释。

建议的工程验收门槛将在配套的《ServingROM 第一代 POC 实施与数据采集规范》中具体给出。

---

## 21. 预期研究贡献表达

若 POC 成立，方法层面的贡献可概括为：

1. **分布场式 serving state**：将变长请求集合表示为输入长度、等待年龄、deadline slack、上下文长度、生成进度和 KV 占用上的高维离散场；
2. **经典数据驱动降阶动力系统**：通过 POD–DMDc 将高维服务状态压缩为受调度参数和请求到达驱动的低维状态空间模型；
3. **实时 Reduced-Order Digital Twin**：低维模型伴随真实 1P2D 系统运行，执行多步状态 rollout；
4. **ROM-MPC 调度**：在低维动力学上联合优化 Prefill budget、chunk、Decode 路由和并发参数；
5. **低维结构实证**：分析 LLM serving 的主导动力模态及其与阶段压力转移、KV 累积和 SLO 风险之间的关系。

---

## 22. 参考文献

1. J. L. Proctor, S. L. Brunton, and J. N. Kutz, “Dynamic Mode Decomposition with Control,” *SIAM Journal on Applied Dynamical Systems*, 15(1), 142–161, 2016. DOI: `10.1137/15M1013857`.
2. L. Sirovich, “Turbulence and the Dynamics of Coherent Structures. Part I: Coherent Structures,” *Quarterly of Applied Mathematics*, 45(3), 1987.
3. P. Holmes, J. L. Lumley, G. Berkooz, and C. W. Rowley, *Turbulence, Coherent Structures, Dynamical Systems and Symmetry*, Cambridge University Press.
4. P. Benner, S. Gugercin, and K. Willcox, “A Survey of Projection-Based Model Reduction Methods for Parametric Dynamical Systems,” *SIAM Review*, 57(4), 483–531, 2015.
5. A. Marquez, J. J. Espinosa Oviedo, and D. Odloak, “Model Reduction Using Proper Orthogonal Decomposition and Predictive Control of Distributed Reactor System,” *Journal of Control Science and Engineering*, 2013.
6. J. Lorenzetti, A. McClellan, C. Farhat, and M. Pavone, “Linear Reduced Order Model Predictive Control,” arXiv:`2012.03384`.
7. O. Basit, Y. Liu, Z. J. Kong, and Y. C. Hu, “BiScale: Energy-Efficient Disaggregated LLM Serving via Phase-Aware Placement and DVFS,” arXiv:`2602.18755`, 2026.
8. Y. Zhang et al., “A Predictive and Synergistic Two-Layer Scheduling Framework for LLM Serving,” arXiv:`2509.23384`, 2025.
9. A. Agrawal et al., “Taming the Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve,” *OSDI*, 2024.
10. Y. Zhong et al., “DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving,” *OSDI*, 2024.

