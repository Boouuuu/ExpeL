"""Math-only training env: Reason / Calculate / Finish. No code execution."""
import re
import ast
import operator
from typing import Tuple

from envs.base import BaseEnv
from utils import parse_action, EM

# Safe operators for Calculate[expr]
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(expr: str):
    """Evaluate a simple numeric expression. Raises on invalid input."""
    expr = expr.strip()
    if not re.match(r"^[\d\s\+\-\*\/\.\(\)]+$", expr):
        raise ValueError("Invalid characters in expression")
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if type(node) not in (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant):
            raise ValueError("Only numeric expressions allowed")
        if isinstance(node, (ast.BinOp, ast.UnaryOp)):
            if type(node.op) not in _SAFE_OPS:
                raise ValueError("Disallowed operator")
    return eval(expr)


class MathTrainEnv(BaseEnv):
    """Training environment: solve math problems with Reason / Calculate / Finish."""

    def __init__(
        self,
        question: str,
        key: str,
        max_steps: int = 6,
    ):
        self.question = question
        self.key = str(key).strip()
        self.max_steps = max_steps
        self.task = "Math problem-solving. Use Reason[step], Calculate[expression], and Finish[answer]."
        self.env_name = "math2code_math"
        self.reset()

    def reset(self):
        self.curr_step = 1
        self.answer = ""
        self.terminated = False

    def step(self, action: str) -> Tuple[str, bool, bool, bool, bool]:
        action_type, argument = parse_action(action)

        if action_type == "Finish":
            self.answer = argument.strip()
            if self.success_fn():
                observation = "Answer is CORRECT"
            else:
                observation = "Answer is INCORRECT"
            self.terminated = True
        elif action_type == "Reason":
            observation = "OK."
        elif action_type == "Calculate":
            try:
                val = _safe_eval(argument)
                observation = f"Result: {val}"
            except Exception as e:
                observation = f"Calculate error: {e}"
        else:
            observation = "Invalid Action. Valid Actions are Reason[<step>], Calculate[<expression>], and Finish[<answer>]."

        self.curr_step += 1
        self.reward = self.success_fn()
        self.terminated = self.is_terminated()
        self.truncated = self.is_truncated()
        return observation, self.reward, self.terminated, self.truncated, self.curr_step

    def success_fn(self) -> bool:
        return EM(self.answer, self.key)
