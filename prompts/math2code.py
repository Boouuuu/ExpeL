from typing import Tuple, Dict, Any, List
import pickle
import re

from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.schema import (
    AIMessage,
    HumanMessage,
    ChatMessage,
)

FEWSHOTS = ["""Question: How to implement a function that calculates the factorial of a number using recursion, similar to the mathematical definition n! = n × (n-1)!?
Thought 1: I need to understand the mathematical concept of factorial and translate it into code. The factorial function is defined recursively: n! = n × (n-1)! with base case 0! = 1.
Action 1: Analyze[factorial recursion]
Observation 1: Factorial recursion has two key components: (1) Base case: factorial(0) = 1 and factorial(1) = 1, (2) Recursive case: factorial(n) = n × factorial(n-1) for n > 1.
Thought 2: Now I need to translate this mathematical definition into code. The recursive structure maps directly to a recursive function.
Action 2: Translate[recursive function pattern]
Observation 2: A recursive function pattern includes: (1) Base case check at the beginning, (2) Return statement for base case, (3) Recursive call with modified parameters, (4) Combine current value with recursive result.
Thought 3: I can now write the code. The base case is when n <= 1, return 1. Otherwise, return n * factorial(n-1).
Action 3: Finish[def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)]""",
"""Question: How to implement matrix multiplication following the mathematical formula C[i][j] = Σ(A[i][k] * B[k][j])?
Thought 1: I need to understand matrix multiplication mathematically and translate it to code. The formula involves nested loops: outer loops for result matrix dimensions, inner loop for summation.
Action 1: Analyze[matrix multiplication]
Observation 1: Matrix multiplication requires: (1) Result matrix C has dimensions [rows_A × cols_B], (2) For each position C[i][j], sum products A[i][k] * B[k][j] for all k, (3) Requires three nested loops: i, j, k.
Thought 2: I need to translate the summation formula Σ into a loop that accumulates the sum.
Action 2: Translate[summation loop pattern]
Observation 2: Summation pattern: initialize sum variable, loop through indices, accumulate products, assign final sum to result position.
Thought 3: Now I can write the code with three nested loops: outer for i, middle for j, inner for k to compute the sum.
Action 3: Finish[def matrix_multiply(A, B):\n    rows_A, cols_A = len(A), len(A[0])\n    rows_B, cols_B = len(B), len(B[0])\n    C = [[0] * cols_B for _ in range(rows_A)]\n    for i in range(rows_A):\n        for j in range(cols_B):\n            for k in range(cols_A):\n                C[i][j] += A[i][k] * B[k][j]\n    return C]""",
"""Question: How to implement binary search algorithm based on the mathematical concept of divide and conquer?
Thought 1: Binary search uses divide and conquer: split search space in half, compare with target, recurse on appropriate half. The mathematical property is that each step reduces search space by half.
Action 1: Analyze[divide and conquer]
Observation 1: Divide and conquer pattern: (1) Divide problem into smaller subproblems, (2) Conquer by solving subproblems recursively, (3) Combine results. For binary search: divide array in half, compare middle element, recurse on left or right half.
Thought 2: I need to translate the recursive divide-and-conquer approach into code, handling base cases and recursive cases.
Action 2: Translate[divide and conquer recursion]
Observation 2: Divide and conquer code pattern: (1) Base case: check if subproblem is trivial, (2) Divide: split into smaller parts, (3) Conquer: recursively solve subproblems, (4) Combine: merge results (not needed for binary search).
Thought 3: For binary search, base case is when left > right (not found) or middle == target (found). Otherwise, recurse on left or right half based on comparison.
Action 3: Finish[def binary_search(arr, target, left=0, right=None):\n    if right is None:\n        right = len(arr) - 1\n    if left > right:\n        return -1\n    mid = (left + right) // 2\n    if arr[mid] == target:\n        return mid\n    elif arr[mid] > target:\n        return binary_search(arr, target, left, mid - 1)\n    else:\n        return binary_search(arr, target, mid + 1, right)]""",
"""Question: How to implement the Euclidean algorithm for finding GCD based on the mathematical property gcd(a, b) = gcd(b, a mod b)?
Thought 1: The Euclidean algorithm uses the mathematical property that gcd(a, b) = gcd(b, a mod b) until b becomes 0, then gcd is a. This is a recursive mathematical definition.
Action 1: Analyze[Euclidean algorithm]
Observation 1: Euclidean algorithm: (1) If b == 0, gcd is a, (2) Otherwise, gcd(a, b) = gcd(b, a mod b). The modulo operation reduces the problem size each iteration.
Thought 2: This maps directly to a recursive function with a base case and recursive case.
Action 2: Translate[recursive algorithm]
Observation 2: Recursive algorithm pattern: base case handles termination condition, recursive case applies the mathematical property with modified parameters.
Thought 3: Base case: if b == 0, return a. Recursive case: return gcd(b, a % b).
Action 3: Finish[def gcd(a, b):\n    if b == 0:\n        return a\n    return gcd(b, a % b)]""",
"""Question: How to implement a function that calculates the Fibonacci sequence using dynamic programming, based on the recurrence relation F(n) = F(n-1) + F(n-2)?
Thought 1: Fibonacci has recurrence relation F(n) = F(n-1) + F(n-2) with base cases F(0) = 0, F(1) = 1. Dynamic programming stores previously computed values to avoid redundant calculations.
Action 1: Analyze[dynamic programming]
Observation 1: Dynamic programming pattern: (1) Identify overlapping subproblems, (2) Store solutions to subproblems in a table, (3) Build solution bottom-up or top-down with memoization, (4) Fibonacci has overlapping subproblems (computing F(3) requires F(2) and F(1), computing F(4) also requires F(2)).
Thought 2: I can use bottom-up DP: start with base cases, iteratively build up to n.
Action 2: Translate[bottom-up dynamic programming]
Observation 2: Bottom-up DP pattern: (1) Initialize array/table with base cases, (2) Loop from base cases to target, (3) Fill each position using recurrence relation and previous values.
Thought 3: Initialize dp[0] = 0, dp[1] = 1, then for i from 2 to n, dp[i] = dp[i-1] + dp[i-2].
Action 3: Finish[def fibonacci(n):\n    if n <= 1:\n        return n\n    dp = [0] * (n + 1)\n    dp[0], dp[1] = 0, 1\n    for i in range(2, n + 1):\n        dp[i] = dp[i-1] + dp[i-2]\n    return dp[n]]""",
"""Question: How to implement a function that checks if a number is prime using the mathematical property that a number n is prime if it has no divisors between 2 and √n?
Thought 1: Prime number property: n is prime if it's only divisible by 1 and itself. We only need to check divisors up to √n because if n has a divisor > √n, it must have a corresponding divisor < √n.
Action 1: Analyze[prime number property]
Observation 1: Prime checking: (1) Numbers <= 1 are not prime, (2) Check if n is divisible by any integer from 2 to √n, (3) If no divisors found, n is prime.
Thought 2: I need to translate the mathematical property into a loop that checks divisors.
Action 2: Translate[divisor checking loop]
Observation 2: Divisor checking pattern: loop through potential divisors, if any divides n evenly, return False. If loop completes without finding divisors, return True.
Thought 3: Check edge cases first (n <= 1), then loop from 2 to int(√n) + 1, check if n % i == 0.
Action 3: Finish[import math\ndef is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(math.sqrt(n)) + 1):\n        if n % i == 0:\n            return False\n    return True]"""]

REFLECTION_FEWSHOTS = [
"""
Previous Trial:
Question: How to implement quicksort algorithm based on the divide and conquer principle?
Thought 1: Quicksort uses divide and conquer: pick pivot, partition array, recursively sort subarrays.
Action 1: Analyze[quicksort divide and conquer]
Observation 1: Quicksort divides array around pivot, then recursively sorts left and right partitions.
Thought 2: I'll implement quicksort with a simple pivot selection.
Action 2: Finish[def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[0]\n    left = [x for x in arr[1:] if x < pivot]\n    right = [x for x in arr[1:] if x >= pivot]\n    return quicksort(left) + [pivot] + quicksort(right)]

Reflection: I implemented quicksort but didn't properly analyze the partition step. The mathematical concept requires partitioning in-place or understanding the partition algorithm. I should have analyzed the partition operation separately before implementing the full algorithm.
""",
"""
Previous Trial:
Question: How to implement matrix transpose based on the mathematical definition where A^T[i][j] = A[j][i]?
Thought 1: Matrix transpose swaps rows and columns. I'll create a new matrix.
Action 1: Finish[def transpose(matrix):\n    return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]]

Reflection: I jumped to implementation without analyzing the mathematical definition first. The transpose operation A^T[i][j] = A[j][i] means element at position (i,j) in result comes from position (j,i) in original. I should have analyzed this mapping more carefully to ensure correct implementation.
"""]

SYSTEM_INSTRUCTION = """Solve a code generation task by translating mathematical concepts into code with interleaving Thought, Action, Observation steps. Thought can reason about the mathematical concept and how to translate it, and Action can be three types:
(1) Analyze[mathematical_concept], which analyzes the mathematical concept, its properties, and how it can be represented computationally.
(2) Translate[code_pattern], which identifies the code pattern or structure that corresponds to the mathematical concept.
(3) Verify[code_snippet], which verifies if a code snippet correctly implements the mathematical concept (optional, for complex cases).
(4) Finish[code], which provides the final code implementation and finishes the task.
"""

human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {
    "role": "human",
    "content": human_instruction_template,
}

human_instruction_reflection_template = """Here are some examples:"""

HUMAN_REFLECTION_INSTRUCTION = {
    "role": "human",
    "content": human_instruction_reflection_template,
}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials in which you were given a mathematical concept to translate into code: one successful and one unsuccessful trial. You failed the trial either because you provided incorrect code with Finish[<code>], or you used up your set number of reasoning steps."""

SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given successful task trials in which you were given a mathematical concept to translate into code."""

SYSTEM_REFLECTION_INSTRUCTION = """You will be given a previous reasoning trial in which you were given a mathematical concept to translate into code. You were unsuccessful in providing correct code either because you provided incorrect code with Finish[<code>], or you used up your set number of reasoning steps. In a few sentences, Diagnose a possible reason for failure and devise a new, concise, high level plan that aims to mitigate the same failure. Use complete sentences."""

def LLM_PARSER(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
    pattern = r'(?i)action\s*(?:\d+|)\s*(?::|)\s*'
    action_pattern = r'(?i)\w+\[[^\]]+(?:\]|)'

    match = re.match(pattern, llm_output)
    if match:
        action = llm_output[match.end():]
        content = f"Action {step}: {action}"

        if len(re.findall(action_pattern, action)) > 1:
            return (
                {'role': 'ai' if ai_message else 'human', 'content': content},
                'action',
                {'action': ''} # triggers invalid action
            )

        return (
            {'role': 'ai' if ai_message else 'human', 'content': content},
            'action',
            {'action': action}
        )

    actions = re.findall(action_pattern, llm_output)
    if len(actions) == 1:
        action = actions[0]
        if action[-1] != ']':
            action += ']'
        content = f"Action {step}: {action}"
        return (
            {'role': 'ai' if ai_message else 'human', 'content': content},
            'action',
            {'action': action}
        )
    
    if len(actions) > 1:
        content = re.sub(r"(?i)action\s*(?:\d*|)\s*(?::|)", "", llm_output)
        return (
            {'role': 'ai', 'content': f"Action {step}: {content}"},
            'action',
            {'action': ''} # triggers invalid action
        )

    # everthing else will be assumed to be a inner thought
    thought_pattern = r'(?i)thought\s*(?:\d+|)\s*(?::|)\s*(.*)'
    match = re.match(thought_pattern, llm_output)
    if match:
        # Extract the thought word and content
        thought_word = match.group(1)
        content = f"Thought {step}: {thought_word.rstrip(':')}"
    else:
        content = f"Thought {step}: {llm_output.rstrip(':')}"
    return (
        {'role': 'ai' if ai_message else 'human', 'content': content},
        'thought',
        {}
    )

def OBSERVATION_FORMATTER(observation: str, step: int, *args, **kwargs) -> Tuple[dict, str]:
    return {'role': 'human', 'content': f"Observation {step}: " + observation.rstrip(':')}, 'append'

def STEP_IDENTIFIER(line: str) -> str:
    line = line.strip()
    pattern = re.compile(r'^(?i)action(?:\s+(\d+))?:')
    match = pattern.match(line)
    if match:
        return 'action'
    pattern = re.compile(r'^(?i)observation(?:\s+(\d+))?:')
    match = pattern.match(line)
    if match:
        return 'observation'
    return 'thought'

def CYCLER(lines: str) -> List[str]:
    new_lines = []
    scratch_pad = ''
    for line in lines.split('\n'):

        # line is action
        pattern = re.compile(r'^(?i)action(?:\s+(\d+))?:')
        match = pattern.match(line)
        if match:
            if scratch_pad != '':
                new_lines.append(scratch_pad.strip())
                scratch_pad = ''
            new_lines.append(line)
            continue

        # line is thought
        pattern = re.compile(r'^(?i)thought(?:\s+(\d+))?:')
        match = pattern.match(line)
        if match:
            if scratch_pad != '':
                new_lines.append(scratch_pad.strip())
                scratch_pad = ''
            new_lines.append(line)
            continue

        # step is observation
        scratch_pad += line + '\n'

    # the rest of the scratch pad
    if scratch_pad != '':
        new_lines.append(scratch_pad.strip())
    return new_lines

REFLECTION_PREFIX = '\nReflection:'

def PREVIOUS_TRIALS_FORMATTER(reflections: List[str], include_prefix: bool = True) -> str:
    if reflections == []:
        return ''
    if include_prefix:
        memory_prefix = "You have attempted to solve the task before but failed. The following reflection(s) give a plan to avoid failing the task in the same way you did previously. Use them to improve your strategy of solving the task successfully."
    else:
        memory_prefix = ''
    memory_prefix += '\nReflections:'
    for reflection in reflections:
        memory_prefix += f"\n- {reflection.strip()}"
    return memory_prefix

def STEP_STRIPPER(step: str, step_type: str):
    if step_type == 'observation':
        return re.sub(r'^(?i)observation(?:\s+(\d+))?:', 'Observation:', step)
    if step_type == 'action':
        return re.sub(r'^(?i)action(?:\s+(\d+))?:', 'Action:', step)
    if step_type == 'thought':
        return re.sub(r'^(?i)thought(?:\s+(\d+))?:', 'Thought:', step)
    return step
