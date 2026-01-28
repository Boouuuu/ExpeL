# Math2Code - 数学到代码的知识迁移

## 概述

Math2Code 基于 ExpeL 实现**数学 → 代码**的知识迁移：  
**训练阶段**用纯数学题（Thought / Reason / Calculate / Finish），保存做题轨迹；  
**见解提取**从数学轨迹中抽取规则；  
**评估阶段**用编程题（Analyze / Translate / Finish）评估迁移效果。

## 流程

1. **Train（数学题）**：`benchmark=math2code_math`，数据 `train_tasks.json`，Agent 解数学题并保存轨迹。  
2. **Insight extraction**：`benchmark=math2code_math`，从数学轨迹提取见解，保存到 `extracted_insights`。  
3. **Eval（编程题）**：`benchmark=math2code`，数据 `eval_tasks.json`，加载见解后在代码题上评估。

## 数据文件

| 文件 | 用途 | 格式 |
|------|------|------|
| `train_tasks.json` | 训练：纯数学题 | `question`, `key` |
| `eval_tasks.json` | 评估：编程题 | `question`, `key`, `test_cases`（可选） |

## Action 类型

### 训练（数学）`math2code_math`

- **Reason[step]**：推理步骤（代数、逻辑等），无计算。  
- **Calculate[expression]**：计算数值表达式，如 `10/2`、`2+3`。  
- **Finish[answer]**：给出最终答案并结束。

### 评估（代码）`math2code`

- **Analyze[concept]**：分析数学概念。  
- **Translate[pattern]**：对应到代码模式。  
- **Verify[code]**（可选）：验证代码片段。  
- **Finish[code]**：给出最终代码并结束。

## 使用示例

### 1. 训练（数学题）

```bash
python train.py benchmark=math2code_math agent_type=react run_name=run testing=false resume=false > &run-train.log &
# 或 agent_type=expel 做 reflection / 规则提取
```

轨迹保存在 `logs/math2code_math/<agent>/run.pkl` 等。

### 2. 见解提取（从数学轨迹）

```bash
python insight_extraction.py benchmark=math2code_math load_run_name=run run_name=insights-run agent.llm=gpt-4 ...
```

见解保存在 `logs/math2code_math/<agent>/extracted_insights/insights-run.pkl`。

### 3. 评估（编程题）

从**数学见解**所在目录加载，在**代码题**上评估：

```bash
python eval.py benchmark=math2code \
  load_log_path=logs/math2code_math/expel/extracted_insights \
  load_run_name=insights-run run_name=eval-run \
  agent.fewshot_strategy=task_similarity testing=false
```

`load_log_path` 指向见解目录，`load_run_name` 为 run 名（对应 `insights-run.pkl` 等）。

## 配置文件

- `configs/benchmark/math2code_math.yaml`：训练用，`task_file: data/math2code/train_tasks.json`。  
- `configs/benchmark/math2code.yaml`：评估用，`task_file: data/math2code/eval_tasks.json`。

## 注意事项

- 训练**仅数学**，无编程、无维基等外部 API。  
- 评估使用代码执行验证；注意运行环境与超时设置。  
- `plot_trial_stats` 等对非 alfworld 的 `len(parsed_result)==100` 断言已放宽，支持 math2code / math2code_math 的任务数。
