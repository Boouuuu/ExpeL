import re
import json
from pathlib import Path

LOG_PATH = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\logs\math2code_math\expel\run-glm-2k.txt"
DATA_PATH = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\data\math2code\math_train_tasks_1750.json"

def parse_log(log_path):
    """解析日志，返回每个任务的最终状态和相关信息"""
    with open(log_path, 'r', encoding='utf-8') as f:
        text = f.read()

    blocks = re.split(r'#######################################', text)
    task_info = {}

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 提取任务编号和反思轮次
        m = re.search(r'TASK (\d+) Reflection (\d+)', block)
        if not m:
            continue
        task_id = int(m.group(1))
        ref_round = int(m.group(2))

        # 提取问题（只存第一个出现的问题，但所有块中的问题应该一致）
        q_match = re.search(r'Question:\s*(.+?)(?=\nThought|\nAction|$)', block, re.DOTALL)
        question = q_match.group(1).strip() if q_match else None

        # 提取模型最终答案（从最后一个 Finish 中提取）
        finish_matches = re.findall(r'Action \d+: Finish\[(.*?)\]', block, re.DOTALL)
        model_answer = finish_matches[-1].strip() if finish_matches else None

        # 判断最终结果
        if 'Answer is CORRECT' in block:
            result = 'CORRECT'
        elif 'Answer is INCORRECT' in block:
            result = 'INCORRECT'
        else:
            result = None
        
        

        # 更新该任务的信息（最后一个块覆盖之前的）
        task_info[task_id] = {
            'question': question,
            'model_answer': model_answer,
            'result': result,
            'ref_round': ref_round
        }

    return task_info

def load_dataset(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    # 加载数据集
    dataset = load_dataset(DATA_PATH)
    print(f"数据集条目数: {len(dataset)}")

    # 解析日志
    task_info = parse_log(LOG_PATH)
    print(f"日志中解析到的任务数: {len(task_info)}")

    # 收集错误的任务
    incorrect_tasks = []
    for tid, info in task_info.items():
        if info['result'] == 'INCORRECT':
            # 从数据集中获取标准答案，假设顺序一致
            if tid < len(dataset):
                std_answer = dataset[tid].get('key', 'N/A')
                question = dataset[tid].get('question', info['question'])
            else:
                std_answer = 'N/A (超出数据集范围)'
                question = info['question']

            incorrect_tasks.append({
                'task_id': tid,
                'question': question,
                'model_answer': info['model_answer'],
                'std_answer': std_answer,
                'ref_round': info['ref_round']
            })

    # 打印结果
    print(f"\n共找到 {len(incorrect_tasks)} 个错误题目\n")
    print("=" * 100)
    for idx, item in enumerate(incorrect_tasks, 1):
        print(f"【错误 #{idx}】 Task {item['task_id']} (反思轮次: {item['ref_round']})")
        print(f"问题: {item['question']}")
        print(f"模型答案: {item['model_answer']}")
        print(f"标准答案: {item['std_answer']}")
        print("-" * 100)

if __name__ == '__main__':
    main()