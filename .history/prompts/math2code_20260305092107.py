"""Math2Code 训练阶段：纯数学题解答。Thought / Reason / Calculate / Finish，无编程。"""
from typing import Tuple, Dict, Any, List
import re
FEWSHOTS = [
"""Question: 
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
""",
"""Question: 
def string_to_md5(text):
    \"\"\"
    Given a string 'text', return its md5 hash equivalent string.
    If 'text' is an empty string, return None.

    >>> string_to_md5('Hello world') == '3e25960a79dbc69b674cd4ec67a72c62'
    \"\"\"

Thought 1: The problem requires MD5 hash computation with a boundary condition (empty string). I need to import the hashlib module, handle encoding, compute the hash, and add the empty string check.
Action 1: Reason[Step 1: Import hashlib for MD5 computation. Step 2: Check if input text is empty → return None. Step 3: Encode text to ASCII (required for hashlib). Step 4: Compute MD5 hash and convert to hexadecimal string. Step 5: Return the hex string.]
Observation 1: OK.

Thought 2: Define the function skeleton with core condition structure (matching the problem's function definition style).
Action 2: Implement[
def string_to_md5(text):
    \"\"\"Return MD5 hash string of text, or None if text is empty.\"\"\"
    import hashlib
    if not text:
        return None
    # Hash computation logic here
]
Observation 2: OK.

Thought 3: Verify the core hash logic and boundary condition with test cases.
Action 3: Verify[
# Test empty string condition
assert string_to_md5("") is None  # Correct boundary handling
# Test hash computation
import hashlib
test_hash = hashlib.md5('Hello world'.encode('ascii')).hexdigest()
assert test_hash == '3e25960a79dbc69b674cd4ec67a72c62'  # Matches example
]
Observation 3: OK.

Thought 4: Complete the full function with all logic and docstring.
Action 4: Finish[
def string_to_md5(text):
    \"\"\"
    Given a string 'text', return its md5 hash equivalent string.
    If 'text' is an empty string, return None.

    >>> string_to_md5('Hello world') == '3e25960a79dbc69b674cd4ec67a72c62'
    \"\"\"
    import hashlib
    return hashlib.md5(text.encode('ascii')).hexdigest() if text else None
]
""",
"""Question: 
def generate_integers(a, b):
    \"\"\"
    Given two positive integers a and b, return the even digits between a
    and b, in ascending order.

    For example:
    generate_integers(2, 8) => [2, 4, 6, 8]
    generate_integers(8, 2) => [2, 4, 6, 8]
    generate_integers(10, 14) => []
    \"\"\"

Thought 1: The problem needs to normalize the input range (min/max), filter even numbers within 2-8, and return sorted result. The key is to first fix the range boundary, then apply even filter.
Action 1: Reason[Step 1: Find lower bound (max of 2 and min(a,b)) and upper bound (min of 8 and max(a,b)). Step 2: Generate a list of numbers from lower to upper (inclusive). Step 3: Filter only even numbers from the list. Step 4: Return the filtered list (already ascending).]
Observation 1: OK.

Thought 2: Define the function skeleton with range normalization logic (matching the problem's function definition style).
Action 2: Implement[
def generate_integers(a, b):
    \"\"\"Return even digits between a and b (2-8) in ascending order.\"\"\"
    lower = max(2, min(a, b))
    upper = min(8, max(a, b))
    # Filter even numbers here
]
Observation 2: OK.

Thought 3: Verify the range normalization and even filter with test cases.
Action 3: Verify[
# Test range normalization (a > b)
lower = max(2, min(8,2))
upper = min(8, max(8,2))
assert lower == 2 and upper == 8  # Correct range
# Test even filter
nums = [i for i in range(2,9) if i%2 ==0]
assert nums == [2,4,6,8]  # Matches example
# Test out-of-range case
lower = max(2, min(10,14))
upper = min(8, max(10,14))
assert lower > upper → return empty list
]
Observation 3: OK.

Thought 4: Complete the full function with all logic and docstring.
Action 4: Finish[
def generate_integers(a, b):
    \"\"\"
    Given two positive integers a and b, return the even digits between a
    and b, in ascending order.

    For example:
    generate_integers(2, 8) => [2, 4, 6, 8]
    generate_integers(8, 2) => [2, 4, 6, 8]
    generate_integers(10, 14) => []
    \"\"\"
    lower = max(2, min(a, b))
    upper = min(8, max(a, b))
    return [i for i in range(lower, upper+1) if i % 2 == 0]
]
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

SYSTEM_INSTRUCTION = """Solve a code generation problem with interleaving Thought, Action, Observation steps.
Thought reasons about the problem at a high level. Before writing detailed code, identify the overall structure, strategy, or reusable pattern of the solution. Focus on reasoning patterns that could be reused across similar problems.
Action can be:
(1) Reason[step], which explains a logical, algorithmic, or structural step without writing full code. Reason steps should form a clear procedure that could be directly translated into a correct program.
(2) Implement[pattern], which defines a function skeleton, loop structure, condition, or basic code block following standard Python syntax and type hints.
(3) Verify[case], which checks the logic against one or more example inputs and outputs to confirm correctness.
(4) Finish[code], which requires to complete the following Python code (including function definition with type hints, docstring, and complete implementation logic) and ends the task."""

human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving code generation problems: one successful and one unsuccessful. You failed either by giving a wrong answer with Finish[<code>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given successful code generation task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a previous code generation trial. You failed either by giving a wrong answer with Finish[<code>] or by using up the steps. In a few sentences, diagnose why you failed and give a concise plan to avoid the same failure. Focus on whether your reasoning was sufficiently structured, explicit, and reusable, rather than jumping directly to the answer. Use complete sentences."""

def LLM_PARSER(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
    print(f"LLM Output: {llm_output}")  # Debug print to see the raw output
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
