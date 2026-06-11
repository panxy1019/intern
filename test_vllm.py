import time
from typing import Any, Dict
import os
import ray
import pandas as pd

# ======================================================
# 每个 Actor 持有一个 vLLM Engine
# ======================================================
class VLLMEmbeddingPredictor:

    def __init__(self):
        from vllm import LLM
        import os
        print("🚀 初始化 vLLM Engine...")

        self.llm = LLM(
            model="/tmp/ms_cache/qwen/Qwen2-0___5B",
            task="embed",
            trust_remote_code=True,
            # 关键修改 1：关闭 eager 模式，让底层走图编译（Graph Mode），极大降低框架调度开销
            enforce_eager=False,
            max_model_len=512,
            gpu_memory_utilization=0.9,
            enable_chunked_prefill=False,
            # 关键修改 2：显式放大最大序列数和 Token 数，防止被 vLLM 内部调度器过早截断
            max_num_seqs=64,
            max_num_batched_tokens=65536,
        )

    def __call__(self, batch: Any) -> Dict[str, list]:
        import numpy as np
        texts = batch["text"].tolist()

        outputs = self.llm.embed(texts)

        # vLLM embed 输出
        embeddings = [x.outputs.embedding for x in outputs]
        return {
            "text": texts,
            "embedding": np.array(embeddings, dtype=np.float32),
        }

# ======================================================
# Main
# ======================================================
def main():

    ray.init(
        address="auto",
        runtime_env={
            "env_vars": {
                "LD_LIBRARY_PATH": (
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/hccl/lib64:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/aarch64-linux/lib64:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/fwkacllib/lib64:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/tools/aml/lib64:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/tools/aml/lib64/plugin:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64/plugin/opskernel:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/lib64/plugin/nnengine:"
                    "/usr/local/Ascend/cann/ascend-toolkit/8.3.RC1/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64:"
                    "/usr/local/Ascend/driver/lib64/driver:"
                    "/usr/local/Ascend/driver/lib64/common:"
                    "/usr/local/Ascend/driver/lib64:"
                    "/usr/local/Ascend/cann/nnal/atb/8.3.RC1/atb/cxx_abi_1/lib:"
                    "/usr/local/lib"
                )
            }
        },
    )
    print("=" * 60)
    print("Connected!")
    print(ray.available_resources())
    print("=" * 60)

    # --------------------------------------------------
    # 生成测试数据：使用 200 - 400 Tokens 长度的真实业务文本
    # --------------------------------------------------
    # 这段背景文本字数在 300 字左右，包含大量专业术语，非常适合测试 Embedding 模型的真实负载
    base_text = (
        "在计算流体力学（CFD）的实际工程应用中，高保真度的数值模拟通常面临着极高的计算成本，难以满足实时预测与多参数设计优化等场景的需求。"
        "为了克服这一瓶颈，降阶模型逐渐成为研究热点。传统方法通过在空间域提取能量主导的基函数，并将高维偏微分方程投影到低维子空间中来减少自由度。然而，"
        "传统的 Galerkin 投影方法在处理具有强对流主导或高度非线性演化的复杂流场时，往往会遇到稳定性和精度下降的问题。近年来，将深度学习与传统降阶方法"
        "相融合成为一种极具潜力的范式。例如，采用概率流形分解（PMD）架构，不仅能够突破线性子空间的表达限制，还能显著提升模型对未见工况的外推能力。"
        "在这种混合驱动的计算框架下，AI 模型可以直接代理复杂的非线性项演化，或者作为闭包模型修正截断误差，从而在保持物理可解释性的同时，实现数量级级别的加速。"
        "本条测试数据的唯一标识符为："
    )

    num_records = 1000000

    # 将 base_text 与 index 拼接，确保每条数据既足够长，又有唯一性
    dataset = ray.data.from_items(
        [{"text": f"{base_text} {i:06d}"} for i in range(num_records)],
        override_num_blocks=16,
    )

    print("Dataset Ready.")

    start = time.time()

    # --------------------------------------------------
    # 分布式 Embedding
    # --------------------------------------------------
    embedded = dataset.map_batches(
        VLLMEmbeddingPredictor,
        batch_format="pandas",
        concurrency=23,       # 每张卡一个 Actor
        batch_size=1024,      # 每批大小，保持大 Batch 以打满 NPU
        resources={"NPU": 1},
    )




    total = embedded.count()
    elapsed = time.time() - start

    print("=" * 60)
    print(f"Total Rows : {total}")
    print(f"Elapsed    : {elapsed:.2f}s")
    print(f"Throughput : {total/elapsed:.2f} req/s")
    print("=" * 60)

if __name__ == "__main__":
    main()