"""Chemistry2Code 训练阶段：纯化学题解答。Thought / Search / Finish，无编程。"""
from typing import Tuple, Dict, Any, List
import re
# 5个fewshots
FEWSHOTS = ["""Question: What is the molarity of a solution prepared by dissolving 5.85 g of NaCl (molar mass = 58.5 g/mol) in enough water to make 500 mL of solution?
Thought 1: This is a solution-concentration problem: molarity equals moles of solute divided by liters of solution, so I need to convert the mass of NaCl to moles first. Let me confirm the definition.
Plan:
- Search for the molarity definition formula
- Convert mass to moles, then divide by the solution volume in liters
Action 1: Search[molarity definition formula moles solute per liter solution]
Observation 1: Molarity M = n / V, where n is the number of moles of solute and V is the volume of the solution in liters; n = mass / molar mass.
Thought 2: n(NaCl) = 5.85 / 58.5 = 0.1 mol, V = 500 mL = 0.5 L, so M = 0.1 / 0.5 = 0.2 mol/L.
Action 2: Finish[0.2]
Observation 2: Answer is correct.""",

# """Question: What is the density of CO2 gas (molar mass = 44 g/mol) at STP (0 C, 1 atm), given that the molar volume of an ideal gas at STP is 22.4 L/mol?
# Thought 1: For a gas at known temperature and pressure, density follows from the molar mass divided by the molar volume. Let me verify this relation.
# Plan:
# - Search for gas density from molar mass and molar volume at STP
# - Substitute the numbers and compute
# Action 1: Search[density of ideal gas at STP molar mass divided by molar volume 22.4 L]
# Observation 1: At STP, the density of an ideal gas is rho = M / Vm = molar mass / 22.4 L/mol.
# Thought 2: Substitute: rho = 44 / 22.4 ≈ 1.96 g/L.
# Action 2: Finish[1.96]
# Observation 2: Answer is correct.""",
]

REFLECTION_FEWSHOTS = [
"""
Previous Trial:
Question: What is the pH of a 0.01 mol/L HCl solution at 25 C?
Thought 1: HCl is a strong acid, so the pH equals the concentration value directly, pH = 0.01.
Action 1: Finish[0.01]
Observation 1: Answer is incorrect.

Reflection: I confused the hydrogen ion concentration with the pH value. pH is defined as $\\text{pH}=-\\log_{10}[\\text{H}^+]$, not $[\\text{H}^+]$ itself. For 0.01 mol/L HCl, $[\\text{H}^+]=10^{-2}$ mol/L, so $\\text{pH}=-\\log_{10}(10^{-2})=2$. Next time I must write down the definition formula before computing and double-check whether the question asks for the concentration or its logarithm."""


# """Previous Trial:
# Question: Which element has a larger first ionization energy, Na or Mg?
# Thought 1: Ionization energy has something to do with atomic size, so I think the answer is probably Na because sodium is more reactive.
# Action 1: Finish[Na]
# Observation 1: Answer is incorrect.

# Reflection: My failure came from mixing up chemical reactivity with first ionization energy and applying an unverified trend. For periodic-trend comparison problems I should use the Search action to confirm that first ionization energy generally increases across a period, verify the electron configurations ($[\\text{Ne}]3s^1$ for Na vs $[\\text{Ne}]3s^2$ for Mg), and then conclude Mg > Na rather than guessing from memory.""",
]

SYSTEM_INSTRUCTION = """Solve a chemistry problem with interleaving Thought, Action, Observation steps.\nThought should reason about the current task state before each Action. It may involve problem understanding, planning, methods selection, local derivation, implementation reasoning, error diagnosis, hypothesis revision, or other reasoning relevant to solving the task. Keep the reasoning flexible and adapt it to the current situation.\nAction represents interaction with the execution environment and has two types:\n
(1) Search[query], which looks up chemical knowledge such as formulas, principles, theorems and laws in a knowledge base.
(2) Finish[answer], which returns the answer and finishes the task.

You should first generate a Thought, then choose an Action. After each Action, STOP generate and wait for the system to return Observation. Do NOT generate Observation by yourself."""


human_instruction_template = """{instruction}You may take maximum of {max_steps} steps.
Here are some examples:"""

HUMAN_INSTRUCTION = {"role": "human", "content": human_instruction_template}
human_instruction_reflection_template = """Here are some examples:"""
HUMAN_REFLECTION_INSTRUCTION = {"role": "human", "content": human_instruction_reflection_template}

SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION = """You will be given two previous task trials of solving chemistry problems: one successful and one failed. You failed either by giving a wrong answer with Finish[<answer>] or by using up the allowed steps."""
SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION = """You will be given two successful chemistry-solving task trials."""
SYSTEM_REFLECTION_INSTRUCTION = """You will be given a Chemistry problem solving trial. You failed either by giving a wrong answer with Finish[<answer>] or by using up the steps. Your task is to analyze the reasons for your failure and put forward concise plans or solutions to prevent repeating the same mistakes in few sentences."""

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
