import json
import openai
import time
import re
from typing import List, Dict, Any, Tuple
import requests

import io
import sys
# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

insights = """To solve Code Generation problems effectively, break down the task into clear, logical steps and explicitly write out each intermediate step or calculation to avoid errors. Verify all results, especially when performing arithmetic or logic operations, by manually checking for accuracy. Simplify complex expressions or algorithms by leveraging patterns, algebraic identities, or modular arithmetic properties where applicable. Ensure the final solution satisfies all constraints and conditions by rigorously testing it against edge cases and requirements. Avoid relying solely on external snippets or unverified assumptions; instead, derive solutions from first principles or established coding practices. Optimize your approach by reducing variables, using substitutions, or applying relevant theorems (e.g., Burnside’s Lemma for symmetry) when needed. Finally, confirm the solution is complete and correct before finalizing, ensuring no partial or intermediate states are left unresolved."""
# Target_Task_File = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\data\code2math\human-eval-v2-20210705.jsonl"
# Target_Task_File = r"C:\Users\HUAWEI\Desktop\COPS-main-real\math2code\data\mbpp_plus_test.jsonl"
# Target_Task_File = r"C:\Users\HUAWEI\Desktop\MathWithCode\Baseline\leetcode-baseline\LeetCodeDataset\LeetCodeDataset-test.jsonl"
Target_Task_File = r"C:\Users\HUAWEI\Desktop\MathWithCode\Baseline\LiveCodeBench\LiveCodebench_200.jsonl"

SYSTEM_PROMPT = "You are an expert competitive programmer."
Target_Task = "Code Completion"
fewshot = """
Solve a programming problem with interleaving Thought, Action, Observation steps.
Thought can reason about the problem, analyze requirements, and design the solution.
Action has only one type:
(1) Finish[code], which submits the final complete Python implementation and finishes the task.

After each observation, provide the next Thought and next Action. Here are examples:

Problem:
You are given a string t.
If t[i] is a digit, replace it with its complement to 9 (9 - digit).
Otherwise keep it unchanged.
If the string contains no digits, convert the entire string to uppercase.
Return the resulting string.

Please complete the following Python code:
def process_string(t):

Thought 1:
First, I analyze the requirement: this is a string transformation task with conditional logic.
- If the string contains digits: replace each digit with 9 minus the digit
- If no digits exist: convert the whole string to uppercase
I need to track whether any digit appears during traversal.
Step-by-step plan:
1. Initialize an empty result list and a flag has_digit
2. Traverse each character in the input string
3. If character is digit: compute complement, append to result, set has_digit to True
4. Else: append the original character
5. After traversal: if no digits, return uppercase of result; else return joined result
Action 1: Finish[
def process_string(t):
    has_digit = False
    res = []
    for ch in t:
        if ch.isdigit():
            res.append(str(9 - int(ch)))
            has_digit = True
        else:
            res.append(ch)
    result = ''.join(res)
    if not has_digit:
        return result.upper()
    return result
]
Observation 1: Answer is correct.

Problem:
Given a string 'text', return its md5 hash equivalent string.
If 'text' is an empty string, return None.

Please complete the following Python code:
def string_to_md5(text):

Thought 1:
I need to implement MD5 hash calculation with empty string handling.
I will use Python's built-in hashlib library which provides standard MD5 implementation.
Key points to handle:
1. Empty input check: return None directly if text is empty
2. Encode string to bytes (utf-8) before hashing
3. Return hexadecimal digest string
Action 1: Finish[
def string_to_md5(text):
    import hashlib
    if not text:
        return None
    return hashlib.md5(text.encode('utf-8')).hexdigest()
]
Observation 1: Answer is correct.

Problem:
Return all odd numbers between x and y that lie within 1 to 9 (inclusive), sorted ascending.

Please complete the following Python code:
def generate_odd_numbers(x, y):

Thought 1:
The function needs to return odd numbers in the intersection of [min(x,y), max(x,y)] and [1,9], sorted ascending.
Key constraints:
1. Handle reversed input (x > y) by taking min and max
2. Clamp the range to [1, 9] to exclude out-of-bound values
3. Filter only odd numbers from the valid range
Edge cases: if clamped lower bound > upper bound, return empty list
Action 1: Finish[
def generate_odd_numbers(x, y):
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    if lower > upper:
        return []
    return [i for i in range(lower, upper+1) if i % 2 == 1]
]
Observation 1: Answer is correct."""


def replace_invalid_roles(messages):
    """
    批量替换messages中的非法角色名:
    - human → user(用户角色)
    - ai → assistant(助手/AI角色)
    支持嵌套结构,深拷贝保护原数据
    """
    import copy
    processed_messages = copy.deepcopy(messages)

    role_mapping = {
        "human": "user",
        "ai": "assistant",
    }
    for msg in processed_messages:
        if isinstance(msg, dict) and "role" in msg and msg["role"] in role_mapping:
            msg["role"] = role_mapping[msg["role"]]
    return processed_messages

import os

def generate_qwen_completion(messages):
    # jiajia
    openai.api_key = os.getenv("ALIYUN_API_KEY")
    openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    messages = replace_invalid_roles(messages)
    completion = openai.ChatCompletion.create(
        model="qwen3-14b",
        messages=messages,
        enable_thinking=False,
        stream=False,
        temperature=0.1,
        headers={
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json",
        },
    )
    return completion.choices[0].message.content

import requests
import json
def generate_glm_completion(messages):
    messages = replace_invalid_roles(messages)
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    payload = {
        "model": "glm-4.7",
        "messages": messages,
        "stream": False,
        "temperature": 0.1,
        "thinking": { "type": "disabled" },
        "response_format": { "type": "text" }
    }
    API_KEY = os.getenv("BIGMODEL_API_KEY")
    headers = {
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # 捕获HTTP请求错误
    try:
        # 尝试正常打印
        print("llm response:", response.text)
    except UnicodeEncodeError:
        # 编码失败时，替换无法编码的字符（或忽略）
        print("llm response:", response.text.encode('utf-8', errors='replace').decode('utf-8'))
    # 第一步:解析LLM返回的顶层JSON
    llm_response = json.loads(response.text)
    # 提取content字段(此时是JSON字符串)
    content_json_str = llm_response["choices"][0]["message"]["content"]
    try:
        content_data = json.loads(content_json_str)
        # 核心:适配content_data为列表的情况(如 [[0], {xxx:xxx, answer:xxx}])
        if isinstance(content_data, list):
            # 遍历列表中的每个元素,找包含answer的字典
            answer = None
            for item in content_data:
                if isinstance(item, dict) and "answer" in item:
                    answer = item.get("answer")
                    break
            # 若列表中没找到answer,返回原字符串兜底
            if answer is None:
                #检查是否有外括号[]包着，且括号内是字符串
                if content_json_str.startswith("[") and content_json_str.endswith("]"):
                    answer = content_json_str[1:-1]
                else:
                    answer = content_json_str
        
        # 兼容content_data为字典的情况
        elif isinstance(content_data, dict):
            answer = content_data.get("answer", content_json_str)
        
        # 其他类型(如字符串/数字)直接返回
        else:
            answer = content_json_str
        return answer.strip() if answer else ""       

    except json.JSONDecodeError:
        # 如果content不是有效JSON,直接返回原字符串
        answer = content_json_str
        return answer.strip() if answer else ""       
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误:{e}")
        return ""


import re

def parse_action(string: str):
    """
    从包含 1 个或多个 action(包括 Finish[]等)的文本中,
    提取最后一个 action 的类型和内容。匹配失败(无有效 action)时返回 (None, None)。
    
    特性:
    - 适配单行/多行 action 内容(支持代码块、换行符、特殊字符)
    - 适配文本中只有 1 个 action 或多个 action 的场景
    - 支持括号嵌套(如 Calculate[13 + 9 - 20 + 3])
    - 自动清理提取内容的首尾空白
    - 只匹配特定的action关键词，避免匹配类型注解
    
    Args:
        string: 待解析的完整文本(可包含任意前缀/后缀文本 + 1个/多个 action)
    
    Returns:
        last_action_type: 最后一个 action 的类型(如 Finish/Implement),无则返回 None
        last_action_content: 最后一个 action 的内容(去掉外层 []),无则返回 None
    """
    
    # 只匹配特定的action关键词，避免匹配到类型注解如List[、Dict[等
    # 支持的action: Reason, Implement, Verify, Finish, Calculate, Think, Thought等
    valid_actions = r'(?:Finish)'
    action_pattern = f'({valid_actions})\\['
    
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
            content = string[start_pos:pos-1]  # 提取括号内的内容(不含最后的']')
            matches.append((action_type, content))
    
    # 无匹配结果时返回 (None, None)
    if not matches:
        return None, None
    
    # 取最后一个匹配项,清理首尾空白后返回
    last_type, last_content = matches[-1]
    return last_type.strip(), last_content.strip()


def extract_finish_code(completion_text):
    """
    提取 Finish[] 中最后一个块的代码内容(支持代码内包含 ])
    :param completion_text: 包含 Finish[code] 的文本
    :return: 提取的代码字符串(去除首尾空白),无匹配时返回空字符串
    """
    # 正则解释:
    # (?is) :i=忽略大小写,s=让.匹配换行符
    # Finish\[ :匹配 Finish[([需要转义)
    # (.*) :贪婪匹配任意字符(直到最后一个 ])
    # (?=]$|\s*$) :正向断言,确保 ] 是行尾/文本尾(或后续只有空白)
    pattern = r"(?is)Finish\[(.*)]\s*$"
    
    # 先找所有 Finish[ 开头的匹配
    matches = list(re.finditer(r"(?is)Finish\[", completion_text))
    if not matches:
        return ""
    
    # 取最后一个 Finish[ 的位置,从该位置开始截取文本
    last_match_start = matches[-1].start()
    target_text = completion_text[last_match_start:]
    
    # 对截取后的文本匹配完整的 Finish[code]
    code_match = re.match(pattern, target_text)
    if code_match:
        return code_match.group(1).strip()
    return ""

def count_indent(text: str) -> int:
    count = 0
    for char in text:
        if char == " ":
            count += 1
        else:
            break
    return count

def fix_indents(text: str, multiple: int = 2):
    outputs = []
    for line in text.split("\n"):
        while count_indent(line) % multiple != 0:
            line = " " + line
        outputs.append(line)
    return "\n".join(outputs)

def clear_code(code: str) -> str:
    #     # 清除前缀python、py、```等标记,以及前后多余的空白
    code = re.sub(r"^(?:python|py|```python)?\s*", "", code)
    code = re.sub(r"\s*```$", "", code)
    code = code.lstrip("\n")
    code = fix_indents(code)
    # 替换代码中的", "为"""
    # code = code.replace('\", \"', '\"\"\"')
    return code

def check_humaneval_completion(problem: Dict[str, Any], completion: str) -> Tuple[bool, str]:
    """
    第二步:参考 human-eval 的 execution.py,对单个 completion 做功能正确性检查。

    这里使用简化实现:
    - 构造程序 = problem['prompt'] + completion + test + check(entry_point)
    - exec 运行,捕获 AssertionError / Exception
    - 不使用多线程,也不引入复杂沙箱,仅用于离线评测。
    """
    prompt = problem["prompt"]
    test_snippet = problem["test"]
    entry_point = problem["entry_point"]

    check_program = f"{prompt}\n{completion}\n\n{test_snippet}\n\ncheck({entry_point})"

    global_ns: Dict[str, Any] = {"__builtins__": __builtins__}
    try:
        exec(compile(check_program, "<humaneval_check>", "exec"), global_ns, global_ns)
    except AssertionError as e:
        return False, f"INCORRECT: test assertion failed: {e}"
    except Exception as e:
        return False, f"ERROR: {type(e).__name__}: {e}"
    return True, "passed"


def run_transfer_and_eval() -> None:
    """
    主流程:
    1)从 ExpeL 日志中抽取 rules,并总结成适用于 HumanEval code generation 的段落;
    2)遍历 HumanEval(code_tasks.jsonl),对每个任务构造 prompt 调用大模型生成代码;
    3)执行 HumanEval 测试脚本评测生成代码是否通过;
    4)统计 pass@1(= 通过任务数 / 总任务数)。
    """
    results: List[Dict[str, Any]] = []
    MODEL_NAME = "qwen3-14b"
    # 生成带时间戳的输出文件名
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    predictions_path = f"expel-leetcode_{MODEL_NAME}_{timestamp}.jsonl"

    # 2. 遍历 Leetcode 任务,逐个生成 & 评测
    with open(Target_Task_File, "r", encoding="utf-8") as f_in, \
            open(predictions_path, "w", encoding="utf-8") as f_pred:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            problem = json.loads(line)
            task_id = problem.get("task_id", "UNKNOWN")
            # Target_Task_description = problem.get("prompt", "").strip()+"\n"+'\n'.join(problem.get("test_list", ""))
            # parts = []

            # problem_desc = problem.get("problem_description", "").strip()
            # starter_code = problem.get("starter_code", "").strip()

            # if problem_desc:
            #     parts.append(f"Problem:\n{problem_desc}")
            
            # if starter_code:
            #     parts.append(f"\nPlease complete the following Python code without providing any additional tasks such as testing or explanations. \n{starter_code}")

            # if not parts:
            #     # 兜底：数据集字段名与预期不符时，打印警告并返回空串
            #     print(f"  [警告] task_id={task.get('task_id')} 缺少 problem_description 和 starter_code 字段")

            # Target_Task_description =  "\n".join(parts)
            Target_Task_description = f"Problem:\n{problem.get('question_content', '').strip()}"
            prompt = f"""The following paragraph is insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the {Target_Task} tasks efficiently:
[Finetuned insights]
{insights}
[Target Task description + fewshot]
{fewshot}
{Target_Task_description}"""

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            for msg in messages:
                role , content = msg.items()
                role = list(role)[1]
                content = list(content)[1]
                print(f"{role}: {content}")

            # 为每个 HumanEval 任务生成一次 completion(n=1,用于 pass@1)
            completion_text = ""
            for i in range(3):
                try:
                    completion_text = generate_qwen_completion(messages)                    
                    if completion_text == "":
                        print(f"\n[{task_id}] API call failed, retrying {i+1}/3...")
                        time.sleep(2)
                        continue
                    else:
                        action , completion_text = parse_action(completion_text)
                        if action == "Finish":
                            completion_text = clear_code(completion_text) 
                            print("============Completion============")
                            print(completion_text)
                            print("==================================")
                    break
                except openai.error.RateLimitError:
                    print(f"\n[{task_id}] Rate limit error, retrying {i+1}/3...")
                    time.sleep(2)
            else:
                print(f"[{task_id}] Failed to get completion after 3 attempts, mark as failed.")

            f_pred.write(
                json.dumps({"task_id": task_id, "completion": completion_text}, ensure_ascii=False)
                + "\n"
            )
            
if __name__ == "__main__":
    run_transfer_and_eval()