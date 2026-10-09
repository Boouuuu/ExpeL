"""Chemistry-only training env: Search / Finish."""
import re
import ast
import operator
import os
from typing import Tuple
import requests


from envs.base import BaseEnv
from utils import parse_action

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


class ChemTrainEnv(BaseEnv):
    """Training environment: solve chemistry problems with Search / Finish."""

    def __init__(
        self,
        question: str,
        key: str,
        max_steps: int = 6,
        verbose_trace: bool = False,
    ):
        self.verbose_trace = verbose_trace
        self.question = question
        self.key = str(key).strip()
        self.max_steps = max_steps
        self.task = "Chemistry problem-solving. Use Search[query], and Finish[answer]."
        self.env_name = "chemistry2code_chemistry"
        self.manual_verified_correct = None
        self.reset()

    def reset(self):
        self.curr_step = 1
        self.answer = ""
        self.terminated = False
        self.manual_verified_correct = None

    def step(self, action: str) -> Tuple[str, bool, bool, bool, bool]:
        action_type, argument = parse_action(action)

        if action_type == "Finish":
            self.answer = argument.strip()
            if self.success_fn():
                observation = "Answer is CORRECT"
            else:
                observation = "Answer is INCORRECT"
            self.terminated = True
        elif action_type == "Search":
            query = (argument or "").strip()
            if not query:
                observation = "Search error: empty query."
            else:
                api_key = os.environ.get("TAVILY_API_KEY", "")
                if not api_key:
                    observation = "Search error: TAVILY_API_KEY is not set."
                else:
                    try:
                        resp = requests.post(
                            "https://api.tavily.com/search",
                            json={
                                "api_key": api_key,
                                "query": query,
                                "search_depth": "basic",
                                "include_answer": True,
                                "max_results": 1,
                            },
                            timeout=20,
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        snippets = []

                        answer = (data.get("answer") or "").strip()
                        if answer:
                            snippets.append(f"Answer: {answer}")

                        for idx, item in enumerate(data.get("results", [])[:3], start=1):
                            title = (item.get("title") or "").strip()
                            content = (item.get("content") or "").strip()
                            url = (item.get("url") or "").strip()
                            line = f"{idx}. "
                            if title:
                                line += title
                            if content:
                                line += f" - {content}"
                            if url:
                                line += f" ({url})"
                            snippets.append(line.strip())

                        observation = "\n".join(snippets) if snippets else "No search results found."
                    except Exception as e:
                        observation = f"Search error: {e}"
        
        else:
            observation = "Invalid Action. Valid Actions are Search[<query>] and Finish[<answer>]."

        self.curr_step += 1
        self.reward = self.success_fn()
        self.terminated = self.is_terminated()
        self.truncated = self.is_truncated()
        return observation, self.reward, self.terminated, self.truncated, self.curr_step

    
    def success_fn(self) -> bool:
        if self.manual_verified_correct is not None:
            return self.manual_verified_correct
        # 直接识别 Finish[...] 中的内容作为答案，与标准答案规范化后比较
        return self.answer.strip().upper() == self.key.strip().upper()
