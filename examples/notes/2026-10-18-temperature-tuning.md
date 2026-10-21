---
date: "2026-10-18"
topic: "生成采样 Temperature 极值测试"
tags: ["hyperparameter", "temperature"]
---
# 实验记录：生成采样 Temperature 极值测试

## 实验改动
- 将 temperature 从 0.3 提升至 0.9；
- top_p 保持 0.95；
- 测试在代码生成和正则生成任务下的表现。

## 实验结果
- 创意性生成任务多样性丰富，但在复杂 Python 语法生成时语法错误率（SyntaxError）激增 24%；
- 测试集代码一次性通过率（Pass@1）从 84% 跌落至 59%。

## 结论与决策
放弃。高 Temperature 对严谨代码生成任务造成严重负面影响，代码辅助场景必须锁定在低温区间 (0.0 ~ 0.2)。
