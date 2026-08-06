# DeepSeek-V4 Flash TP8 启动验证报告

时间：2026-08-06 UTC

## 结论

首轮 DeepSeek-V4-Flash-0731 W8A8 单 Pod TP8 + EP8 服务启动成功。服务监听
`0.0.0.0:8900`，`/health` 返回 HTTP 200，`/v1/models` 返回指定模型；两次相同的
temperature=0、seed=0 短 completion 返回完全一致。

## 固定拓扑

- Worker Pod：`dsv4-tp8-worker-fixed-2-9-5f4666d85c-wm5bc`
- 宿主机固定 NPU：Phy-ID `2..9`
- 容器设备节点：`/dev/davinci2` 至 `/dev/davinci9`
- 容器 runtime ID：`0..7`
- Ray 资源：`CPU=192`、`NPU=8`、`dsv4_worker=1`
- 服务模型名：`DeepSeek-V4-Flash-0731-w8a8`

## 启动配置

- `--distributed-executor-backend mp`
- `--tensor-parallel-size 8`
- `--data-parallel-size 1`
- `--enable-expert-parallel`
- `--quantization ascend`
- `--max-model-len 131072`
- `--max-num-seqs 1`
- `--max-num-batched-tokens 4096`
- `--gpu-memory-utilization 0.88`
- `--block-size 128`，DeepSeek-V4 后端实际调整为 32
- `--enforce-eager`
- `--safetensors-load-strategy prefetch`

## 启动观测

- 8 个 HCCL rank 均加入 world size 8；未出现 HCCL timeout。
- Expert Parallelism：每 rank 32 个 local experts，共 256 个 global experts。
- 74/74 个 safetensors 分片加载完成，加载总耗时约 99.28 秒。
- 每 rank 权重占用 36.0576 GiB。
- 引擎 KV cache 计算为 709,938 tokens，当前每卡约 15.59 GiB KV cache。
- 引擎 profile、KV cache 创建及 warmup 约 27.42 秒。
- 服务就绪后 Phy-ID 2..9 HBM 约 57.6 GiB/卡。

## 验证边界

本轮验证的是基础可用性与联合推理路径，不是吞吐或质量基准。模型 tokenizer 未发现
内置 chat template，故原始 `/v1/completions` 文本仅作为确定性连通性检查，不能用来
评价对话语义质量。

## 运维入口

参见 `docs/TP8_VLLM_启动与控制指南.md`：使用 `start-vllm-tp8.sh`、
`status-vllm-tp8.sh` 与 `stop-vllm-tp8.sh` 控制实例；参数在
`k8s/26-vllm-control-config.yaml` 中维护。
