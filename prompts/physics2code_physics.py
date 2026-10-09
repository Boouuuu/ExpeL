"""Physics2Code 训练阶段：纯物理题解答。Thought / Search / Finish，无编程。"""
from typing import Tuple, Dict, Any, List
import re
# 5个fewshots
FEWSHOTS = ["""Question: A block of mass m = 2 kg slides without friction from rest down an incline of height h = 5 m. Take g = 10 m/s^2. What is the speed of the block at the bottom?
Thought 1: This is an energy-conservation problem: on a frictionless incline, the lost gravitational potential energy becomes kinetic energy, so mgh = (1/2)mv^2 and v = sqrt(2gh). Let me confirm the conservation relation.
Plan:
- Search for the conservation-of-energy relation for a frictionless slide
- Solve for v and substitute the numbers
Action 1: Search[conservation of energy frictionless incline v = sqrt(2gh)]
Observation 1: For a body sliding without friction from rest through a vertical drop h, mgh = (1/2)mv^2, hence v = sqrt(2gh), independent of mass.
Thought 2: Substitute g = 10, h = 5: v = sqrt(2 * 10 * 5) = sqrt(100) = 10 m/s.
Action 2: Finish[10]
Observation 2: Answer is correct.""",

# """Question: A simple pendulum of length L = 1 m oscillates with small amplitude near Earth's surface (g = 9.8 m/s^2). What is its period? Take pi = 3.14.
# Thought 1: This is a small-amplitude pendulum problem. The period depends on length and gravity through a known formula, so I should retrieve it rather than guess.
# Plan:
# - Retrieve the small-angle pendulum period formula
# - Substitute L and g and simplify
# Action 1: Search[period of simple pendulum small angle formula]
# Observation 1: For small oscillations the period is T = 2*pi*sqrt(L/g), independent of the bob mass.
# Thought 2: Substitute L = 1, g = 9.8: sqrt(1/9.8) = sqrt(0.102) ≈ 0.32, so T = 2 * 3.14 * 0.32 ≈ 2.0 s.
# Action 2: Finish[2.0]""",

# """Question: Two point charges q1 = +3 microC and q2 = -2 microC are placed 0.3 m apart in vacuum. Given k = 9e9 N m^2/C^2, what is the magnitude of the electrostatic force between them?
# Thought 1: First identify the governing law. Two stationary point charges interact via Coulomb's force, whose magnitude is F = k|q1 q2| / r^2.
# Key conditions:
# - Charges given in microCoulombs, must convert to Coulombs (1 microC = 1e-6 C)
# - Only the magnitude is asked, so the sign of q2 does not affect the result
# Plan:
# 1. Retrieve/confirm Coulomb's law expression
# 2. Convert units to SI
# 3. Substitute and compute the power-of-ten factors carefully
# Action 1: Search[Coulomb's law magnitude force between two point charges]
# Observation 1: F = k |q1 q2| / r^2, with k = 8.99e9 N m^2/C^2 in vacuum; force acts along the line joining the charges.
# Thought 2: Convert charges: q1 = 3e-6 C, q2 = 2e-6 C, so |q1 q2| = 6e-12 C^2. With r = 0.3 m, r^2 = 0.09 m^2. Then F = 9e9 * 6e-12 / 0.09 = (9 * 6 / 0.09) * 1e-3 = 600 * 1e-3... checking: 9e9 * 6e-12 = 54e-3 = 0.054; 0.054 / 0.09 = 0.6. So the magnitude is 0.6 N.
# Action 2: Finish[0.6]"""
]

REFLECTION_FEWSHOTS = [
"""
Previous Trial:
Question: A car accelerates uniformly from rest to 20 m/s in 5 s. What is its acceleration?
Thought 1: The acceleration formula is a = v * t. Plug in v=20, t=5, so a = 100 m/s².
Action 1: Finish[100]
Observation 1: Answer is incorrect.

Reflection: I incorrectly remembered the kinematic formula for uniform acceleration. Acceleration is the change in velocity divided by time, not multiplied. The correct formula should be $a=(v-u)/t$. Since starting from rest, initial velocity $u=0$. Substitute values: $a=(20-0)/5=4\ \text{m/s}^2$. Next time I need to double-check the definition of acceleration before calculation and avoid mixing up multiplication and division in kinematic equations."""


# """Previous Trial:
# Question: A 5 kg object is pushed by a constant net force of 20 N across a frictionless surface. What is its acceleration?
# Thought 1: Force causes acceleration. I recall Newton's second law involves force and mass, so the acceleration is probably $F + m = 20 + 5 = 25$, let me just answer that.
# Action 1: Finish[25]

# Reflection: My failure came from applying an unverified and dimensionally wrong relation (adding force and mass). For Newton's-second-law problems I should use the Search action to confirm the exact formula $a = F/m$ and check units before computing. I should have searched for "Newton's second law acceleration a = F/m" and verified that dividing force by mass gives $20/5 = 4\\,\\mathrm{m/s^2}$, rather than guessing an operation.""",
]

SYSTEM_INSTRUCTION = """Solve a physics problem with interleaving Thought, Action, Observation steps.\nThought should reason about the current task state before each Action. It may involve problem understanding, planning, algorithm selection, local derivation, implementation reasoning, error diagnosis, hypothesis revision, or other reasoning relevant to solving the task. Keep the reasoning flexible and adapt it to the current situation.\nAction represents interaction with the execution environment and has two types:\n
(1) Search[query], which looks up physical knowledge such as formulas, principles, theorems and laws in a knowledge base.
(2) Finish[answer], which returns the answer and finishes the task.

You should first generate a Thought, then choose an Action. After each Action, STOP generate and wait for the system to return Observation. Do NOT generate Observation by yourself."""


human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving physics problems: one successful and one failed. You failed either by giving a wrong answer with Finish[<answer>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given two successful physics-solving task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a Physics problem solving trial. You failed either by giving a wrong answer with Finish[<answer>] or by using up the steps. Your task is to analyze the reasons for your failure and put forward concise plans or solutions to prevent repeating the same mistakes in few sentences."""

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
