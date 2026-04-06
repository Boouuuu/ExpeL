"""Code2Math 训练阶段：纯代码生成问题解答。Thought / Reason / Implement / Finish，无编程。"""
from typing import Tuple, Dict, Any, List
import re

FEWSHOTS = [
"""Question:
def process_string(t):
    """You are given a string t.
    If t[i] is a digit, replace it with its complement to 9 (9 - digit).
    Otherwise keep it unchanged.
    If the string contains no digits, convert the entire string to uppercase.
    Return the resulting string.
    """

Thought 1:
This is a string transformation task with a conditional branch:
- If digits exist → replace digits
- If no digits → convert entire string to uppercase
We must track whether any digit appears. I will first implement and then verify using tests.

Action 1: Test[
def process_string(t):
    res = []
    for ch in t:
        if ch.isdigit():
            res.append(str(9 - int(ch)))
        else:
            res.append(ch)
    return ''.join(res)

assert process_string("abc") == "ABC"
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
]

Observation 1:
Tests passing:
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"

Tests failing:
assert process_string("abc") == "ABC" # output: "abc"


Thought 2:
The failure shows that the "no digit → uppercase" branch is missing. I need to track digit existence and fix the logic.

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

assert process_string("abc") == "ABC"
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
assert process_string("") == ""
]

Observation 2:
Tests passing:
assert process_string("abc") == "ABC"
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
assert process_string("") == ""

Thought 3:
The implementation is correct.

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
    return result"""

# ========================
# 示例2：直接成功（SHA256）
# ========================
"""Question:
def string_to_sha256(content):
    \"\"\"Return sha256 hash of content, or None if empty\"\"\"

Thought 1:
This task requires hashing with a boundary condition (empty string). We must handle encoding and use hashlib.

Action 1: Plan[
1. If content is empty → return None
2. Encode content to utf-8
3. Compute sha256
4. Return hex string
]

Observation 1: Plan is clear.

Thought 2:
Implement the function.

Action 2: Code[
def string_to_sha256(content):
    import hashlib
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
]

Observation 2: Code defined.

Thought 3:
We should test:
1. Empty input
2. Known hash value

Action 3: Test[
assert string_to_sha256("") is None
assert string_to_sha256("Python") == "11a4a60b518bf24989d481468076e5d5982884626aed9faeb35b8576fcd223e1"
]

Observation 3: All tests passed.

Thought 4:
The implementation is correct.

Action 4: Finish[
def string_to_sha256(content):
    import hashlib
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
]
""",


# ========================
# 示例3：失败 → 修复（边界问题）
# ========================
"""Question:
def generate_odd_numbers(x, y):
    \"\"\"Return odd digits between x and y (1-9) in ascending order\"\"\"

Thought 1:
We need to normalize range and filter odd numbers within [1,9].

Action 1: Plan[
1. Determine lower and upper bounds
2. Iterate through range
3. Filter odd numbers
]

Observation 1: Plan is clear.

Thought 2:
Implement the function.

Action 2: Code[
def generate_odd_numbers(x, y):
    lower = min(x, y)
    upper = max(x, y)
    return [i for i in range(lower, upper+1) if i % 2 == 1]
]

Observation 2: Code defined.

Thought 3:
We should test:
1. Normal range
2. Reversed range
3. Out-of-bound cases (outside 1-9)

Action 3: Test[
assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
assert generate_odd_numbers(10, 18) == []
]

Observation 3:
AssertionError on (10,18)

Thought 4:
The issue is we did not restrict range to [1,9].

Action 4: Code[
def generate_odd_numbers(x, y):
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    if lower > upper:
        return []
    return [i for i in range(lower, upper+1) if i % 2 == 1]
]

Observation 4: Code updated.

Thought 5:
Re-run tests.

Action 5: Test[
assert generate_odd_numbers(1, 9) == [1,3,5,7,9]
assert generate_odd_numbers(9, 1) == [1,3,5,7,9]
assert generate_odd_numbers(10, 18) == []
]

Observation 5: All tests passed.

Thought 6:
The implementation is correct.

Action 6: Finish[
def generate_odd_numbers(x, y):
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    if lower > upper:
        return []
    return [i for i in range(lower, upper+1) if i % 2 == 1]
]
"""
]

FEWSHOTS = [
"""Question:
def process_string(t):
    \"\"\"You are given a string t.
    If t[i] is a digit, replace it with its complement to 9 (9 - digit).
    Otherwise keep it unchanged.
    If the string contains no digits, convert the entire string to uppercase.
    Return the resulting string.
    \"\"\"

Thought 1:
This is a string processing task with a conditional branch:
- If digits exist → replace digits
- If no digits → convert entire string to uppercase
We must track whether any digit appears during traversal.

Action 1: Plan[
1. Traverse string
2. Replace digits with (9 - digit)
3. Track digit existence
4. If no digit → uppercase
5. Else → return modified string
]

Observation 1: Plan is clear.

Thought 2:
Implement the function based on the plan.

Action 2: Code[
def process_string(t):
    res = []
    for ch in t:
        if ch.isdigit():
            res.append(str(9 - int(ch)))
        else:
            res.append(ch)
    result = ''.join(res)
    return result  # BUG: missing uppercase condition
]

Observation 2: Code defined.

Thought 3:
We should test:
1. No digit case (should uppercase)
2. All digits
3. Mixed characters
4. Edge case (empty string)

Action 3: Test[
assert process_string("abc") == "ABC"
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
]

Observation 3:
AssertionError on "abc" → expected "ABC", got "abc"

Thought 4:
The failure shows that the "no digit → uppercase" branch is missing.
We need to track digit existence and fix the return logic.

Action 4: Code[
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

Observation 4: Code updated.

Thought 5:
Re-run the same tests to verify correctness.

Action 5: Test[
assert process_string("abc") == "ABC"
assert process_string("123") == "876"
assert process_string("#8@9") == "#1@0"
assert process_string("") == ""
]

Observation 5: All tests passed.

Thought 6:
The implementation is now correct.

Action 6: Finish[
def process_string(t):
    \"\"\"You are given a string t.
    If t[i] is a digit, replace it with its complement to 9 (9 - digit).
    Otherwise keep it unchanged.
    If the string contains no digits, convert the entire string to uppercase.
    Return the resulting string.
    \"\"\"
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

Observation 6: Answer is CORRECT.
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

Thought 2: Define the function skeleton with range normalization logic (matching the problem's function definition style).
Action 2: Implement[
def generate_odd_numbers(x, y):
    \"\"\"Return odd digits between x and y (1-9) in ascending order.\"\"\"
    lower = max(1, min(x, y))
    upper = min(9, max(x, y))
    # Filter odd numbers here
]
Observation 2: OK.

Thought 3: Verify the range normalization and odd filter with test cases.
Action 3: Verify[
# Test range normalization (x > y)
lower = max(1, min(9,1))
upper = min(9, max(9,1))
assert lower == 1 and upper == 9  # Correct range
# Test odd filter
nums = [i for i in range(1,10) if i%2 ==1]
assert nums == [1,3,5,7,9]  # Matches example
# Test out-of-range case
lower = max(1, min(10,18))
upper = min(9, max(10,18))
assert lower > upper → return empty list
]
Observation 3: OK.

Thought 4: Complete the full function with all logic and docstring.
Action 4: Finish[
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
Observation 4: Answer is CORRECT
"""
]

REFLECTION_FEWSHOTS = [
"""
Previous Trial:
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

Reflection: I directly wrote the concise one-line solution but skipped breaking down the reasoning into reusable algorithmic steps. I should have first outlined the step-by-step logic (initialize flag, iterate through characters, update flag) that could be translated into a structured program, instead of jumping to the final code.
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
