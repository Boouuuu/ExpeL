import re
import pickle
from typing import List, Dict, Callable, Optional
from copy import deepcopy

# ======================== Trajectory 类定义（按用户提供）========================
class Trajectory:
    def __init__(
        self,
        task: str,
        trajectory: str,
        splitter: Callable,
        identifier: Callable,
        step_splitter: Callable,
        embedder: Optional[Callable] = None,
        reflections: List[str] = None
    ):
        self._task = task
        self._trajectory = trajectory
        self._reflections = deepcopy(reflections) if reflections else []
        self._observations, self._actions, self._thoughts = [], [], []
        for line in splitter(self._trajectory):
            setattr(self, f'_{identifier(line)}s', getattr(self, f'_{identifier(line)}s') + [line])
        self._steps = step_splitter(lines=trajectory, cycler=splitter, step_identifier=identifier)
        self._keys = {'thought': [], 'step': []}
        if embedder is not None:
            self._keys['task'] = [embedder(self.task)]
            for step in self.steps:
                self._keys['step'].append(embedder(step))
            for thought in self.thoughts:
                self._keys['thought'].append(embedder(thought))

    @property
    def task(self) -> str:
        return self._task

    @property
    def steps(self) -> List[str]:
        return self._steps

    @property
    def trajectory(self) -> str:
        return self._trajectory

    @property
    def num_steps(self) -> int:
        return max(len(self.thoughts), len(self.actions), len(self.observations))

    @property
    def observations(self) -> List[str]:
        return self._observations

    @property
    def actions(self) -> List[str]:
        return self._actions

    @property
    def thoughts(self) -> List[str]:
        return self._thoughts

    @property
    def reflections(self) -> List[str]:
        return self._reflections

    @property
    def keys(self) -> Dict[str, List[float]]:
        return self._keys

    def _replace(self, attr, value):
        self.__setattr__(self, attr, value)


# ======================== 辅助函数（由用户提供）========================
def CYCLER(lines: str) -> List[str]:
    new_lines = []
    scratch_pad = ''
    for line in lines.split('\n'):
        if re.compile(r'^(?i)action(?:\s+(\d+))?:').match(line):
            if scratch_pad:
                new_lines.append(scratch_pad.strip())
                scratch_pad = ''
            new_lines.append(line)
            continue
        if re.compile(r'^(?i)thought(?:\s+(\d+))?:').match(line):
            if scratch_pad:
                new_lines.append(scratch_pad.strip())
                scratch_pad = ''
            new_lines.append(line)
            continue
        scratch_pad += line + '\n'
    if scratch_pad:
        new_lines.append(scratch_pad.strip())
    return new_lines


def STEP_IDENTIFIER(line: str) -> str:
    line = line.strip()
    if re.compile(r'^(?i)action(?:\s+(\d+))?:').match(line):
        return 'action'
    if re.compile(r'^(?i)observation(?:\s+(\d+))?:').match(line):
        return 'observation'
    return 'thought'


# 自定义 step_splitter，适配 Trajectory 的调用签名 (lines, cycler, step_identifier)
def step_splitter(lines: str, cycler: Callable, step_identifier: Callable) -> List[str]:
    steps = []
    scratch = ''
    for line in cycler(lines):
        step_type = step_identifier(line)
        scratch += line + '\n'
        if step_type == 'observation':
            steps.append(scratch.strip())
            scratch = ''
    if scratch:
        steps.append(scratch.strip())
    return steps


# ======================== 日志解析 ========================
def parse_log(log_path: str):
    with open(log_path, 'r', encoding='utf-8') as f:
        text = f.read()

    blocks = re.split(r'#######################################', text)
    # 每个任务的所有轮次信息，按任务ID存储
    tasks = {}

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

        # 提取问题
        q_match = re.search(r'Question:\s*(.+?)(?=\nThought|\nAction|$)', block, re.DOTALL)
        question = q_match.group(1).strip() if q_match else None

        # 提取模型最终答案（从最后一个 Finish 中提取，用于判断结果，但也可以直接看 CORRECT/INCORRECT）
        finish_matches = re.findall(r'Action \d+: Finish\[(.*?)\]', block, re.DOTALL)
        model_answer = finish_matches[-1].strip() if finish_matches else None

        # 判断本轮结果
        if 'Answer is CORRECT' in block:
            result = 'CORRECT'
        elif 'Answer is INCORRECT' in block:
            result = 'INCORRECT'
        else:
            result = None

        # 提取轨迹文本：从第一个 Thought 或 Action 开始，到块结束
        lines = block.split('\n')
        start_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^(?i)thought(?:\s+\d+)?:', line) or re.match(r'^(?i)action(?:\s+\d+)?:', line):
                start_idx = i
                break
        if start_idx is not None:
            trajectory_text = '\n'.join(lines[start_idx:])
        else:
            trajectory_text = ''  # 如果没有 Thought/Action，则空

        # 存入 tasks
        if task_id not in tasks:
            tasks[task_id] = {'reflections': []}
        tasks[task_id]['reflections'].append({
            'round': ref_round,
            'question': question,
            'trajectory': trajectory_text,
            'result': result,
            'model_answer': model_answer
        })

    return tasks


# ======================== 主修正逻辑 ========================
def main():
    log_path = r'C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\logs\math2code_math\expel\run-glm-2k.txt'
    pkl_path = r'C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\logs\math2code_math\expel\run-glm-2k.pkl'

    # 1. 解析日志
    tasks = parse_log(log_path)

    # 2. 统计结果
    success_count = 0
    fail_count = 0
    halted_count = 0
    failed_training_task_idx = []   # 存在任一 INCORRECT 轮次的任务编号
    succeeded_trial_history = {}    # {question: [Trajectory, ...]}
    failed_trial_history = {}       # {question: [Trajectory, ...]}
    
    print(f"Total tasks parsed: {len(tasks)}")

    for task_id, info in tasks.items():
        reflections = info['reflections']
        if not reflections:
            continue

        # 按轮次排序（日志顺序即递增）
        reflections_sorted = sorted(reflections, key=lambda x: x['round'])

        # 最终状态由最后一个轮次决定
        last_result = reflections_sorted[-1]['result']

        # 统计计数
        if last_result == 'CORRECT':
            success_count += 1
        elif last_result == 'INCORRECT':
            fail_count += 1
        else:
            halted_count += 1

        # 检查是否有任一 INCORRECT 轮次
        has_incorrect = any(r['result'] == 'INCORRECT' for r in reflections_sorted)
        if has_incorrect:
            failed_training_task_idx.append(task_id)

        # 构建 Trajectory 并分类
        for ref in reflections_sorted:
            question = ref['question']
            if question is None:
                continue
            traj_text = ref['trajectory']
            if not traj_text:
                continue

            # 构造 Trajectory 对象
            traj = Trajectory(
                task=question,
                trajectory=traj_text,
                splitter=CYCLER,
                identifier=STEP_IDENTIFIER,
                step_splitter=step_splitter,
                embedder=None,
                reflections=None
            )

            result = ref['result']
            if result == 'CORRECT':
                succeeded_trial_history.setdefault(question, []).append(traj)
            elif result == 'INCORRECT':
                failed_trial_history.setdefault(question, []).append(traj)
            # 其他状态（None）不加入任何历史

    # 3. 加载 pkl，修改 data[-1]
    import sys
    import pickle

    file_path = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\logs\math2code_math\expel\run-glm-2k.pkl"

    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    # 查看数据类型和结构
    print(type(data))
    print(data.keys() if isinstance(data, dict) else data)
    # 获取最后一个元素（假设是最终汇总字典）
    last = data[-1]
    # 更新指定键
    last['success'] = success_count
    last['fail'] = fail_count
    last['halted'] = halted_count
    last['failed_training_task_idx'] = failed_training_task_idx
    last['succeeded_trial_history'] = succeeded_trial_history
    last['failed_trial_history'] = failed_trial_history

    # 保存回 pkl
    # with open(pkl_path, 'wb') as f:
    #     pickle.dump(data, f)

    print(f"修正完成！")
    print(f"成功任务数: {success_count}, 失败任务数: {fail_count,len(failed_trial_history)}, 暂停任务数: {halted_count}")
    print(f"包含错误轮次的任务编号: {failed_training_task_idx}")
    print(f"正确轨迹条目数: {sum(len(v) for v in succeeded_trial_history.values())}")
    print(f"错误轨迹条目数: {sum(len(v) for v in failed_trial_history.values())}")


if __name__ == '__main__':
    main()