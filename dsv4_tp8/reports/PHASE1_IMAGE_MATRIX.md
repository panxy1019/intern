# 第一阶段镜像矩阵

## Ray Head

```text
tag: 110.120.0.3:8889/ds/ray-head:py312-ray2.49.0-amd64-20260806
digest: sha256:4a4788e419952373e42e0dc104fea5238d8c7ec353c9c4f72fdb707967769cb2
architecture: amd64
python: 3.12
ray: 2.49.0
```

## DeepSeek-V4 Worker

```text
tag: 110.120.0.3:8889/ds/dsv4-vllm-ascend:v0.22.1rc1-ray2.49.0-arm64-20260806
digest: sha256:e29d1493cbe3571f1200c8b99778ab533f8396eb447a0acf78f742c0a53fc008
architecture: arm64
python: 3.12
ray: 2.49.0
vllm: 0.22.1+empty
vllm-ascend: 0.22.1rc1
torch: 2.10.0
torch-npu: 2.10.0
CANN: 9.0.0
```

Worker 只替换了 Ray wheel；vLLM、vLLM-Ascend、PyTorch、torch-npu 和
CANN 沿用已验证基础镜像。完整 `torch_npu` 导入测试必须在挂载宿主机
Ascend driver 的 Worker Pod 中执行。
