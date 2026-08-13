# PIQA / HellaSwag 全量 Bad Case 分析

## 文件

- [PIQA_BAD_CASES_ALL.md](PIQA_BAD_CASES_ALL.md)：PIQA 全量 bad case 表，共 787 条。
- [HELLASWAG_BAD_CASES_ALL.md](HELLASWAG_BAD_CASES_ALL.md)：HellaSwag 全量 bad case 表，共 8106 条。
- [PIQA_BAD_CASES_ALL.xlsx](PIQA_BAD_CASES_ALL.xlsx)：PIQA Excel 版本。
- [HELLASWAG_BAD_CASES_ALL.xlsx](HELLASWAG_BAD_CASES_ALL.xlsx)：HellaSwag Excel 版本。
- `*.summary.json`：便于程序读取的计数和一致性校验结果。

## 口径

Bad case 使用 `acc=0` 或 `acc_norm=0` 的并集，而不是只取两个指标同时错误的样本。每一行都包含：

1. 错误类型；
2. 完整题干和全部候选；
3. 正确答案、`acc` 答案、`acc_norm` 答案和逐候选分数；
4. 规则初筛得到的可能原因。

LightEval 0.9.2 的 `acc_norm` 在这两个任务中采用字符长度归一化。PIQA 会忽略 continuation 开头的一个空格；HellaSwag 使用完整候选字符数。生成时已逐题对照 parquet 内的官方 `metrics.acc` 和 `metrics.acc_norm`，两个任务均为：

```text
skipped_rows = 0
metric_mismatch_count = 0
```

## 汇总

| 数据集 | 总样本 | Bad case 并集 | acc 与 acc_norm 均错 | 仅 acc 错 | 仅 acc_norm 错 |
|---|---:|---:|---:|---:|---:|
| PIQA | 1838 | 787 | 417 | 188 | 182 |
| HellaSwag | 10042 | 8106 | 4914 | 1879 | 1313 |

错误类型和可能原因由确定性规则生成，适合做第一轮聚类、筛选和统计；涉及语义歧义、数据集标注争议或具体模型机制的结论仍需人工复核。

## 重新生成

生成器位于 `analysis/generate_full_badcase_tables.py`。示例：

```bash
python analysis/generate_full_badcase_tables.py \
  --dataset piqa \
  --details /path/to/details_lighteval-piqa.parquet \
  --output results/badcase-full/PIQA_BAD_CASES_ALL.md

python analysis/generate_full_badcase_tables.py \
  --dataset hellaswag \
  --details /path/to/details_leaderboard-hellaswag.parquet \
  --output results/badcase-full/HELLASWAG_BAD_CASES_ALL.md
```
