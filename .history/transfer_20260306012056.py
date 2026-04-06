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

Give a concise and easy to follow instructional paragraph based on the RULES for the student agent to solve {Target_Task}. Do not state where each sentence is using whichever rule, and make sure the paragraph is VERY CONCISE and EASY TO FOLLOW!
"""

Knowledge_transfer_prompt_template = """The following paragraph is insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the {Target_Task} tasks efficiently:

{Finetuned_insights}

{Target_Task_description}\{Fixed_fewshot_examples_of_Target_Task}

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

Fixed_fewshot_examples_of_Target_Task = """Question: 
def solve(s):
    \"\"\"You are given a string s.
    if s[i] is a letter, reverse its case from lower to upper or vise versa, 
    otherwise keep it as it is.
    If the string contains no letters, reverse the string.
    The function should return the resulted string.
    Examples
    solve("1234") = "4321"
    solve("ab") = "AB"
    solve("#a@C") = "#A@c"
    \"\"\"

Thought 1: The problem has two core logic branches: case reversal for letters, and full string reversal if no letters exist. I need to first iterate through the string to process letters, then check the letter existence flag to decide the final output.
Action 1: Reason[Step 1: Initialize a flag to track if any letter exists (default 0), convert string to list for mutable access. Step 2: Iterate over each character, if it's a letter, swap its case and set the flag to 1. Step 3: Reconstruct the string from the processed list. Step 4: If flag remains 0 (no letters), reverse the string; else return the processed string.]
Observation 1: OK.

Thought 2: Now define the basic function skeleton with loop structure for character processing (matching the problem's function definition style).
Action 2: Implement[
def solve(s):
    \"\"\"Process string case reversal or full reversal based on letter existence.\"\"\"
    has_letter = 0
    char_list = list(s)
    for idx, char in enumerate(char_list):
        if char.isalpha():
            char_list[idx] = char.swapcase()
            has_letter = 1
]
Observation 2: OK.

Thought 3: Verify the core logic with example inputs to ensure correctness before finalizing.
Action 3: Verify[
# Test letter case reversal
char_list = list("#a@C")
has_letter = 0
for idx, char in enumerate(char_list):
    if char.isalpha():
        char_list[idx] = char.swapcase()
        has_letter = 1
assert ''.join(char_list) == "#A@c"  # Matches example
# Test no-letter reversal condition
has_letter = 0
assert has_letter == 0 → need to reverse "1234" to "4321"
]
Observation 3: OK.

Thought 4: Complete the full function implementation with all logic and return statements.
Action 4: Finish[
def solve(s):
    \"\"\"You are given a string s.
    if s[i] is a letter, reverse its case from lower to upper or vise versa, 
    otherwise keep it as it is.
    If the string contains no letters, reverse the string.
    The function should return the resulted string.
    Examples
    solve("1234") = "4321"
    solve("ab") = "AB"
    solve("#a@C") = "#A@c"
    \"\"\"
    flg = 0
    idx = 0
    new_str = list(s)
    for i in s:
        if i.isalpha():
            new_str[idx] = i.swapcase()
            flg = 1
        idx += 1
    s = ""
    for i in new_str:
        s += i
    if flg == 0:
        return s[len(s)::-1]
    return s
]
"""
Target_Task_description = """You are Code problem-solving system. Thought reasons about the problem at a high level. Before writing detailed code, identify the overall structure, strategy, or reusable pattern of the solution. Focus on reasoning patterns that could be reused across similar problems.
Action can be:
(1) Reason[step], which explains a logical, algorithmic, or structural step without writing full code. Reason steps should form a clear procedure that could be directly translated into a correct program.
(2) Implement[pattern], which defines a function skeleton, loop structure, condition, or basic code block following standard Python syntax and type hints.
(3) Verify[case], which checks the logic against one or more example inputs and outputs to confirm correctness.
(4) Finish[code], which requires to complete the following Python code (including function definition with type hints, docstring, and complete implementation logic) and ends the task.
You may take maximum of 5 steps.
Here are some examples:
"""

Insights_Path = r"C:\Users\HUAWEI\Desktop\ExpeL\logs\math2code_math\expel\extracted_insights\insights-mathscode-run-glm-expel.txt"
Target_Task_File = r"C:\Users\HUAWEI\Desktop\ExpeL\data\math2code\human-eval-v2-20210705.jsonl"


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
            

            # 1) 使用正则提取最后一个 Finish[code] 中的 code 内容
            code_for_exec = completion_text
            pattern = r"(?is)Finish\[(.*?)]"
            matches = list(re.finditer(pattern, completion_text))
            if matches:
                last = matches[-1]
                code_for_exec = last.group(1).strip()
                
            print("\n==============================")
            print(f"[{task_id}] code extracted for execution:\n{code_for_exec}")
            
            # 2) 将用于执行的 code 写入 predictions_expel.jsonl
            f_pred.write(
                json.dumps({"task_id": task_id, "completion": code_for_exec}, ensure_ascii=False) + "\n"
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