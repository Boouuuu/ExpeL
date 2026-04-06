import json
import openai
import time

def replace_invalid_roles(messages):
    """
    批量替换messages中的非法角色名：
    - human → user（用户角色）
    - ai → assistant（助手/AI角色）
    支持嵌套结构，深拷贝保护原数据
    
    Args:
        messages (list): 原始消息列表，每个元素是含"role"键的字典
    
    Returns:
        list: 替换后的合法消息列表
    """
    import copy
    processed_messages = copy.deepcopy(messages)
    
    # 定义非法角色到合法角色的映射
    role_mapping = {
        "human": "user",    # 人类提问者 → user
        "ai": "assistant"   # AI回复者 → assistant
    }
    
    for msg in processed_messages:
        # 仅处理字典类型且包含role字段的元素
        if isinstance(msg, dict) and "role" in msg:
            # 如果当前role在映射表中，替换为合法值
            if msg["role"] in role_mapping:
                msg["role"] = role_mapping[msg["role"]]
    
    return processed_messages
def generate_one_completion(messages):
    # jiajia
    # openai.api_key = "sk-a3b1a801d70747a0b7d3b2797a14ab05"
    openai.api_key = "sk-afa113e744a345899ad27f3452c08ffa"
    openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    messages = replace_invalid_roles(messages)
    # completion = client.chat.completions.create(
    completion = openai.ChatCompletion.create(
        model="glm-4.6",
        messages=messages,
        extra_body={"enable_thinking": False},
        stream=False,
        temperature=0.2,  # 新增：可选，控制回复随机性
        max_tokens=4096,   # 新增：可选，限制回复长度
        headers={
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }
    )
    # print(f"\n🔹 Generating for task: {task_id}")
    # 修正：直接取属性，而非转JSON字符串（更高效）
    return completion.choices[0].message.content

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

{Target_Task_description}{Fixed_fewshot_examples_of_Target_Task}

{Target_Task_Question}
"""
def extract_insights(insights_path):
    return 
    

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

Insights_Path = r"C:\Users\HUAWEI\Desktop\ExpeL\data\math2code\insights.jsonl"
Target_Task_File = r"C:\Users\HUAWEI\Desktop\ExpeL\data\math2code\code_tasks.jsonl"

if __name__ == "__main__": 
    for i in range(3):
        try:
            output = generate_one_completion(Knowledge_Finetuning_prompt_template.format(
                Source_Task = "math problem-solving",
                Extracted_insights = extract_insights(Insights_Path),
                Target_Task = "code generation",
                Fixed_fewshot_examples_of_Target_Task = Fixed_fewshot_examples_of_Target_Task
            ))
            if output == "":  # API调用失败
                print(f'\nAPI call failed, retrying {i+1}/6...')
                time.sleep(2)  # 等待2秒后重试
                continue
            Finetuned_insights = output.strip('\n').strip()
            break
        except openai.error.RateLimitError:
            print(f'\nRate limit error, retrying {i+1}/6...')
            time.sleep(2)
    else:
        raise RuntimeError('Failed to generate response after 6 attempts')

# 遍历Target_Task_File
    with open(Target_Task_File, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            prompt= Knowledge_transfer_prompt_template.format(
                Target_Task = "code generation",
                Finetuned_insights = Finetuned_insights,
                Target_Task_description = Target_Task_description,
                Fixed_fewshot_examples_of_Target_Task = Fixed_fewshot_examples_of_Target_Task,
                Target_Task_Question = item.get('prompt', '').strip(),
                
            )
            print("prompt:", prompt)
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Please provide a concise and easy to follow instructional paragraph based on the RULES for the student agent to solve the task."}
            ]
            try:
                output = generate_one_completion(messages)
    