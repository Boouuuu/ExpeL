"""Code2Math 训练阶段：纯代码生成问题解答。Thought / Action / Observation"""
from typing import Tuple, Dict, Any, List
import re

FEWSHOTS = ["""Question:
def process_string(t):
    \"\"\"You are given a string t.
    If t[i] is a digit, replace it with its complement to 9 (9 - digit).
    Otherwise keep it unchanged.
    If the string contains no digits, convert the entire string to uppercase.
    Return the resulting string.
    Examples:
    process_string("123") == "876"
    process_string("#8@9") == "#1@0"
    process_string("abc") == "ABC"
    \"\"\"

Thought 1:
First, I analyze the requirement: this is a string transformation task with a conditional branch:
- If digits exist → replace digits
- If no digits → convert entire string to uppercase
We must track whether any digit appears. I will first implement and then verify using tests.

Step-by-step plan:
1. Traverse the string character by character
2. If a character is a digit, replace it with (9 - digit)
3. Otherwise keep it unchanged
4. Track whether any digit appears
5. If no digit appears, convert the entire string to uppercase

Test design:
- Case 1: only digits (e.g., "123")
- Case 2: mixed characters (e.g., "#8@9")
- Case 3: no digits (e.g., "abc") → should trigger uppercase

Action 1: Test[
def process_string(t):
    res = []
    for ch in t:
        if ch.isdigit():
            res.append(str(9 - int(ch)))
        else:
            res.append(ch)
    return ''.join(res)

assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
assert process_string("abc") == "ABC"
]

Observation 1:
Tests passing:
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"

Tests failing:
assert process_string("abc") == "ABC" # output: "abc"

Thought 2:
The failure occurs for inputs without digits. The current implementation never checks whether digits exist, so it skips the uppercase requirement.

Fix strategy:
- Introduce a flag to track whether any digit appears
- If no digit appears, convert the result to uppercase before returning

Action 2: Test[
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

assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
assert process_string("abc") == "ABC"
assert process_string("") == ""
]

Observation 2:
Tests passing:
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
assert process_string("abc") == "ABC"
assert process_string("") == ""

Tests failing:
None

Thought 3:
All cases pass, including edge case (empty string). I will finish the implementation.

Action 3: Finish[
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

Observation 3: Answer is correct.
""",

"""Question:
def string_to_sha256(content):
    \"\"\"
    Return sha256 hash of content, or None if empty
    Examples:
    string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"
    string_to_sha256("") == None
    \"\"\"

Thought 1:
First, I analyze the requirement: this function needs to compute the SHA256 hash of input content and return None when the content is empty. I will use Python's built-in hashlib library, which is the standard tool for SHA256 hashing. I will first implement and then verify using tests. 

Step-by-step plan:
1. Check if content is empty → return None
2. Encode content to utf-8
3. Compute sha256 hash
4. Return hexadecimal string

Test design:
- Case 1: empty string → None
- Case 2: known input with known hash (e.g., "Python")

Action 1: Test[
def string_to_sha256(content):
    import hashlib
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

assert string_to_sha256("") is None
assert string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"
]

Observation 1:
Tests passing:
assert string_to_sha256("") is None
assert string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"

Tests failing:
None

Thought 2:
All test cases pass, including boundary condition. I will finish the implementation.

Action 2: Finish[
def string_to_sha256(content):
    import hashlib
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
]

Observation 2: Answer is correct.
""",


"""Question:
def generate_odd_numbers(x, y):
    \"\"\"
    Return all odd numbers between x and y that lie within 1 to 9 (inclusive), sorted ascending
    Examples:
    generate_odd_numbers(1, 9) == [1,3,5,7,9]
    generate_odd_numbers(9, 1) == [1,3,5,7,9]
    generate_odd_numbers(0, 5) == [1,3,5]
    generate_odd_numbers(10, 12) == []
    \"\"\"

Thought 1:
First, I analyze the problem requirements: the function needs to return all odd numbers between x and y, and these numbers must be within the range 1 to 9 inclusive, then return them sorted in ascending order. I need to handle two key constraints: limit the valid range to 1–9, and filter only odd numbers. I will first implement and then verify using tests. 

Step-by-step plan:
1. Determine lower and upper bounds from x and y
2. Restrict the range to [1, 9]
3. Iterate through the range
4. Select only odd numbers

Test design:
- Case 1: normal range (1,9)
- Case 2: reversed range (9,1)
- Case 3: partially out-of-bound (0,5)
- Case 4: fully out-of-bound (10,12)

Action 1: Test[
def generate_odd_numbers(x, y):
    lower = min(x, y)
    upper = max(x, y)
    return [i for i in range(lower, upper+1) if i % 2 == 1]

assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
assert generate_odd_numbers(0, 5) == [1,3,5]
assert generate_odd_numbers(10, 12) == []
]

Observation 1:
Tests passing:
assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
assert generate_odd_numbers(9, 1) == [1,3,5,7,9]

Tests failing:
assert generate_odd_numbers(0, 5) == [1,3,5] # output: [1,3,5]
assert generate_odd_numbers(10, 12) == [] # output: [11]

Thought 2:
The issue is that the implementation does not restrict values to the range [1,9].
- It incorrectly includes values like 11
- It does not explicitly enforce lower bound = 1 and upper bound = 9

Fix strategy:
- Clamp the range using max(1, ...) and min(9, ...)
- If lower > upper, return empty list

Action 2: Test[
def generate_odd_numbers(x, y):
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    if lower > upper:
        return []
    return [i for i in range(lower, upper+1) if i % 2 == 1]

assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
assert generate_odd_numbers(0, 5) == [1,3,5]
assert generate_odd_numbers(10, 12) == []
]

Observation 2:
Tests passing:
assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
assert generate_odd_numbers(0, 5) == [1,3,5]
assert generate_odd_numbers(10, 12) == []

Tests failing:
None

Thought 3:
All test cases pass after enforcing the valid range constraint. I will finish the implementation.

Action 3: Finish[
def generate_odd_numbers(x, y):
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    if lower > upper:
        return []
    return [i for i in range(lower, upper+1) if i % 2 == 1]
]

Observation 3: Answer is correct.
"""
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
    Examples
    solve("1234") = "4321"
    solve("ab") = "AB"
    solve("#a@C") = "#A@c"
    \"\"\"
Thought 1: Just swap case for letters and reverse if no letters.
Action 1: Finish[
def solve(s):
    return s[::-1] if not any(c.isalpha() for c in s) else ''.join(c.swapcase() if c.isalpha() else c for c in s)
]
Observation 1: Answer is incorrect.

Reflection: I directly wrote the concise one-line solution but skipped breaking down the reasoning into reusable algorithmic steps. I should have first outlined the step-by-step logic (initialize flag, iterate through characters, update flag) that could be translated into a structured program and verified test cases, instead of jumping to the final code.
""",
"""
Previous Trial:
Question: 
def string_to_md5(text):
    \"\"\"
    Given a string 'text', return its md5 hash equivalent string.
    If 'text' is an empty string, return None.

    >>> string_to_md5('Hello world') == '3e25960a79dbc69b674cd4ec67a72c62'
    \"\"\"
Thought 1: Use hashlib to compute MD5 hash.
Action 1: Finish[
def string_to_md5(text):
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()
]

Reflection: I missed handling the empty string boundary condition and skipped verifying the logic with test cases first. I should have first defined the condition check (if text is empty return None) as a separate Reason step, then verified it with an empty string test case before finalizing the code.
"""
]

SYSTEM_INSTRUCTION = """Solve a programming problem using interleaved Thought, Action, Observation steps. Thought can reason about the current situation, and Action can be of two types:
(1) Test[code], which sends code to a Python interpreter for execution. The code should include the function implementation and assert-based test cases that call the function. The system will execute the code and return the result as Observation.
(2) Finish[answer], which returns the final correct implementation and ends the task.

You should first generate a Thought, then choose an Action. After each Action, STOP and wait for Observation."""

human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving code completion problems: one successful and one unsuccessful. You failed either by giving a wrong answer with Finish[<code>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given successful code completion task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a previous code completion trial. You failed either by giving a wrong answer with Finish[<code>] or by using up the steps. In a few sentences, diagnose why you failed and give a concise plan to avoid the same failure. Focus on whether your reasoning was sufficiently structured, explicit, and reusable, rather than jumping directly to the answer. Use complete sentences."""

def LLM_PARSER(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
    pattern = r'(?i)action\s*(?:\d+|)\s*(?::|)\s*'
    action_pattern = r'(?i)\w+\[[^\]]+(?:\]|)'

    match = re.match(pattern, llm_output)
    if match:
        action = llm_output[match.end():]
        content = f"Action {step}: {action}"
        acts = re.findall(action_pattern, action)
        if len(acts) > 1:
            use_action = acts[-1]
            if use_action[-1] != ']':
                use_action += ']'
            return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': use_action}
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': action}

    actions = re.findall(action_pattern, llm_output)
    if len(actions) == 1:
        action = actions[0]
        if action[-1] != ']':
            action += ']'
        content = f"Action {step}: {action}"
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': action}
    if len(actions) > 1:
        use_action = actions[-1]
        if use_action[-1] != ']':
            use_action += ']'
        content = re.sub(r"(?i)action\s*(?:\d*|)\s*(?::|)", "", llm_output)
        return {'role': 'ai', 'content': f"Action {step}: {content}"}, 'action', {'action': use_action}

    thought_pattern = r'(?i)thought\s*(?:\d+|)\s*(?::|)\s*(.*)'
    match = re.match(thought_pattern, llm_output)
    if match:
        content = f"Thought {step}: {match.group(1).rstrip(':')}"
    else:
        content = f"Thought {step}: {llm_output.rstrip(':')}"
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
