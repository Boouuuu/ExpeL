import json
import openai
import time
import re
from typing import List, Dict, Any, Tuple
import requests

def replace_invalid_roles(messages):
    """
    批量替换messages中的非法角色名：
    - human → user（用户角色）
    - ai → assistant（助手/AI角色）
    支持嵌套结构，深拷贝保护原数据
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
MODEL_NAME = "glm-4.7"


# def generate_one_completion(messages):
#     # jiajia
#     # openai.api_key = "sk-a3b1a801d70747a0b7d3b2797a14ab05"
#     openai.api_key = "sk-afa113e744a345899ad27f3452c08ffa"
#     openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
#     messages = replace_invalid_roles(messages)
#     completion = openai.ChatCompletion.create(
#         model=MODEL_NAME,
#         messages=messages,
#         extra_body={"enable_thinking": False},
#         stream=False,
#         temperature=0.2,
#         max_tokens=4096,
#         headers={
#             "Authorization": f"Bearer {openai.api_key}",
#             "Content-Type": "application/json",
#         },
#     )
#     return completion.choices[0].message.content

import requests
import json
def generate_one_completion(messages):
    messages = replace_invalid_roles(messages)
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    payload = {
        "model": "glm-4.7",
        "messages": messages,
        "stream": False,
        "temperature": 0.1,
        "thinking": { "type": "disabled" },
        "response_format": { "type": "json_object" }
    }
    headers = {
        "Authorization": "Bearer 8e9538dc2cad4a958edcc94295daba15.FRhIeGeqFkFLcDCq",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # 捕获HTTP请求错误
    print("llm response：", response.text)
    # 第一步：解析LLM返回的顶层JSON
    llm_response = json.loads(response.text)
    # 提取content字段（此时是JSON字符串）
    content_json_str = llm_response["choices"][0]["message"]["content"]
    try:
        content_data = json.loads(content_json_str)
        # 核心：适配content_data为列表的情况（如 [[0], {xxx:xxx, answer:xxx}]）
        if isinstance(content_data, list):
            # 遍历列表中的每个元素，找包含answer的字典
            answer = None
            for item in content_data:
                if isinstance(item, dict) and "answer" in item:
                    answer = item.get("answer")
                    break
            # 若列表中没找到answer，返回原字符串兜底
            if answer is None:
                answer = content_json_str
        
        # 兼容content_data为字典的情况
        elif isinstance(content_data, dict):
            answer = content_data.get("answer", content_json_str)
        
        # 其他类型（如字符串/数字）直接返回
        else:
            answer = content_json_str
        return answer.strip() if answer else ""       

    except json.JSONDecodeError:
        # 如果content不是有效JSON，直接返回原字符串
        answer = content_json_str
        return answer.strip() if answer else ""       
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误：{e}")
        return ""

Knowledge_Finetuning_prompt_template = """You are a teacher agent that passes on experience to student agents. You came up with the following rules to help you achieve the task of {Source_Task} effectively. The number at the end are the importance you gave to each of the rules.
RULES:
{Extracted_insights}
Now a student agent is trying to solve a similar {Target_Task}.

Some examples of this new task are:
{Fixed_fewshot_examples_of_Target_Task}
(END OF EXAMPLES)

Give a concise and easy to follow instructional paragraph based on the RULES for the student agent to solve {Target_Task}. Do not state where each sentence is using whichever rule, and make sure the paragraph is VERY CONCISE and EASY TO FOLLOW!
"""

Knowledge_transfer_prompt_template = """The following paragraph is insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the {Target_Task} tasks efficiently:
{Finetuned_insights}

{Target_Task_description}

{Fixed_fewshot_examples_of_Target_Task}
(END OF EXAMPLES)

Now it's your turn!
{Target_Task_Question}
"""

def extract_insights(insights_path: str) -> str:
    """
    从 ExpeL 日志 txt 中抽取最后一段 \"Extracted insights from Source Task\" 的规则。

    假设：
    - 日志中多次出现 '-------'，最后一次之后紧跟的是最终的 insights；
    - insights 以 '- ' 开头的一行一个规则，末尾可能有 '{27}' 这样的重要性标记。
    """
    with open(insights_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 取最后一个分隔块后的内容
    if "-------" in text:
        tail = text.split("-------")[-1]
    else:
        tail = text

    lines = [ln.strip() for ln in tail.splitlines()]
    insight_lines: List[str] = []
    for ln in lines:
        if ln.startswith("- "):
            insight_lines.append(ln)

    # 如果没有符合格式的行，则退化为返回最后一块的非空行
    if not insight_lines:
        insight_lines = [ln for ln in lines if ln]

    return "\n".join(insight_lines)

Fixed_fewshot_examples_of_Target_Task = [
"""Question: 
def process_string(t):
    \"\"\"You are given a string t.
    if t[i] is a digit, replace it with its complement to 9 (9 - digit), 
    otherwise keep it as it is.
    If the string contains no digits, convert the entire string to uppercase.
    The function should return the resulted string.
    Examples
    process_string("abc") = "ABC"
    process_string("123") = "876"
    process_string("#8@9") = "#1@0"
    \"\"\"

Thought 1: The problem has two core logic branches: digit complement replacement, and full uppercase conversion if no digits exist. I need to first iterate through the string to process digits, then check the digit existence flag to decide the final output.
Action 1: Reason[Step 1: Initialize a flag to track if any digit exists (default 0), convert string to list for mutable access. Step 2: Iterate over each character, if it's a digit, replace it with 9 - int(digit) and set the flag to 1. Step 3: Reconstruct the string from the processed list. Step 4: If flag remains 0 (no digits), convert to uppercase; else return the processed string.]
Observation 1: OK.

Thought 2: Now define the basic function skeleton with loop structure for character processing (matching the problem's function definition style).
Action 2: Implement[
def process_string(t):
    \"\"\"Process string digit replacement or full uppercase conversion based on digit existence.\"\"\"
    has_digit = 0
    char_list = list(t)
    for idx, char in enumerate(char_list):
        if char.isdigit():
            char_list[idx] = str(9 - int(char))
            has_digit = 1
]
Observation 2: OK.

Thought 3: Verify the core logic with example inputs to ensure correctness before finalizing.
Action 3: Verify[
# Test digit replacement logic
char_list = list("#8@9")
has_digit = 0
for idx, char in enumerate(char_list):
    if char.isdigit():
        char_list[idx] = str(9 - int(char))
        has_digit = 1
assert ''.join(char_list) == "#1@0"  # Matches example
# Test no-digit uppercase condition
has_digit = 0
assert has_digit == 0 → need to convert "abc" to "ABC"
]
Observation 3: OK.

Thought 4: Complete the full function implementation with all logic and return statements.
Action 4: Finish[
def process_string(t):
    \"\"\"You are given a string t.
    if t[i] is a digit, replace it with its complement to 9 (9 - digit), 
    otherwise keep it as it is.
    If the string contains no digits, convert the entire string to uppercase.
    The function should return the resulted string.
    Examples
    process_string("abc") = "ABC"
    process_string("123") = "876"
    process_string("#8@9") = "#1@0"
    \"\"\"
    flg = 0
    idx = 0
    new_str = list(t)
    for i in t:
        if i.isdigit():
            new_str[idx] = str(9 - int(i))
            flg = 1
        idx += 1
    t = ""
    for i in new_str:
        t += i
    if flg == 0:
        return t.upper()
    return t
]
Observation 4: Answer is CORRECT
""",
"""Question: 
def string_to_sha256(content):
    \"\"\"
    Given a string 'content', return its sha256 hash equivalent string.
    If 'content' is an empty string, return None.

    >>> string_to_sha256('Python') == '11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1'
    \"\"\"

Thought 1: The problem requires SHA256 hash computation with a boundary condition (empty string). I need to import the hashlib module, handle encoding, compute the hash, and add the empty string check.
Action 1: Reason[Step 1: Import hashlib for SHA256 computation. Step 2: Check if input content is empty → return None. Step 3: Encode content to UTF-8 (required for hashlib). Step 4: Compute SHA256 hash and convert to hexadecimal string. Step 5: Return the hex string.]
Observation 1: OK.

Thought 2: Define the function skeleton with core condition structure (matching the problem's function definition style).
Action 2: Implement[
def string_to_sha256(content):
    \"\"\"Return SHA256 hash string of content, or None if content is empty.\"\"\"
    import hashlib
    if not content:
        return None
    # Hash computation logic here
]
Observation 2: OK.

Thought 3: Verify the core hash logic and boundary condition with test cases.
Action 3: Verify[
# Test empty string condition
assert string_to_sha256("") is None  # Correct boundary handling
# Test hash computation
import hashlib
test_hash = hashlib.sha256('Python'.encode('utf-8')).hexdigest()
assert test_hash == '11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1'  # Matches example
]
Observation 3: OK.

Thought 4: Complete the full function with all logic and docstring.
Action 4: Finish[
def string_to_sha256(content):
    \"\"\"
    Given a string 'content', return its sha256 hash equivalent string.
    If 'content' is an empty string, return None.

    >>> string_to_sha256('Python') == '11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1'
    \"\"\"
    import hashlib
    return hashlib.sha256(content.encode('utf-8')).hexdigest() if content else None
]
Observation 4: Answer is CORRECT
""",
"""Question: 
def generate_odd_numbers(x, y):
    \"\"\"
    Given two positive integers x and y, return the odd digits between x
    and y, in ascending order.

    For example:
    generate_odd_numbers(1, 9) => [1, 3, 5, 7, 9]
    generate_odd_numbers(9, 1) => [1, 3, 5, 7, 9]
    generate_odd_numbers(10, 18) => []
    \"\"\"

Thought 1: The problem needs to normalize the input range (min/max), filter odd numbers within 1-9, and return sorted result. The key is to first fix the range boundary, then apply odd filter.
Action 1: Reason[Step 1: Find lower bound (max of 1 and min(x,y)) and upper bound (min of 9 and max(x,y)). Step 2: Generate a list of numbers from lower to upper (inclusive). Step 3: Filter only odd numbers from the list. Step 4: Return the filtered list (already ascending).]
Observation 1: OK.

Thought 2: Complete the full function with all logic and docstring.
Action 2: Finish[
def generate_odd_numbers(x, y):
    \"\"\"
    Given two positive integers x and y, return the odd digits between x
    and y, in ascending order.

    For example:
    generate_odd_numbers(1, 9) => [1, 3, 5, 7, 9]
    generate_odd_numbers(9, 1) => [1, 3, 5, 7, 9]
    generate_odd_numbers(10, 18) => []
    \"\"\"
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    return [i for i in range(lower, upper+1) if i % 2 == 1]
]   
Observation 2: Answer is CORRECT
"""
]
Fixed_fewshot_examples_of_Target_Task = '\n\n'.join(Fixed_fewshot_examples_of_Target_Task)

Target_Task_description = """You are Code problem-solving system. Thought reasons about the problem at a high level. Before writing detailed code, identify the overall structure, strategy, or reusable pattern of the solution. Focus on reasoning patterns that could be reused across similar problems.
Action can be:
(1) Reason[step], which explains a logical, algorithmic, or structural step without writing full code. Reason steps should form a clear procedure that could be directly translated into a correct program.
(2) Implement[pattern], which defines a function skeleton, loop structure, condition, or basic code block following standard Python syntax and type hints.
(3) Verify[case], which checks the logic against one or more example inputs and outputs to confirm correctness.
(4) Finish[code], which is necessary and required to complete the Python code (including function definition with type hints, docstring, and complete implementation logic) and ends the task.
You may take maximum of 5 steps.
Here are some examples:
"""

Insights_Path = r"C:\Users\HUAWEI\Desktop\ExpeL\logs\math2code_math\expel\extracted_insights\insights-mathscode-run-glm-expel.txt"
Target_Task_File = r"C:\Users\HUAWEI\Desktop\ExpeL\data\math2code\human-eval-v2-20210705.jsonl"
def extract_finish_code(completion_text):
    """
    提取 Finish[] 中最后一个块的代码内容（支持代码内包含 ]）
    :param completion_text: 包含 Finish[code] 的文本
    :return: 提取的代码字符串（去除首尾空白），无匹配时返回空字符串
    """
    # 正则解释：
    # (?is) ：i=忽略大小写，s=让.匹配换行符
    # Finish\[ ：匹配 Finish[（[需要转义）
    # (.*) ：贪婪匹配任意字符（直到最后一个 ]）
    # (?=]$|\s*$) ：正向断言，确保 ] 是行尾/文本尾（或后续只有空白）
    pattern = r"(?is)Finish\[(.*)]\s*$"
    
    # 先找所有 Finish[ 开头的匹配
    matches = list(re.finditer(r"(?is)Finish\[", completion_text))
    if not matches:
        return ""
    
    # 取最后一个 Finish[ 的位置，从该位置开始截取文本
    last_match_start = matches[-1].start()
    target_text = completion_text[last_match_start:]
    
    # 对截取后的文本匹配完整的 Finish[code]
    code_match = re.match(pattern, target_text)
    if code_match:
        return code_match.group(1).strip()
    return ""

def clear_code(code: str) -> str:
    # 清除前缀python、py、```等标记，以及前后多余的空白
    code = re.sub(r"^(?:python|py|```python)?\s*", "", code)
    code = re.sub(r"\s*```$", "", code)
    return code

def summarize_insights(source_task: str, target_task: str) -> str:
    """
    第一步：把从源任务抽取的 rules 总结成一段适用于目标任务的提示。
    """
    raw_insights = extract_insights(Insights_Path)
    print("提取到的insights:", raw_insights)
    for i in range(3):
        try:
            prompt = Knowledge_Finetuning_prompt_template.format(
                Source_Task=source_task,
                Extracted_insights=raw_insights,
                Target_Task=target_task,
                Fixed_fewshot_examples_of_Target_Task=Fixed_fewshot_examples_of_Target_Task,
            )
            messages = [{"role": "user", "content": prompt}]
            output = generate_one_completion(messages)
            if output == "":
                print(f"\nAPI call failed, retrying {i+1}/3...")
                time.sleep(2)
                continue
            return output.strip()
        except openai.error.RateLimitError:
            print(f"\nRate limit error, retrying {i+1}/3...")
            time.sleep(2)
    raise RuntimeError("Failed to generate summarized insights after 3 attempts")


def check_humaneval_completion(problem: Dict[str, Any], completion: str) -> Tuple[bool, str]:
    """
    第二步：参考 human-eval 的 execution.py，对单个 completion 做功能正确性检查。

    这里使用简化实现：
    - 构造程序 = problem['prompt'] + completion + test + check(entry_point)
    - exec 运行，捕获 AssertionError / Exception
    - 不使用多线程，也不引入复杂沙箱，仅用于离线评测。
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
    主流程：
    1）从 ExpeL 日志中抽取 rules，并总结成适用于 HumanEval code generation 的段落；
    2）遍历 HumanEval（code_tasks.jsonl），对每个任务构造 prompt 调用大模型生成代码；
    3）执行 HumanEval 测试脚本评测生成代码是否通过；
    4）统计 pass@1（= 通过任务数 / 总任务数）。
    """
    # 1. 汇总从 math2code_math 得到的经验到 code generation 任务
    finetuned_insights = summarize_insights(
        source_task="math problem-solving",
        target_task="code generation",
    )
    print("\n===== Finetuned Insights =====\n")
    print(finetuned_insights)
    print("\n==============================\n")

    results: List[Dict[str, Any]] = []

    # 生成带时间戳的输出文件名
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    predictions_path = f"humaneval_{MODEL_NAME}_{timestamp}_predictions_expel.jsonl"
    simple_results_path = f"humaneval_{MODEL_NAME}_{timestamp}_predictions_expel_simple_results.jsonl"

    # 2. 遍历 HumanEval / math2code 任务，逐个生成 & 评测
    simple_records: List[Dict[str, Any]] = []
    with open(Target_Task_File, "r", encoding="utf-8") as f_in, \
            open(predictions_path, "w", encoding="utf-8") as f_pred:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            problem = json.loads(line)
            task_id = problem.get("task_id", "UNKNOWN")
            question_prompt = problem.get("prompt", "").strip()

            prompt = Knowledge_transfer_prompt_template.format(
                Target_Task="code generation",
                Finetuned_insights=finetuned_insights,
                Target_Task_description=Target_Task_description,
                Fixed_fewshot_examples_of_Target_Task=Fixed_fewshot_examples_of_Target_Task,
                Target_Task_Question=question_prompt,
            )

            messages = [{"role": "user", "content": prompt}]
            print("\nmessages: ", messages, "-" * 100)

            # 为每个 HumanEval 任务生成一次 completion（n=1，用于 pass@1）
            completion_text = ""
            for i in range(3):
                try:
                    completion_text = generate_one_completion(messages)
                    if completion_text == "":
                        print(f"\n[{task_id}] API call failed, retrying {i+1}/3...")
                        time.sleep(2)
                        continue
                    break
                except openai.error.RateLimitError:
                    print(f"\n[{task_id}] Rate limit error, retrying {i+1}/3...")
                    time.sleep(2)
            else:
                print(f"[{task_id}] Failed to get completion after 3 attempts, mark as failed.")
                results.append(
                    {
                        "task_id": task_id,
                        "completion": completion_text,
                        "passed": False,
                        "result": "API failure",
                    }
                )
                # 预测文件中也写入一个空 completion 记录
                f_pred.write(
                    json.dumps({"task_id": task_id, "completion": completion_text}, ensure_ascii=False)
                    + "\n"
                )
                simple_records.append(
                    {
                        "task_id": task_id,
                        "results": [
                            {
                                "task_id": task_id,
                                "passed": False,
                                "result": "API failure",
                                "completion_id": None,
                            }
                        ],
                    }
                )
                continue

            completion_text = completion_text.strip()
            print("\n==============================")
            print(f"[{task_id}] completion={completion_text}")
            
            step = 5
            for 
            # 1) 使用正则提取最后一个 Finish[code] 中的 code 内容
            code_for_exec = extract_finish_code(completion_text)
            code_for_exec = clear_code(code_for_exec)
                
            print("\n==============================")
            print(f"[{task_id}] code extracted for execution:\n{code_for_exec}")
            
            # 2) 将用于执行的 code 写入 predictions_expel.jsonl
            f_pred.write(
                json.dumps({"task_id": task_id, "completion": code_for_exec, "answer":completion_text}, ensure_ascii=False) + "\n"
            )

            passed, detail = check_humaneval_completion(problem, code_for_exec)
            print(f"[{task_id}] passed={passed}, detail={detail}")

            results.append(
                {
                    "task_id": task_id,
                    "completion": code_for_exec,
                    "passed": passed,
                    "result": detail,
                }
            )

            # simple_results 结构与 human-eval simple_results 格式对齐
            simple_records.append(
                {
                    "task_id": task_id,
                    "results": [
                        {
                            "task_id": task_id,
                            "passed": passed,
                            "result": detail,
                            "completion_id": None,
                        }
                    ],
                }
            )

    # 3. 计算 pass@1（每个任务只采样 1 次）
    total = len(results)
    correct = sum(1 for r in results if r["passed"])
    pass_at_1 = (correct / total) if total > 0 else 0.0

    print("\n========== Evaluation Summary ==========")
    print(f"Total tasks: {total}")
    print(f"Passed tasks: {correct}")
    print(f"pass@1: {pass_at_1:.4f}")

    # 4. 写出每个任务的详细结果和 simple_results 方便之后排查
    out_path = "transfer_humaneval_results.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Per-task results written to: {out_path}")

    with open(simple_results_path, "w", encoding="utf-8") as f:
        for rec in simple_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Simplified results written to: {simple_results_path}")


if __name__ == "__main__":
    run_transfer_and_eval()