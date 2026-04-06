import random
import string
from typing import List, Dict, Callable, Tuple, Any, Union
from matplotlib import pyplot as plt

import tiktoken
from langchain.schema import (
    ChatMessage
)

from prompts import FEWSHOTS

import math
import pickle
import re


ENV_NAMES = [
            'pick_and_place',
            'pick_clean_then_place',
            'pick_heat_then_place',
            'pick_cool_then_place',
            'look_at_obj',
            'pick_two_obj'
        ]

TASK_ENV_NAMES = [
    ('clean', 'pick_clean_then_place'),
    ('hot', 'pick_heat_then_place'),
    ('heat', 'pick_heat_then_place'),
    ('cool', 'pick_cool_then_place'),
    ('look', 'look_at_obj'),
    ('examine', 'look_at_obj'),
    ('two', 'pick_two_obj'),
    ('put', 'pick_and_place') # last one must be at last position
]

class Count:
    """
    Class for reflection counting.
    """
    def __init__(self, maximum):
        self.count = 0
        self.maximum = maximum

    def increment(self):
        self.count += 1
        if self.count > self.maximum:
            self.count = self.maximum

    def is_beginning(self):
        return self.count == 1

    def reset(self):
        self.count = 0

    def is_maximum(self):
        return self.count == self.maximum

def random_divide_list(lst: List[Any], k: int):
    """
    Divides the list into chunks, each with maximum length k.

    Args:
        lst: The list to be divided.
        k: The maximum length of each chunk.

    Returns:
        A list of chunks.
    """
    random.shuffle(lst)
    if len(lst) <= k:
        return [lst]
    else:
        num_chunks = math.ceil(len(lst) / k)
        chunk_size = math.ceil(len(lst) / num_chunks)
        return [lst[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]

def shuffled_chunks(lst: List[Any], num_chunks: int):
    """
    Divides the list into chunks as equally as possible.

    Args:
        lst: The list to be divided.
        num_chunks: The number of chunks.

    Returns:
        A list of chunks.
    """
    random.shuffle(lst)
    chunk_size = len(lst) // num_chunks
    remainder = len(lst) % num_chunks
    chunks = [lst[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
    
    # Distribute the remainder elements across the chunks
    if remainder > 0:
        for i in range(remainder):
            chunks[i].append(lst[num_chunks * chunk_size + i])
    
    random.shuffle(chunks)
    return chunks

def token_counter(text: str, llm: str = 'gpt-3.5-turbo', tokenizer: Callable = None) -> int:
    """
    Counts the number of tokens in the text.
    
    Args:
        text: The text to be counted.
        llm: The language model name.
        tokenizer: The tokenizer to be used.
    """
    if 'gpt' in llm:
        return len(tiktoken.encoding_for_model(llm).encode(text))

    raise NotImplementedError

def print_message(message: Union[dict, ChatMessage], token_counter: Callable = None, testing: bool = True, extra_text: str = '') -> None:
    """
    Prints the formatted message.
    
    Args:
        message: The message to be printed (either dict or ChatMessage).
        token_counter: A function that takes in a string and returns the number of tokens in the string.
        testing: Add message type and token count in testing mode.
        extra_text: Extra text to be printed after the message in testing mode.
    """
    # 处理dict格式的消息
    if isinstance(message, dict):
        message_type = message.get('role', 'unknown')
        message_content = message.get('content', '')
    else:
        # 兼容原有的ChatMessage格式
        message_type = message.type
        message_content = message.content
    
    if testing:
        formatted_message = f"$$${message_type}$$$\t{message_content}\t$$${message_type}$$$"
        if token_counter is not None:
            formatted_message += f"\t***{token_counter(message_content)} tokens***"
            formatted_message += extra_text
        print(formatted_message)
    else:
        print(message_content)


def trace_prompt_history(
    prompt_history: List[dict],
    label: str,
    benchmark_name: str = None,
    max_preview: int = 120,
) -> None:
    """
    当 benchmark 为 math2code / math2code_math 时，将 prompt_history 的变化打印到控制台，
    用于跟踪 eval 运行时 self.prompt_history 的演变。
    """
    if benchmark_name not in ('math2code_math', 'code2math_code'):
        return
    print(f"\n>>> [prompt_history] {label}")
    print(f"    len(prompt_history) = {len(prompt_history)}")
    for i, msg in enumerate(prompt_history):
        role = msg.get('role', '?') if isinstance(msg, dict) else getattr(msg, 'type', '?')
        content = msg.get('content', '') if isinstance(msg, dict) else getattr(msg, 'content', '')
        n = len(content)
        preview = (content[:max_preview] + '...') if n > max_preview else content
        preview = preview.replace('\n', ' ')
        print(f"    [{i}] role={role} len={n} | {preview}")
    print("<<<\n")


# 原代码
# def parse_action(string: str):
#     """
#     Parse action string into action type and argument for HotpotQA and Fever.
    
#     Args:
#         string: action string
    
#     Returns:
#         action_type: action type
#         argument: argument
#     """
#     # Support multiline arguments inside [...] (e.g., code blocks in Finish[...])
#     # and allow empty arguments if the caller ever uses Action[].
#     pattern = r'^(\w+)\[(.*)\]$'
#     match = re.match(pattern, string, flags=re.DOTALL)
    
#     if match:
#         action_type = match.group(1)
#         argument = match.group(2)
#         return action_type, argument
    
#     else:
#         return None, None
import re

def parse_action2(string: str):
    """
    从包含 1 个或多个 action（包括 Reason[]、Implement[]、Finish[]等）的文本中,
    提取最后一个 action 的类型和内容。匹配失败（无有效 action）时返回 (None, None)。
    
    特性:
    - 适配单行/多行 action 内容（支持代码块、换行符、特殊字符）
    - 适配文本中只有 1 个 action 或多个 action 的场景
    - 支持括号嵌套（如 Calculate[13 + 9 - 20 + 3]）
    - 自动清理提取内容的首尾空白
    
    Args:
        string: 待解析的完整文本（可包含任意前缀/后缀文本 + 1个/多个 action）
    
    Returns:
        last_action_type: 最后一个 action 的类型（如 Finish/Implement），无则返回 None
        last_action_content: 最后一个 action 的内容（去掉外层 []），无则返回 None
    """
    
    # 匹配 action 类型（字母开头的单词）后跟方括号
    # 使用递归或栈来处理嵌套括号
    
    # 首先找到所有可能的 action 起始位置
    action_pattern = r'([A-Z][a-zA-Z]*)\['
    
    matches = []
    
    for match in re.finditer(action_pattern, string):
        action_type = match.group(1)
        start_pos = match.end()  # '[' 之后的位置
        
        # 使用栈来匹配嵌套括号
        bracket_count = 1
        pos = start_pos
        
        while pos < len(string) and bracket_count > 0:
            if string[pos] == '[':
                bracket_count += 1
            elif string[pos] == ']':
                bracket_count -= 1
            pos += 1
        
        # 如果括号匹配成功
        if bracket_count == 0:
            content = string[start_pos:pos-1]  # 提取括号内的内容（不含最后的']'）
            matches.append((action_type, content))
    
    # 无匹配结果时返回 (None, None)
    if not matches:
        return None, None
    
    # 取最后一个匹配项，清理首尾空白后返回
    last_type, last_content = matches[-1]
    return last_type.strip(), last_content.strip()


# 测试
test_str = """
Action 1: Thought 1: We can approach this problem using the principle of inclusion-exclusion to find the number of boxes containing both pens and pencils by considering the number of boxes containing pencils, pens, neither, and the total number of boxes. Let's calculate the number of boxes containing both pens and pencils using the formula: \( B_{\text{both}} = P + N - B + B_{\text{neither}} \), where \( P = 13 \) (boxes containing pencils), \( N = 9 \) (boxes containing pens), \( B = 20 \) (total number of boxes), and \( B_{\text{neither}} = 3 \) (boxes containing neither).
Calculate[13 + 9 - 20 + 3]Observation 1: Result: 5
Finish[5]
"""

result = parse_action2(test_str)
# print(result)  # 应该输出: ('Finish', '5')
import re

def parse_action(text: str):
    """
    专门解析 LLM 输出中的 Action（仅支持 Test / Finish）

    支持：
    - 多行代码
    - 嵌套括号
    - 忽略 List[...] / typing[...] 等干扰

    返回：
        (action_type, content) 或 (None, None)
    """

    ACTION_TYPES = ("Test", "Finish")
    matches = []

    i = 0
    n = len(text)

    while i < n:
        # 检查是否匹配某个 Action 类型
        for action in ACTION_TYPES:
            prefix = action + "["
            if text.startswith(prefix, i):
                start = i + len(prefix)

                # 栈匹配括号
                bracket_count = 1
                j = start

                while j < n and bracket_count > 0:
                    if text[j] == '[':
                        bracket_count += 1
                    elif text[j] == ']':
                        bracket_count -= 1
                    j += 1

                if bracket_count == 0:
                    content = text[start:j-1]
                    matches.append((action, content.strip()))
                    i = j  # 跳到匹配结束
                    break
        else:
            i += 1  # 没匹配到任何 action，继续

    if not matches:
        return None, None

    return matches[-1]
test_str = """
Action 1: Thought 1: ... Test[from typing import List
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    n = len(numbers)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False
assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False
assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True
assert has_close_elements([], 0.5) == False
assert has_close_elements([1.0], 0.5) == False
]
"""
action_type, content = parse_action(test_str)

print(action_type)
print(content[:200])

def normalize_answer(s: str):
    """
    Lower text and remove punctuation, articles and extra whitespace.
    
    Args:
        s: string to normalize

    Returns:
        normalized string
    """
    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)
    
    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))

def EM(answer, key) -> bool:
    """
    Exact match between answer and key.

    Args:
        answer: answer
        key: key
    
    Returns:
        True if exact match, else False
    """
    return normalize_answer(answer) == normalize_answer(key)


def save_trajectories_log(path: str, log: str = None, dicts: list = None, true_log: str = None, save_log: bool = True, save_dict: bool = True, save_true_log: bool = True, run_name: str = 'run') -> None:
    """
    Saves the log and the dict to the path.
    
    Args:
        path: The path to save the log and the dictionaries.
        log: The log to be saved.
        dicts: The dict to be saved.
        true_log: The true log to be saved.
        save_log: Whether to save the log.
        save_dict: Whether to save the dictionaries.
        save_true_log: Whether to save the true log.
        run_name: The name of the run.
    """
    if save_log:
        with open(f'{path}/{run_name}.txt', 'w', encoding='utf-8') as f:
            f.write(log)
    if save_dict:
        with open(f'{path}/{run_name}.pkl', 'wb') as f:
            pickle.dump(dicts, f)
    if save_true_log:
        with open(f'{path}/{run_name}_true.txt', 'w', encoding='utf-8') as f:
            f.write(true_log)

def load_trajectories_log(path: str, load_log: bool = True, load_dict: bool = True, load_true_log: bool = False, run_name: str = 'run') -> Dict[str, Any]:
    """
    Loads the log and the dict from the path.
    
    Args:
        path: The path to load the logs and the dictionaries.
        load_log: Whether to load the log.
        load_dict: Whether to load the dictionaries.
        load_true_log: Whether to load the true log.
        run_name: The name of the run.
    
    Returns:
        A dictionary containing the logs and the dict.
    """
    out = dict()
    if load_log:
        with open(f'{path}/{run_name}.txt', 'r', encoding='utf-8') as f:
            out['log'] = f.read()
    if load_dict:
        with open(f'{path}/{run_name}.pkl', 'rb') as f:
            out['dicts'] = pickle.load(f)
    if load_true_log:
        with open(f'{path}/{run_name}_true.txt', 'r', encoding='utf-8') as f:
            out['true_log'] = f.read()
        
    return out


def format_math2code_log(s: str) -> str:
    """Insert newlines before Observation/Action/Thought blocks for readable math2code_math logs."""
    for pat in [r'Observation\s*\d+\s*:', r'Action\s*\d+\s*:', r'Thought\s*\d+\s*:']:
        s = re.sub(r'(?<!\n)(?=' + pat + r')', '\n', s)
    return s


def split_logs_by_task(text: str, num_tasks: int) -> List[List[str]]:
    """
    Splits the log text by task.
    
    Args:
        text: The log text.
        num_tasks: The number of tasks.
        
    Returns:
        A list of lists of log texts, each list corresponding to a task.
    """
    remaining_text = text
    parsed_result = []
    for task_i in range(num_tasks+1):
        if task_i == num_tasks:
            pattern_i = r'########################################\nEND TRIAL'
        else:
            pattern_i = rf'#######################################\n.*TASK {str(task_i)} '
        matches_i = re.split(pattern_i, remaining_text)
        remaining_text = matches_i[-1]
        parsed_result.append(matches_i[1:-1])
        if task_i != 0:
            parsed_result[task_i-1].append(matches_i[0])

    # remove the last empty list
    parsed_result.pop()

    return parsed_result

def recompute_stats(parsed_result: List[List[str]], benchmark: str, trial: int = -1) -> Dict[str, int]:
    """
    Recomputes the stats from the parsed log text.
    
    Args:
        parsed_result: The parsed log text.
        benchmark: The benchmark name.
        trial: The number of trials.
        
    Returns:
        The stats for the given benchmark.
    """
    stats = {"success": 0, "fail": 0, "halted": 0} if benchmark != 'alfworld' else {"success": 0, "fail": 0}

    for task_i in range(len(parsed_result)):
        trajectories = parsed_result[task_i]
        last_trajectory = trajectories[min(trial, len(trajectories) - 1)].strip()
        last_step = last_trajectory.split('\n')[-1]

        if benchmark in ['hotpotqa', 'math2code_math', 'code2math_code']:
            if ' CORRECT' in last_step or 'Answer is correct.' in last_step:
                stats["success"] += 1
            elif 'INCORRECT' in last_step or 'Answer is incorrect.' in last_step:
                stats["fail"] += 1
            else:
                stats["halted"] += 1
        elif benchmark == 'alfworld':
            if 'SOLVED' in last_step:
                stats["success"] += 1
            else:
                stats["fail"] += 1
        elif benchmark == 'webshop':
            if ': 1.0' in last_step or 'Your score' in last_step:
                stats["success"] += 1
            else:
                stats["halted"] += 1
        elif benchmark == 'fever':
            if 'reward = 1' in last_step:
                stats["success"] += 1
            elif 'reward = 0' in last_step:
                stats["fail"] += 1
            else:
                stats["halted"] += 1
        else:
            raise NotImplementedError(f'recompute_stats for {benchmark} not implemented')
        
    return stats

def plot_trial_stats(parsed_result: List[List[str]], benchmark: str, max_trials: int = 4, save_path: str = None) -> Dict[str, List[int]]:
    """
    Plots the stats from the parsed log text.
    
    Args:
        parsed_result: The parsed log text.
        benchmark: The benchmark name.
        max_trials: The number of trials.
        save_path: The path to save the figure.
        
    Returns:
        The stats for the given benchmark.
    """
    results = dict()
    colors = {'success': 'green', 'fail': 'red', 'halted': 'orange'}

    for i in range(max_trials):
        stats = recompute_stats(parsed_result, benchmark, i)
        for key, value in stats.items():
            results[key] = results.get(key, []) + [value]

    if benchmark == 'alfworld':
        assert len(parsed_result) == 134
        results = {k: [round(x / 134 * 100, 2) for x in v] for k, v in results.items()}
    else:
        num_tasks = len(parsed_result)
        if num_tasks == 100:
            results = {k: [round(x / 100 * 100, 2) for x in v] for k, v in results.items()}
        # math2code / math2code_math: keep raw counts

    for i, (key, value) in enumerate(results.items()):
        plt.plot(value, label=key, marker='o', color=colors[key])

    # annotate all points with their values next to them
    for i in range(max_trials):
        for key, value in results.items():
            plt.annotate(value[i], (i, value[i]), textcoords="offset points", xytext=(0,10), ha='center')

    plt.legend(loc='best')
    plt.xlabel("Reflection numbers")
    plt.ylabel("Task SR %")
    plt.xticks(range(max_trials))
    plt.show()
    if save_path:
        plt.savefig(save_path)
    
    return results

def get_env_name_from_gamefile(gamefile: str) -> Union[str, None]:
    """
    Gets the environment name from the gamefile for ALFWorld.

    Args:
        gamefile: The gamefile.

    Returns:
        The environment name.
    """
    for k in ENV_NAMES:
        if k in gamefile:
            return k

def get_env_name_from_task(task: str, benchmark: str) -> Union[str, None]:
    """
    Gets the environment name from the task instruction for ALFWorld.

    Args:
        task: The task.
        benchmark: The benchmark name.

    Returns:
        The environment name.
    """
    if benchmark == 'alfworld':
        for k, v in TASK_ENV_NAMES:
            if k in task:
                return v
    else:
        return benchmark

def alfworld_results_per_env_name(agent: Dict[str, Any]) -> Dict[str, int]:
    """
    Computes the results per environment name for ALFWorld from agent dict.
    
    Args:
        agent: The agent dictionary.
        
    Returns:
        The results per environment name.
    """
    tasks = agent['tasks']
    succeeded_trial_history = agent['succeeded_trial_history']
    failed_trial_history = agent['failed_trial_history']
    
    results = {k: 0 for k in ENV_NAMES}
    totals = {k: 0 for k in ENV_NAMES}
    seen = {t['task']: 0 for t in tasks}
    for task in tasks:
        t = task['task']
        env_name = get_env_name_from_gamefile(task['env_kwargs']['gamefile'])
        if len(succeeded_trial_history[t]) > seen[t]:
            results[env_name] += 1
            totals[env_name] += 1
            seen[t] += 1
        elif len(failed_trial_history[t]) > 0:
            totals[env_name] += 1
    
    return {k: round(results[k] / totals[k], 2) if totals[k] != 0 else 0 for k in results.keys()}

def alfworld_results_per_env_name_log(log: str, num_tasks: int, num_trials: int) -> Dict[str, int]:
    """
    Computes the results per environment name for ALFWorld from log text.
    
    Args:
        log: The log text.
        num_tasks: The number of tasks.
        num_trials: The number of trials.
    
    Returns:
        The results per environment name.
    """
    results = {k: [0, 0, 0, 0] for k in ENV_NAMES}
    totals = {k: [0, 0, 0, 0] for k in ENV_NAMES}

    parsed_results = split_logs_by_task(log, num_tasks)
    for i in range(num_trials):
        for task in parsed_results:
            if 'You are in the middle of a room' not in task[i if i < len(task) else -1]:
                continue
            task_desc = re.findall(r'Your task is to: (.*)', task[i if i < len(task) else -1])[0]
            env_name = get_env_name_from_task(task_desc, 'alfworld')
            if env_name is None:
                raise ValueError(f'env_name is None for task {task_desc}')
            if 'SOLVED' in task[i if i < len(task) else -1].strip().split('\n')[-1]:
                results[env_name][i] += 1
            totals[env_name][i] += 1

    assert all([sum([totals[k][i] for k in ENV_NAMES]) == num_tasks for i in range(num_trials)])
    print(totals)
    
    return {k: [round(results[k][i] / totals[k][i], 2) if totals[k][i] != 0 else 0 for i in range(num_trials)] for k in ENV_NAMES}

def get_webshop_mean_score(log: str, num_tasks: int, num_trials: int) -> float:
    """
    Computes the mean score for WebShop from log text.
    
    Args:
        log: The log text.
        num_tasks: The number of tasks.
        num_trials: The number of trials.
    
    Returns:
        The mean score.
    """
    parsed_result = split_logs_by_task(text=log, num_tasks=num_tasks)
    
    assert len(parsed_result) == num_tasks
    return sum([
        max([
            float(parsed_result[k][i].strip().split('\n')[-1].split()[-1] 
                if 'Your score' in parsed_result[k][i].strip().split('\n')[-1] else 0) 
            for i in range(min(len(parsed_result[k]), num_trials))
            ]
        ) for k in range(len(parsed_result))]
    ) / len(parsed_result)

def get_webshop_mean_scores(log: str, num_tasks: int, num_trials: int) -> float:
    """
    Computes the mean scores for WebShop from log text.

    Args:
        log: The log text.
        num_tasks: The number of tasks.
        num_trials: The number of trials.
    
    Returns:
        The mean scores.
    """
    return [get_webshop_mean_score(log, num_tasks, i) for i in range(1, num_trials + 1)]

def get_fewshot_max_tokens(benchmark: str) -> int:
    """
    Gets the maximum number of tokens in the fewshot tasks for the given benchmark.
    
    Args:
        benchmark: The benchmark name.
    
    Returns:
        The maximum number of tokens.
    """
    fewshots = FEWSHOTS[benchmark]
    if isinstance(fewshots, dict):
        return max([max([token_counter(f) for f in fs]) for fs in fewshots.values()])
    elif isinstance(fewshots, list):
        return max([token_counter(f) for f in fewshots])

def get_split_eval_idx_list(agent_dict: Dict[str, Any], n_folds: int) -> List[List[int]]:
    """
    Gets the split evaluation index list.
    
    Args:
        agent_dict: The agent dictionary.
        n_folds: The number of folds.
    
    Returns:
        The split evaluation index list.
    """
    # For eval-only runs (or when explicitly set), a single fold means "evaluate all tasks".
    # The no-overlap invariant is trivially satisfied for 1 fold.
    if n_folds <= 1:
        return [list(range(len(agent_dict.get('tasks', []))))]

    eval_idx_list = [[] for _ in range(n_folds)]
    env_names = set(x['env_name'] for x in agent_dict['tasks'])
    task2idx = agent_dict['task2idx']

    # compare success/failure
    compare_dict = {env_name: [] for env_name in env_names}
    success_dict = {env_name: [] for env_name in env_names}
    fail_dict = {env_name: [] for env_name in env_names}
    for task, trials in agent_dict['succeeded_trial_history'].items():
        # 检查键是否存在
        if task not in agent_dict['failed_trial_history']:
            agent_dict['failed_trial_history'][task] = []
        
        if len(trials) > 0:
            if len(agent_dict['failed_trial_history'][task]) > 0:
                compare_dict[get_env_name_from_task(task, agent_dict['benchmark_name'])].append(task2idx[task])
            else:
                success_dict[get_env_name_from_task(task, agent_dict['benchmark_name'])].append(task2idx[task])
        else:
            # 只有在有失败试验时才添加到fail_dict
            if len(agent_dict['failed_trial_history'][task]) > 0:
                fail_dict[get_env_name_from_task(task, agent_dict['benchmark_name'])].append(task2idx[task])
            # 如果既没有成功也没有失败，跳过这个任务
            else:
                print(f'task {task} has no failed trials')
                continue

    # split into n_folds
    j = 0
    for idx_list in list(compare_dict.values()) + list(success_dict.values()) + list(fail_dict.values()):
        random.shuffle(idx_list)
        for idx in idx_list:
            eval_idx_list[j % n_folds].append(idx)
            j += 1
    
    # Ensure there are no duplicates across folds.
    flat = [i for fold in eval_idx_list for i in fold]
    assert len(flat) == len(set(flat))
    
    return eval_idx_list

def mode_results(benchmark: str, log: str, num_tasks: int, mode: str) -> Any:
    """
    Computes the statistic results for the given mode.
    
    Args:
        benchmark: The benchmark name.
        log: The log text.
        num_tasks: The number of tasks.
        mode: The mode.
    
    Returns:
        The results.
    """
    parsed_result = split_logs_by_task(text=log, num_tasks=num_tasks)
    if 'react' in mode:
        parsed_result = [x[0] for x in parsed_result]
    elif 'reflection' in mode:
        pattern = r'reflection(\d+)'
        res = re.findall(pattern, mode)
        if len(res) > 0:
            i = int(res[0])
        else:
            pattern = r'(\d+)reflection'
            res = re.findall(pattern, mode)
            if len(res) > 0:
                i = int(res[0])
            else:
                i = 0
        parsed_result = [x[i if i < len(x) else -1] for x in parsed_result]

    if 'token' in mode:
        f_trial = token_counter
    elif 'count' in mode:
        f_trial = lambda x: 1
    else:
        raise NotImplementedError(f'mode must contain token or count')

    invalid = None
    if 'invalid' in mode:
        if benchmark == 'alfworld':
            invalid = 'nothing happens'
        elif benchmark == 'webshop':
            invalid = 'invalid action' 
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'code2math_code']:
            invalid = 'invalid action'
        mode += 'observation'

    if 'thought' in mode:
        if benchmark == 'webshop':
            lambda_filter = lambda y: y.strip().startswith('Action: think[')
        elif benchmark == 'alfworld':
            lambda_filter = lambda y: y.strip().startswith('> think:')
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'code2math_code']:
            lambda_filter = lambda y: y.strip().startswith('Thought')
        else:
            raise NotImplementedError(f'benchmark {benchmark} not implemented')
    elif 'action' in mode:
        if benchmark == 'webshop':
            lambda_filter = lambda y: y.strip().startswith('Action: click[') or y.strip().startswith('Action: search[') # valid actions
        elif benchmark == 'alfworld':
            lambda_filter = lambda y: y.strip().startswith('> ') and not y.strip().startswith('> think:') # valid and invalid actions
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'code2math_code']:
            lambda_filter = lambda y: y.strip().startswith('Action')
        else:
            raise NotImplementedError(f'benchmark {benchmark} not implemented')
    elif 'observation' in mode:
        if benchmark == 'webshop':
            lambda_filter = lambda y: y.strip().startswith('Observation:')
        elif benchmark == 'alfworld':
            lambda_filter = lambda y: not y.strip().startswith('> ')
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'code2math_code']:
            lambda_filter = lambda y: y.strip().startswith('Observation')
        else:
            raise NotImplementedError(f'benchmark {benchmark} not implemented')
    else:
        lambda_filter = lambda y: True

    if 'step' in mode:
        if invalid is not None:
            parsed_result = [y for x in parsed_result for y in x.strip().split('\n') if lambda_filter(y) and invalid in y.lower()]
        else:
            parsed_result = [y for x in parsed_result for y in x.strip().split('\n') if lambda_filter(y)]
        
    elif 'traj' in mode:
        if invalid is not None:
            parsed_result = [[y for y in x.strip().split('\n') if lambda_filter(y) and invalid in y.lower()] for x in parsed_result]
        else:
            parsed_result = [[y for y in x.strip().split('\n') if lambda_filter(y)] for x in parsed_result]
        assert len(parsed_result) == num_tasks
    else:
        raise NotImplementedError('mode must contain traj or step')

    if 'sum' in mode:
        f_return = sum
    elif 'mean' in mode:
        f_return = lambda x: sum(x) / len(x) if len(x) > 0 else 0
    elif 'list' in mode:
        f_return = lambda x: x
    else:
        raise NotImplementedError('mode must contain sum, mean or list')
    
    if 'print' in mode:
        print(parsed_result)

    if len(parsed_result) > 0 and isinstance(parsed_result[0], List):
        return f_return([sum([f_trial(trial) for trial in result]) for result in parsed_result])
    
    return f_return([f_trial(trial) for trial in parsed_result])
