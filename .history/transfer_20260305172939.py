import json
prompt_template = """You are a teacher agent that passes on experience to student agents. You came up with the following rules to help you achieve the task of {Source Task} effectively. The number at the end are the importance you gave to each of the rules.
RULES:
{Extracted_insights}
Now a student agent is trying to solve a similar {Target_Task}.

Some examples of this new task are:
{Fixed_fewshot_examples_of_Target_Task}

Give a concise and easy to follow instructional paragraph based on the RULES for the student agent to solve {Target Task}. Do not state where each sentence is using whichever rule, and make sure the paragraph is VERY CONCISE and EASY TO FOLLOW!


Knowledge transfer
Fewshot Evaluation

The following paragraph is insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the {Target_Task} tasks efficiently:

{Finetuned_insights}

{Target_Task_description}{fewshot}

{Target_Task}
"""
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
Extracted_insights = """"""
Target_Task_File = r"C:\Users\HUAWEI\Desktop\ExpeL\data\math2code\code_tasks.jsonl"
# 遍历Target_Task_File
with open(Target_Task_File, 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line.strip())
        Target_Task = item.get('prompt', '').strip()
        prompt= prompt_template.format(
            Source_Task = "math problem-solving",
            Extracted_insights = Extracted_insights,
            Target_Task = Target_Task,
            Fixed_fewshot_examples_of_Target_Task = "",
            Finetuned_insights = "",
            Target_Task_description = "",
            fewshot = ""
        )
        print("prompt:", prompt)
    