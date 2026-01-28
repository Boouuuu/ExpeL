"""Math2Code 训练阶段：纯数学题解答。Thought / Reason / Calculate / Finish，无编程。"""
from typing import Tuple, Dict, Any, List
import re

FEWSHOTS = ["""Question: Solve for x: 2x + 5 = 15
Thought 1: I need to isolate x. First subtract 5 from both sides.
Action 1: Reason[Subtract 5 from both sides: 2x + 5 - 5 = 15 - 5, so 2x = 10]
Observation 1: OK.
Thought 2: Now divide both sides by 2 to get x.
Action 2: Calculate[10 / 2]
Observation 2: Result: 5
Thought 3: So x = 5.
Action 3: Finish[5]""",
"""Question: What is 5! (factorial of 5)?
Thought 1: 5! = 5 × 4 × 3 × 2 × 1. I can compute step by step.
Action 1: Calculate[5 * 4]
Observation 1: Result: 20
Thought 2: 20 × 3 = 60, then 60 × 2 = 120, then 120 × 1 = 120.
Action 2: Calculate[20 * 3]
Observation 2: Result: 60
Thought 3: 60 × 2 = 120, 120 × 1 = 120.
Action 3: Calculate[60 * 2]
Observation 3: Result: 120
Thought 4: So 5! = 120.
Action 4: Finish[120]""",
"""Question: Find gcd(48, 18) using the Euclidean algorithm.
Thought 1: gcd(48, 18). 48 = 18 × 2 + 12, so gcd(48, 18) = gcd(18, 12).
Action 1: Reason[48 mod 18 = 12, so gcd(48,18) = gcd(18,12)]
Observation 1: OK.
Thought 2: 18 = 12 × 1 + 6, so gcd(18, 12) = gcd(12, 6).
Action 2: Reason[18 mod 12 = 6, so gcd(18,12) = gcd(12,6)]
Observation 2: OK.
Thought 3: 12 = 6 × 2 + 0, so gcd(12, 6) = 6.
Action 3: Reason[12 mod 6 = 0, so gcd(12,6) = 6]
Observation 3: OK.
Thought 4: Therefore gcd(48, 18) = 6.
Action 4: Finish[6]""",
"""Question: Solve the quadratic equation x² - 5x + 6 = 0.
Thought 1: Use factoring. We need two numbers that multiply to 6 and add to -5: -2 and -3.
Action 1: Reason[Factor: (x-2)(x-3) = 0, so x = 2 or x = 3]
Observation 1: OK.
Thought 2: Solutions are x = 2 and x = 3. I'll give both.
Action 2: Finish[2, 3]""",
"""Question: What is the sum of the first 10 positive integers? 1 + 2 + ... + 10
Thought 1: Formula n(n+1)/2 for sum 1 to n. Here n = 10.
Action 1: Reason[Sum = 10 * 11 / 2 = 55]
Observation 1: OK.
Thought 2: 10 * 11 = 110, 110 / 2 = 55.
Action 2: Calculate[10 * 11 / 2]
Observation 2: Result: 55.0
Thought 3: So the sum is 55.
Action 3: Finish[55]""",
"""Question: Is 17 a prime number?
Thought 1: A prime has no divisors except 1 and itself. Check divisors from 2 to sqrt(17) ≈ 4.
Action 1: Reason[Check 2, 3, 4. 17 mod 2 = 1, 17 mod 3 = 2, 17 mod 4 = 1]
Observation 1: OK.
Thought 2: None divide 17, so 17 is prime.
Action 2: Finish[yes]"""]

REFLECTION_FEWSHOTS = [
"""
Previous Trial:
Question: Solve for x: 3x - 7 = 8
Thought 1: Add 7 to both sides.
Action 1: Finish[5]

Reflection: I jumped to the answer without showing steps. I should have used Reason to write 3x = 15, then Calculate or Reason to get x = 5, and only then Finish[5].
""",
"""
Previous Trial:
Question: What is 2^10?
Thought 1: 2^10 = 1024.
Action 1: Finish[1024]

Reflection: I gave the answer without intermediate reasoning. I should have broken it down, e.g. 2^5=32, 2^10=32*32=1024, using Calculate for verification.
"""]

SYSTEM_INSTRUCTION = """Solve a math problem with interleaving Thought, Action, Observation steps. Thought reasons about the problem; Action can be:
(1) Reason[step], which explains a logical or algebraic step (no computation).
(2) Calculate[expression], which evaluates a numeric expression (e.g. 2+3, 10/2) and returns the result.
(3) Finish[answer], which gives the final answer and ends the task.
"""

human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving math problems: one successful and one unsuccessful. You failed either by giving a wrong answer with Finish[<answer>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given successful math-solving task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a previous math-solving trial. You failed either by giving a wrong answer with Finish[<answer>] or by using up the steps. In a few sentences, diagnose why you failed and give a concise plan to avoid the same failure. Use complete sentences."""

def LLM_PARSER(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
    pattern = r'(?i)action\s*(?:\d+|)\s*(?::|)\s*'
    action_pattern = r'(?i)\w+\[[^\]]+(?:\]|)'

    match = re.match(pattern, llm_output)
    if match:
        action = llm_output[match.end():]
        content = f"Action {step}: {action}"
        if len(re.findall(action_pattern, action)) > 1:
            return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': ''}
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': action}

    actions = re.findall(action_pattern, llm_output)
    if len(actions) == 1:
        action = actions[0]
        if action[-1] != ']':
            action += ']'
        content = f"Action {step}: {action}"
        return {'role': 'ai' if ai_message else 'human', 'content': content}, 'action', {'action': action}
    if len(actions) > 1:
        content = re.sub(r"(?i)action\s*(?:\d*|)\s*(?::|)", "", llm_output)
        return {'role': 'ai', 'content': f"Action {step}: {content}"}, 'action', {'action': ''}

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
