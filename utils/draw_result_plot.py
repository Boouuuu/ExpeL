import re
import sys
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def parse_log(text):
    """
    解析日志，返回：
        results: {task_id: {reflection_round: 'correct'/'incorrect'}}
        同时返回所有出现的 task_id 集合（用于缺失检查）
    """
    results = {}
    all_task_ids = set()

    blocks = re.split(r'#######################################', text)

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

        all_task_ids.add(task_id)  # 记录所有出现的任务ID

        if ref_round >= 3:
            print(f"⚠️ 任务 {task_id} 的反思轮次 {ref_round} 超过预期范围，已跳过")
            continue

        correct_pos = block.rfind('Answer is CORRECT')
        incorrect_pos = block.rfind('Answer is INCORRECT')

        if correct_pos == -1 and incorrect_pos == -1:
            print(f"⚠️ 任务 {task_id} 的反思轮次 {ref_round} 未找到正确/错误标记")
            result = 'unknown'

        elif correct_pos > incorrect_pos:
            result = 'correct'
        else:
            result = 'incorrect'

        results.setdefault(task_id, {})[ref_round] = result

    return results, all_task_ids


def compute_statuses(results):
    """根据正确/错误记录生成每轮的状态序列（success/fail/halted）"""
    statuses = {}

    for task_id, ref_results in results.items():
        seq = [''] * 3
        for ref, res in ref_results.items():
            if ref < 3:
                seq[ref] = res

        status_seq = []
        for r in range(3):
            if seq[r] == 'correct':
                status_seq.append('success')
            elif seq[r] == 'incorrect':
                status_seq.append('fail')
            elif 'success' in status_seq:
                status_seq.append('success')
            else:
                status_seq.append('halted')

        statuses[task_id] = status_seq

    return statuses


def main():
    

    log_file = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\logs\math2code_math\expel\run-glm-2k.txt"

    with open(log_file, 'r', encoding='utf-8') as f:
        log_text = f.read()

    # 解析日志
    results, all_task_ids = parse_log(log_text)

    # 检查缺失的题目（预期 0~1049）
    expected_ids = set(range(1050))
    missing = expected_ids - all_task_ids

    if missing:
        print(f"⚠️ 缺失的题目 ID（共 {len(missing)} 个）: {sorted(missing)}")
    else:
        print("✅ 所有 0~1049 题目均存在")

    # 统计状态
    statuses = compute_statuses(results)
    total_tasks = len(statuses)
    print(f"解析到有效状态的题目数: {total_tasks}")

    success_counts = []
    fail_counts = []
    halted_counts = []

    for r in range(3):
        sc = fc = hc = 0
        for task_id, seq in statuses.items():
            if seq[r] == 'success':
                sc += 1
            elif seq[r] == 'fail':
                fc += 1
            elif seq[r] == 'halted':
                hc += 1

        # 每轮三类数量之和应等于有效题目数
        if sc + fc + hc != total_tasks:
            print(f"警告：第 {r} 轮统计不匹配 (sum={sc+fc+hc}, expected={total_tasks})")
        success_counts.append(sc)
        fail_counts.append(fc)
        halted_counts.append(hc)

    # 绘制折线图
    rounds = [0, 1, 2]
    plt.plot(rounds, success_counts, marker='o', label='success')
    plt.plot(rounds, fail_counts, marker='o', label='fail')
    plt.plot(rounds, halted_counts, marker='o', label='halted')

    plt.xlabel('反思轮次')
    plt.ylabel('题目数量')
    plt.title('各反思轮次后的题目状态分布')
    plt.legend()
    plt.grid(True)

    plt.xticks(rounds)

    # 标注数值
    for x, y in zip(rounds, success_counts):
        plt.text(x, y + 0.1, str(y), ha='center', va='bottom', fontsize=10)
    for x, y in zip(rounds, fail_counts):
        plt.text(x, y + 0.1, str(y), ha='center', va='bottom', fontsize=10)
    for x, y in zip(rounds, halted_counts):
        plt.text(x, y + 0.1, str(y), ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()