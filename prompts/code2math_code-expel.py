"""Code2Math 训练阶段：纯代码生成问题解答。Thought / Action / Observation"""
from typing import Tuple, Dict, Any, List
import re

FEWSHOTS = ["""
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
]""",
"""
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
]""",
"""
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
""",

# """Question:
# def string_to_sha256(content):
#     \"\"\"
#     Return sha256 hash of content, or None if empty
#     Examples:
#     string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"
#     string_to_sha256("") == None
#     \"\"\"

# Thought 1:
# First, I analyze the requirement: this function needs to compute the SHA256 hash of input content and return None when the content is empty. I will use Python's built-in hashlib library, which is the standard tool for SHA256 hashing. I will first implement and then verify using tests. 

# Step-by-step plan:
# 1. Check if content is empty → return None
# 2. Encode content to utf-8
# 3. Compute sha256 hash
# 4. Return hexadecimal string

# Test design:
# - Case 1: empty string → None
# - Case 2: known input with known hash (e.g., "Python")

# Action 1: Test[
# def string_to_sha256(content):
#     import hashlib
#     if not content:
#         return None
#     return hashlib.sha256(content.encode('utf-8')).hexdigest()

# assert string_to_sha256("") is None
# assert string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"
# ]

# Observation 1:
# Tests passing:
# assert string_to_sha256("") is None
# assert string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"

# Tests failing:
# None

# Thought 2:
# All test cases pass, including boundary condition. I will finish the implementation.

# Action 2: Finish[
# def string_to_sha256(content):
#     import hashlib
#     if not content:
#         return None
#     return hashlib.sha256(content.encode('utf-8')).hexdigest()
# ]

# Observation 2: Answer is correct.""",

# """Question:
# def generate_odd_numbers(x, y):
#     \"\"\"
#     Return all odd numbers between x and y that lie within 1 to 9 (inclusive), sorted ascending
#     Examples:
#     generate_odd_numbers(1, 9) == [1,3,5,7,9]
#     generate_odd_numbers(9, 1) == [1,3,5,7,9]
#     generate_odd_numbers(0, 5) == [1,3,5]
#     generate_odd_numbers(10, 12) == []
#     \"\"\"

# Thought 1:
# First, I analyze the problem requirements: the function needs to return all odd numbers between x and y, and these numbers must be within the range 1 to 9 inclusive, then return them sorted in ascending order. I need to handle two key constraints: limit the valid range to 1–9, and filter only odd numbers. I will first implement and then verify using tests. 

# Step-by-step plan:
# 1. Determine lower and upper bounds from x and y
# 2. Restrict the range to [1, 9]
# 3. Iterate through the range
# 4. Select only odd numbers

# Test design:
# - Case 1: normal range (1,9)
# - Case 2: reversed range (9,1)
# - Case 3: partially out-of-bound (0,5)
# - Case 4: fully out-of-bound (10,12)

# Action 1: Test[
# def generate_odd_numbers(x, y):
#     lower = min(x, y)
#     upper = max(x, y)
#     return [i for i in range(lower, upper+1) if i % 2 == 1]

# assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
# assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
# assert generate_odd_numbers(0, 5) == [1,3,5]
# assert generate_odd_numbers(10, 12) == []
# ]

# Observation 1:
# Tests passing:
# assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
# assert generate_odd_numbers(9, 1) == [1,3,5,7,9]

# Tests failing:
# assert generate_odd_numbers(0, 5) == [1,3,5] # output: [1,3,5]
# assert generate_odd_numbers(10, 12) == [] # output: [11]

# Thought 2:
# The issue is that the implementation does not restrict values to the range [1,9].
# - It incorrectly includes values like 11
# - It does not explicitly enforce lower bound = 1 and upper bound = 9

# Fix strategy:
# - Clamp the range using max(1, ...) and min(9, ...)
# - If lower > upper, return empty list

# Action 2: Test[
# def generate_odd_numbers(x, y):
#     lower = max(1, min(x, y))
#     upper = min(9, max(x, y))
#     if lower > upper:
#         return []
#     return [i for i in range(lower, upper+1) if i % 2 == 1]

# assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
# assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
# assert generate_odd_numbers(0, 5) == [1,3,5]
# assert generate_odd_numbers(10, 12) == []
# ]

# Observation 2:
# Tests passing:
# assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
# assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
# assert generate_odd_numbers(0, 5) == [1,3,5]
# assert generate_odd_numbers(10, 12) == []

# Tests failing:
# None

# Thought 3:
# All test cases pass after enforcing the valid range constraint. I will finish the implementation.

# Action 3: Finish[
# def generate_odd_numbers(x, y):
#     lower = max(1, min(x, y))
#     upper = min(9, max(x, y))
#     if lower > upper:
#         return []
#     return [i for i in range(lower, upper+1) if i % 2 == 1]
# ]

# Observation 3: Answer is correct."""
]


REFLECTION_FEWSHOTS = [
"""Previous Trial:
Question: 
def solve(s):
    \"\"\"You are given a string s.
    if s[i] is a letter, reverse its case from lower to upper or vise versa, 
    otherwise keep it as it is.
    If the string contains no letters, reverse the string.
    The function should return the resulted string.
    Examples:
    solve("1234") == "4321"
    solve("ab") == "AB"
    solve("#a@C") == "#A@c"
    \"\"\"
Thought 1: Just swap case for letters and reverse if no letters.
Action 1: Finish[
def solve(s):
    return s[::-1] if not any(c.isalpha() for c in s) else ''.join(c.swapcase() if c.isalpha() else c for c in s)
]
Observation 1: Answer is incorrect.

Reflection: I directly wrote the concise one-line solution but skipped breaking down the reasoning into reusable algorithmic steps. I should have first outlined the step-by-step logic (initialize flag, iterate through characters, update flag) that could be translated into a structured program and verified by test cases, instead of jumping to the final code.
""",
# """
# Previous Trial:
# Question: 
# def string_to_md5(text):
#     \"\"\"
#     Given a string 'text', return its md5 hash equivalent string.
#     If 'text' is an empty string, return None.
#     Examples:
#     string_to_md5('Hello world') == '3e25960a79dbc69b674cd4ec67a72c62'
#     \"\"\"
# Thought 1: Use hashlib to compute MD5 hash.
# Action 1: Finish[
# def string_to_md5(text):
#     import hashlib
#     return hashlib.md5(text.encode()).hexdigest()
# ]

# Reflection: I missed handling the empty string boundary condition and skipped verifying the logic with test cases first. When a problem includes explicit edge cases, I should first define the condition check (return None if the text is empty) as a separate step, then verify it with an empty string test case before finalizing the code."""
]

SYSTEM_INSTRUCTION = """Solve a programming problem with interleaving Thought, Action, Observation steps.
Thought can reason about the problem, analyze requirements, and design the solution.
Action has only one type:
(1) Finish[code], which submits the final complete Python implementation and finishes the task.

After each observation, provide the next Thought and next Action."""

human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""+ '\n'.join(FEWSHOTS)

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving code completion problems: one successful and one unsuccessful. You failed either by giving a wrong answer with Finish[<code>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given successful code completion task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a previous code completion trial. You failed either by giving a wrong answer with Finish[<code>] or by using up the steps. In a few sentences, diagnose why you failed and give a concise guide to avoid the same failure. Focus on whether your reasoning was sufficiently structured, explicit, and reusable, rather than jumping directly to the answer. Use complete sentences."""

def _strip_leaked_observation_suffix(s: str) -> str:
    """stop=Observation 时可能残留 Observation / Observ 片段，从 Action 尾部去掉。"""
    if not s:
        return s
    parts = re.split(r'(?i)\bobserv', s, maxsplit=1)
    return parts[0].rstrip()


def LLM_PARSER(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
    # Check if the output contains both Thought and Action
    thought_pattern = r'(?i)thought\s*(?:\d+|)\s*(?::|)\s*'
    action_pattern = r'(?i)action\s*(?:\d+|)\s*(?::|)\s*'
    
    thought_match = re.search(thought_pattern, llm_output)
    action_match = re.search(action_pattern, llm_output)
    
    if action_match:
        blocks: List[str] = []
        if thought_match and thought_match.start() < action_match.start():
            thought_body = llm_output[thought_match.end() : action_match.start()].strip()
            thought_body = re.sub(r'\n{3,}', '\n\n', thought_body)
            blocks.append(f"Thought {step}:\n{thought_body}")

        action_content = llm_output[action_match.end() :].strip()
        action_content = _strip_leaked_observation_suffix(action_content)

        from utils import parse_action
        action_type, parsed_action = parse_action(action_content)

        if action_type and parsed_action:
            full_action = f"{action_type}[{parsed_action}]"
            display_tail = full_action
        else:
            display_tail = action_content

        blocks.append(f"Action {step}: {display_tail}")
        content = "\n\n".join(blocks)

        if action_type and parsed_action:
            return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': full_action}
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': action_content}
    
    elif thought_match:
        # Only thought exists
        thought_content = llm_output[thought_match.end():].strip()
        thought_content = re.sub(r'\n{3,}', '\n\n', thought_content).strip()
        content = f"Thought {step}:\n{thought_content}"
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'thought', {}
    
    # No clear patterns, try to parse as action
    from utils import parse_action
    action_type, parsed_action = parse_action(llm_output)
    
    if action_type and parsed_action:
        full_action = f"{action_type}[{parsed_action}]"
        content = f"Action {step}: {full_action}"
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': full_action}
    
    # Default to thought
    content = f"Thought {step}: {llm_output.strip()}"
    return {'role': 'ai' if ai_message else 'human', 'content': content}, 'thought', {}

def OBSERVATION_FORMATTER(observation: str, step: int, *args, **kwargs) -> Tuple[dict, str]:
    return {'role': 'human', 'content': f"Observation {step}: " + observation.rstrip(':')}, 'append'

def STEP_IDENTIFIER(line: str) -> str:
    line = line.strip()
    if re.compile(r'^(?i)action(?:\s+(\d+))?:').match(line):
        return 'action'
    if re.compile(r'^(?i)observation(?:\s+(\d+))?:').match(line):
        return 'observation'
    return 'thought'

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

REFLECTION_PREFIX = '\nReflection:'

def PREVIOUS_TRIALS_FORMATTER(reflections: List[str], include_prefix: bool = True) -> str:
    if not reflections:
        return ''
    memory_prefix = "You have attempted to solve the task before but failed. The following reflection(s) give a plan to avoid failing the same way. Use them to improve.\nReflections:" if include_prefix else ""
    for r in reflections:
        memory_prefix += f"\n- {r.strip()}"
    return memory_prefix

def STEP_STRIPPER(step: str, step_type: str) -> str:
    if step_type == 'observation':
        return re.sub(r'^(?i)observation(?:\s+(\d+))?:', 'Observation:', step)
    if step_type == 'action':
        return re.sub(r'^(?i)action(?:\s+(\d+))?:', 'Action:', step)
    if step_type == 'thought':
        return re.sub(r'^(?i)thought(?:\s+(\d+))?:', 'Thought:', step)
    return step
