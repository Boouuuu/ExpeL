from typing import Callable, List

from . import alfworld
from . import hotpotQA, fever, webshop, math2code_math, code2math_code
from .templates.human import *
from .templates.system import *

FEWSHOTS = dict(
    hotpotqa=hotpotQA.FEWSHOTS,
    fever=fever.FEWSHOTS,
    alfworld=alfworld.FEWSHOTS,
    webshop=webshop.FEWSHOTS,
    math2code_math=math2code_math.FEWSHOTS,
    code2math_code=code2math_code.FEWSHOTS,
)
REFLECTION_FEWSHOTS = dict(
    hotpotqa=hotpotQA.REFLECTION_FEWSHOTS,
    fever=None,#fever.REFLECTION_FEWSHOTS,
    alfworld=alfworld.REFLECTION_FEWSHOTS,
    webshop=webshop.REFLECTION_FEWSHOTS,
    math2code_math=math2code_math.REFLECTION_FEWSHOTS,
    code2math_code=code2math_code.REFLECTION_FEWSHOTS,
)
SYSTEM_INSTRUCTION = dict(
    hotpotqa=hotpotQA.SYSTEM_INSTRUCTION,
    fever=fever.SYSTEM_INSTRUCTION,
    alfworld=alfworld.SYSTEM_INSTRUCTION,
    webshop=webshop.SYSTEM_INSTRUCTION,
    math2code_math=math2code_math.SYSTEM_INSTRUCTION,
    code2math_code=code2math_code.SYSTEM_INSTRUCTION,
)
SYSTEM_REFLECTION_INSTRUCTION = dict(
    hotpotqa=hotpotQA.SYSTEM_REFLECTION_INSTRUCTION,
    fever=None,#fever.SYSTEM_REFLECTION_INSTRUCTION,
    alfworld=None,#alfworld.SYSTEM_REFLECTION_INSTRUCTION,
    webshop=None,#webshop.SYSTEM_REFLECTION_INSTRUCTION,
    math2code_math=math2code_math.SYSTEM_REFLECTION_INSTRUCTION,
    code2math_code=code2math_code.SYSTEM_REFLECTION_INSTRUCTION,
)
HUMAN_INSTRUCTION = dict(
    hotpotqa=hotpotQA.HUMAN_INSTRUCTION,
    fever=fever.HUMAN_INSTRUCTION,
    alfworld=alfworld.HUMAN_INSTRUCTION,
    webshop=webshop.HUMAN_INSTRUCTION,
    math2code_math=math2code_math.HUMAN_INSTRUCTION,
    code2math_code=code2math_code.HUMAN_INSTRUCTION,
)
HUMAN_REFLECTION_INSTRUCTION = dict(
    hotpotqa=hotpotQA.HUMAN_REFLECTION_INSTRUCTION,
    fever=None,
    alfworld=alfworld.HUMAN_REFLECTION_INSTRUCTION,
    webshop=webshop.HUMAN_REFLECTION_INSTRUCTION,
    math2code_math=math2code_math.HUMAN_REFLECTION_INSTRUCTION,
    code2math_code=code2math_code.HUMAN_REFLECTION_INSTRUCTION,
)
SYSTEM_CRITIQUE_INSTRUCTION = dict(
    hotpotqa=dict(
        compare_existing_rules=hotpotQA.SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION,
        all_success_existing_rules=hotpotQA.SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION,
    ),
    fever=dict(
        compare_existing_rules=None,
        all_success_existing_riles=None
    ),
    alfworld=dict(
        compare_existing_rules=alfworld.SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION,
        all_success_existing_rules=alfworld.SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION,
    ),
    webshop=dict(
        compare_existing_rules=webshop.SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION,
        all_success_existing_rules=webshop.SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION,
    ),
    math2code_math=dict(
        compare_existing_rules=math2code_math.SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION,
        all_success_existing_rules=math2code_math.SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION,
    ),
    code2math_code=dict(
        compare_existing_rules=code2math_code.SYSTEM_CRITIQUE_EXISTING_RULES_INSTRUCTION,
        all_success_existing_rules=code2math_code.SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_RULES_INSTRUCTION,
    ),
)

LLM_PARSER = dict(
    hotpotqa=hotpotQA.LLM_PARSER,
    fever=hotpotQA.LLM_PARSER,
    alfworld=alfworld.LLM_PARSER,
    webshop=webshop.LLM_PARSER,
    math2code_math=math2code_math.LLM_PARSER,
    code2math_code=code2math_code.LLM_PARSER,
)

OBSERVATION_FORMATTER = dict(
    hotpotqa=hotpotQA.OBSERVATION_FORMATTER,
    fever=hotpotQA.OBSERVATION_FORMATTER,
    alfworld=alfworld.OBSERVATION_FORMATTER,
    webshop=webshop.OBSERVATION_FORMATTER,
    math2code_math=math2code_math.OBSERVATION_FORMATTER,
    code2math_code=code2math_code.OBSERVATION_FORMATTER,
)

STEP_IDENTIFIER = dict(
    hotpotqa=hotpotQA.STEP_IDENTIFIER,
    fever=hotpotQA.STEP_IDENTIFIER,
    webshop=webshop.STEP_IDENTIFIER,
    alfworld=alfworld.STEP_IDENTIFIER,
    math2code_math=math2code_math.STEP_IDENTIFIER,
    code2math_code=code2math_code.STEP_IDENTIFIER,
)

CYCLER = dict(
    hotpotqa=hotpotQA.CYCLER,
    fever=hotpotQA.CYCLER,
    webshop=webshop.CYCLER,
    alfworld=alfworld.CYCLER,
    math2code_math=math2code_math.CYCLER,
    code2math_code=code2math_code.CYCLER,
)
REFLECTION_PREFIX = dict(
    hotpotqa=hotpotQA.REFLECTION_PREFIX,
    fever=hotpotQA.REFLECTION_PREFIX,
    alfworld=alfworld.REFLECTION_PREFIX,
    webshop=webshop.REFLECTION_PREFIX,
    math2code_math=math2code_math.REFLECTION_PREFIX,
    code2math_code=code2math_code.REFLECTION_PREFIX,
)
PREVIOUS_TRIALS_FORMATTER=dict(
    hotpotqa=hotpotQA.PREVIOUS_TRIALS_FORMATTER,
    fever=hotpotQA.PREVIOUS_TRIALS_FORMATTER,
    alfworld=alfworld.PREVIOUS_TRIALS_FORMATTER,
    webshop=webshop.PREVIOUS_TRIALS_FORMATTER,
    math2code_math=math2code_math.PREVIOUS_TRIALS_FORMATTER,
    code2math_code=code2math_code.PREVIOUS_TRIALS_FORMATTER,
)

STEP_STRIPPER = dict(
    hotpotqa=hotpotQA.STEP_STRIPPER,
    fever=hotpotQA.STEP_STRIPPER,
    alfworld=alfworld.STEP_STRIPPER,
    webshop=webshop.STEP_STRIPPER,
    math2code_math=math2code_math.STEP_STRIPPER,
    code2math_code=code2math_code.STEP_STRIPPER,
)

def STEP_CYCLER(benchmark: str, lines: str, cycler: Callable, step_identifier: Callable, stripper: Callable = lambda x, y: x) -> List[str]:
    steps = []
    scratch_pad = ''
    for line in cycler(lines):
        step_type = step_identifier(line)
        stripped_line = stripper(line, step_type)
        scratch_pad += stripped_line + '\n'
        if step_type == 'observation':
            steps.append(scratch_pad.strip())
            scratch_pad = ''
    if scratch_pad != '':
        steps.append(scratch_pad.strip())
    return steps
