# Math2Code - 数学到代码的知识迁移

## 概述

Math2Code是基于ExpeL框架实现的数学领域到代码领域的知识迁移任务。它借鉴了HotpotQA的ReAct（Reasoning + Acting）思路，通过Thought-Action-Observation循环将数学概念翻译成代码实现。

## 文件结构

```
prompts/
  └── math2code.py          # Math2Code的prompt定义（fewshots, instructions等）

envs/
  └── math2code/
      ├── __init__.py
      └── math2code.py       # Math2Code环境实现

configs/
  └── benchmark/
      └── math2code.yaml     # Math2Code配置文件

data/
  └── math2code/
      └── tasks.json         # 任务数据文件
```

## Action类型

Math2Code定义了以下Action类型：

1. **Analyze[mathematical_concept]** - 分析数学概念，理解其定义、性质和计算要求
2. **Translate[code_pattern]** - 识别与数学概念对应的代码模式或结构
3. **Verify[code_snippet]** - 验证代码片段是否正确实现了数学概念（可选）
4. **Finish[code]** - 提供最终的代码实现并完成任务

## 使用方法

### 1. 准备数据

编辑 `data/math2code/tasks.json`，添加你的任务：

```json
[
    {
        "question": "你的数学问题描述",
        "key": "期望的代码实现",
        "test_cases": [
            {"input": ..., "expected": ...}
        ]
    }
]
```

### 2. 运行训练

```bash
python train.py benchmark=math2code agent_type=react run_name=math2code-run
```

### 3. 运行评估

```bash
python eval.py benchmark=math2code load_run_name=math2code-run run_name=eval-run
```

## 特点

- **无需外部API**：不依赖维基百科等外部API，使用本地代码执行环境
- **代码验证**：通过实际执行代码来验证实现的正确性
- **ReAct框架**：保留Thought-Action-Observation的推理步骤
- **可扩展**：易于添加新的数学概念和代码模式

## 自定义

### 修改Few-shot示例

编辑 `prompts/math2code.py` 中的 `FEWSHOTS` 列表，添加你的示例。

### 修改Action类型

在 `prompts/math2code.py` 的 `SYSTEM_INSTRUCTION` 中修改Action类型定义。

### 增强代码验证

在 `envs/math2code/math2code.py` 的 `success_fn()` 方法中添加更复杂的验证逻辑，例如：
- 运行测试用例
- 检查代码复杂度
- 验证代码风格

## 示例任务

当前包含的示例任务：
- 阶乘递归实现
- 矩阵乘法
- 二分查找
- 欧几里得算法（GCD）
- 斐波那契数列（动态规划）
- 质数判断

## 注意事项

- 代码执行环境需要Python环境
- 出于安全考虑，代码执行有超时限制（5秒）
- 建议在隔离环境中运行代码执行功能
