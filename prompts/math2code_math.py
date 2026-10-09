"""Math2Code 训练阶段：纯数学题解答。Thought / Search / Finish，无编程。"""
from typing import Tuple, Dict, Any, List
import re
# 5个fewshots
FEWSHOTS = ["""Question: What is the sum of the first 10 positive integers?
Thought 1: This is a structured summation problem: 1 + 2 + ... + n. Instead of computing iteratively, I check if a closed-form formula exists.
Plan:
- Search for a known formula for arithmetic series
- Substitute n = 10 and compute directly
Action 1: Search[formula for sum of first n positive integers]
Observation 1: 1 + 2 + ... + n = n(n + 1) / 2
Thought 2: Substitute n = 10: 10 × 11 / 2 = 55, which is the final answer.
Action 2: Finish[55]""",

"""Question: Evaluate C(10, 3).
Thought 1: This is a combinatorics problem involving combinations. I recognize the structure "n choose k".
Plan:
- Retrieve the formula for combinations
- Substitute values and simplify carefully
Action 1: Search[combination formula n choose k]
Observation 1: C(n, k) = n! / (k!(n-k)!)
Thought 2: Substitute n = 10, k = 3. Simplify by canceling factorial terms: 10! / 7! = 10 × 9 × 8, and 3! = 6. So the value becomes (10 × 9 × 8) / 6 = 120.
Action 2: Finish[120]""",

"""Question: Joel selected an acute angle x and wrote sin x, cos x, tan x on three cards. Only Malvina could uniquely identify her function. Find the sum of all possible values on her card.
Thought 1: First formalize the setting. There are three values: sin x, cos x, tan x, all shared among students.
Key condition:
- Only Malvina can uniquely determine her function
- The other two cannot
This is a distinguishability problem: whether a value uniquely identifies its generating function.
Plan:
1. Analyze properties of sin x, cos x, tan x on (0°, 90°)
2. Determine when values may coincide (causing ambiguity)
3. Enumerate all equality cases
4. Check which cases satisfy “exactly one identifiable student”
Action 1: Search[properties of sin x cos x tan x on (0, 90 degrees)]
Observation 1:
- sin x, cos x, tan x are all strictly monotonic → each is one-to-one 
- sin x ∈ (0,1), cos x ∈ (0,1), tan x ∈ (0, +∞) 
- sin x = cos x at x = 45° - tan x = sin x / cos x
Thought 2: Case 1: sin x = cos x ⇒ x = 45°. Then values are {√2/2, √2/2, 1}. The value 1 can only be tan x, so that student can identify uniquely, while the two √2/2 values cannot distinguish between sin and cos. This satisfies the condition, so Malvina’s value could be 1.
Case 2: sin x = tan x has no valid solution in (0°, 90°), so discard.
Case 3: cos x = tan x ⇒ cos^2 x = sin x. Using cos^2 x = 1 - sin^2 x gives 1 - sin^2 x = sin x ⇒ sin^2 x + sin x - 1 = 0. Solving gives sin x = (-1 + √5)/2 (valid in (0,1)). Then cos x = tan x, so two values are equal and one is distinct. The distinct value is sin x, so that student can uniquely identify, while the other two cannot. This also satisfies the condition, so Malvina’s value could be (-1 + √5)/2.
Thus the possible values are 1 and (-1 + √5)/2, and their sum is (1 + √5)/2.
Action 2: Finish[(1 + sqrt(5)) / 2]"""
]

REFLECTION_FEWSHOTS = [
"""
Previous Trial:
Question: What is the sum of the first 20 positive integers?
Thought 1: This is a simple summation. The answer is 210.
Action 1: Finish[210]

Reflection: I jumped directly to the answer without outlining a clear plan or step-by-step reasoning. I should first identify the problem as an arithmetic series, explicitly state the formula n(n+1)/2, and then substitute the value. Including a structured plan and intermediate steps would make the reasoning more reliable and reusable.""",

"""Previous Trial:
Question: A torus is formed by rotating a circle of radius $r=3$ centered at $(7, 0)$ around the $y$-axis. Calculate the volume of this torus.
Thought 1: The volume of a torus can be found using integration or a specific geometric theorem. I remember it involves the area of the circle and the distance the centroid travels. I'll guess it's $2\pi^2 r^2 R = 2 \times \pi^2 \times 3^2 \times 7 = 126\pi^2 \approx 1243.6$.
Action 1: Finish[126\pi^2]

Reflection: My failure stemmed from relying on an unverified memory of a specialized geometric formula. For high-level problems involving the Theorem of Pappus, I should use the Search action to confirm the exact parameters (distance of centroid vs. radius) and the formula structure ($V = 2\pi R \cdot A$). I should have first searched for "Pappus's Second Theorem for volume" to ensure the relationship between the generating shape's area and its centroid's path was correctly applied.""",

# """Previous Trial:
# Question: Find the area of a triangle with vertices at coordinates $(2, 3)$, $(-1, 5)$, and $(4, -2)$.
# Thought 1: To find the area of a triangle given coordinates, I should use the Shoelace Formula. I will first search for the exact formula to avoid signs errors.
# Action 1: Search[Shoelace Formula for triangle area]
# Observation 1: The Shoelace Formula for a triangle with vertices $(x_1, y_1), (x_2, y_2), (x_3, y_3)$ is: Area = $\frac{1}{2} |x_1(y_2 - y_3) + x_2(y_3 - y_1) + x_3(y_1 - y_2)|$.
# Thought 2: Now I substitute the coordinates: $(2, 3)$, $(-1, 5)$, $(4, -2)$.
# $x_1=2, y_1=3$
# $x_2=-1, y_2=5$
# $x_3=4, y_3=-2$
# Calculation:
# $2(5 - (-2)) = 2(7) = 14$
# $-1((-2) - 3) = -1(-5) = 5$
# $4(3 - 5) = 4(-2) = -8$
# Sum: $14 + 5 - 8 = 11$.
# Final Area: $11 / 2 = 5.5$.
# Action 2: Finish[5.5]
# Observation 2: Answer is INCORRECT.

# Reflection: I made a silent arithmetic error during the summation or substitution phase. My plan was flawed because it did not include a "verification" or "cross-check" step (such as calculating the area using a different method like the determinant form or double-checking the subtraction of negative numbers). In future trials, I must explicitly add a "Verify Calculation" step to my plan to catch manual processing errors before submitting the final answer."""
]

SYSTEM_INSTRUCTION = """Solve a math problem with interleaving Thought, Action, Observation steps.
Thought can reason about the current situation, and Action can be two types:
(1) Search[query], which looks up mathematical knowledge such as formulas, principles, theorems and laws in a knowledge base.
(2) Finish[answer], which returns the answer and finishes the task.
"""


human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving math problems: one successful and one failed. You failed either by giving a wrong answer with Finish[<answer>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given two successful math-solving task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a Mathematical problem solving trial. You failed either by giving a wrong answer with Finish[<answer>] or by using up the steps. Your task is to analyze the reasons for your failure and put forward concise plans or solutions to prevent repeating the same mistakes in few sentences."""

def _strip_leaked_observation_suffix(s: str) -> str:
    """stop=Observation 时可能残留 Observation / Observ 片段，从 Action 尾部去掉。"""
    if not s:
        return s
    parts = re.split(r'(?i)\bobserv', s, maxsplit=1)
    return parts[0].rstrip()

def LLM_PARSER(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
    # Check if the output contains both Thought and Action
    # 步骤标记必须形如 "Thought N:" / "Action N:"（数字+冒号必选），
    # 否则会把 "reaction"/"interaction" 等单词内嵌的 "action" 误判为步骤起点，
    # 导致 Thought 被从中间截断（尤其在 LLM 输出换行被删除、文本粘连时）。
    thought_pattern = r'(?i)thought\s*\d+\s*:'
    action_pattern = r'(?i)action\s*\d+\s*:'
    
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

def LLM_PARSER2(llm_output, step: int, ai_message: bool) -> Tuple[dict, str, Dict[str, Any]]:
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
    if reflections == []:
        return ''
    if include_prefix:
        memory_prefix = "You have attempted to solve the task before but failed. The following reflection(s) give a plan to avoid failing the task in the same way you did previously. Use them to improve your strategy of solving the task successfully."
    else:
        memory_prefix = ''
    memory_prefix += '\nReflections:'
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
