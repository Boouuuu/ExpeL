"""code2math eval env: write Python code and run provided test cases."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from envs.base import BaseEnv
from utils import parse_action


class CodeTrainEnv(BaseEnv):
    """
    Evaluation environment for code-generation tasks.

    The agent should respond with:
    - Test[<python code>]: required, must define a function. We then run test_cases.
    - Finish[<python code>]
    """

    def __init__(
        self,
        question: Optional[str] = None,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        key: Optional[str] = None,
        problem: Optional[Dict[str, Any]] = None,
        max_steps: int = 6,
    ):
        """
        Args:
            question: Plain-text question or prompt shown to the model.
            test_cases: Legacy field – structured test cases for non-HumanEval style tasks.
            key: Optional reference solution code / answer.
            problem: When using HumanEval-style data, this is a single problem dict
                containing at least: 'task_id', 'prompt', 'entry_point', 'test'.
        """
        # HumanEval-style problem (preferred for math2code)
        self.problem: Optional[Dict[str, Any]] = problem
        if self.problem is not None:
            # Use the HumanEval prompt as the natural language question.
            self.question = str(self.problem.get("prompt", question or ""))
            self.entry_point: Optional[str] = self.problem.get("entry_point")
            self.test_snippet: str = str(self.problem.get("test", ""))
        else:
            # Fallback: legacy JSON task format with explicit test_cases.
            self.question = str(question or "")
            self.entry_point = None
            self.test_snippet = ""

        # Keep legacy fields for backward compatibility (not used in HumanEval mode).
        self.test_cases = list(test_cases or [])
        self.key = key  # optional reference solution code (not required for grading)
        self.max_steps = max_steps
        self.task = (
            "Code writing task. Use the following actions to solve the problem:\n"
            "(1) Reason[step]: explain each logical / algorithmic step in natural language;\n"
            "(2) Implement[pattern]: write partial Python code skeletons (functions, loops, branches) "
            "with standard syntax and type hints;\n"
            "(3) Verify[case]: think through or simulate example inputs/outputs to check your logic;\n"
            "(4) Finish[code]: provide the complete Python solution, including function definition "
            "with type hints, docstring, and full implementation.\n"
            "We will run hidden tests (HumanEval-style when available) on the code inside Finish[code]."
        )
        self.env_name = "code2math_code"
        self.reset()

    def reset(self):
        self.curr_step = 1
        self.terminated = False
        self.truncated = False
        self.reward = False
        self.last_observation = ""
        self.submitted_code = ""
        self.passed = False

    def _extract_function_name(self, code: str) -> str | None:
        m = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", code, flags=re.MULTILINE)
        return m.group(1) if m else None

    def _normalize_code(self, code: str) -> str:
        """
        Heuristic normalization for model outputs that flatten Python into one line
        using spaces for indentation (common inside Finish[...]).
        """
        code = (code or "").strip()
        if not code:
            return code

        # If the code is already multiline, keep it as-is.
        if "\n" in code:
            return code

        # Insert newlines after block headers when they're followed by 4 spaces.
        while ":    " in code:
            code = code.replace(":    ", ":\n    ")

        # Insert newlines before common statement keywords when preceded by 4 spaces.
        # This helps transform "def f(...):    if ...:        return ..." into valid Python.
        for kw in ["if", "for", "while", "elif", "else", "return", "try", "except", "with", "raise"]:
            code = code.replace(f"    {kw} ", f"\n    {kw} ")
            code = code.replace(f"    {kw}:", f"\n    {kw}:")

        return code.strip()

    def _run_humaneval_tests(self, code: str) -> Tuple[bool, str]:
        """
        HumanEval-style evaluation: execute model code together with the
        official test snippet that defines `check(candidate)` and run it on
        the entry function.
        """
        if self.problem is None:
            return False, "Internal error: HumanEval problem metadata is missing."

        entry_point = self.entry_point or self.problem.get("entry_point")
        if not entry_point:
            return False, "Internal error: `entry_point` missing in HumanEval problem."

        code = self._normalize_code(code)
        if not code:
            return False, "Empty code."

        test_snippet = self.test_snippet or str(self.problem.get("test", ""))
        if not test_snippet.strip():
            return False, "Internal error: HumanEval test snippet is empty."

        # In HumanEval, the prompt already contains the function signature.
        # Here we expect Finish[code] to provide a *complete* solution
        # (including `def ...`), so we execute only the submitted code plus tests.
        check_program = f"{code}\n\n{test_snippet}\n\ncheck({entry_point})"

        global_ns: Dict[str, Any] = {"__builtins__": __builtins__}
        try:
            exec(compile(check_program, "<math2code_humaneval>", "exec"), global_ns, global_ns)
        except AssertionError as e:
            # At least one test assertion failed.
            return False, f"INCORRECT: test assertion failed: {e}"
        except Exception as e:
            # Any other runtime / syntax error is treated as failure.
            return False, f"ERROR: {type(e).__name__}: {e}"

        return True, "CORRECT"

    def _run_legacy_tests(self, code: str) -> Tuple[bool, str]:
        """
        Backward-compatible evaluation using explicit `test_cases` with
        (input, expected) pairs.
        """
        code = self._normalize_code(code)
        if not code:
            return False, "Empty code."

        fn_name = self._extract_function_name(code)
        if not fn_name:
            return False, "No function definition found (expected `def ...(...):`)."

        safe_globals: Dict[str, Any] = {"__builtins__": __builtins__}
        local_ns: Dict[str, Any] = {}
        try:
            exec(compile(code, "<math2code_submission>", "exec"), safe_globals, local_ns)
        except Exception as e:
            return False, f"Code execution error: {type(e).__name__}: {e}"

        fn = local_ns.get(fn_name) or safe_globals.get(fn_name)
        if not callable(fn):
            return False, f"Function `{fn_name}` not found after execution."

        for i, tc in enumerate(self.test_cases):
            inp = tc.get("input")
            expected = tc.get("expected")
            try:
                if isinstance(inp, dict):
                    out = fn(**inp)
                elif isinstance(inp, (list, tuple)):
                    out = fn(*inp)
                else:
                    out = fn(inp)
            except Exception as e:
                return False, f"Test case {i} runtime error: {type(e).__name__}: {e}"

            if out != expected:
                return False, f"Test case {i} failed: expected={expected!r}, got={out!r}"

        return True, "All test cases passed."

    def _run_tests(self, code: str) -> Tuple[bool, str]:
        """
        Dispatch to HumanEval-style evaluation when `problem` is provided;
        otherwise fall back to the legacy `test_cases`-based evaluator.
        """
        if self.problem is not None:
            return self._run_humaneval_tests(code)
        return self._run_legacy_tests(code)

    def step(self, action: str) -> Tuple[str, bool, bool, bool, int]:
        print("action:", action)
        action_type, argument = parse_action(action)
        print("action_type:", action_type)
        print("argument:", argument)
        if action_type == "Finish":
            self.submitted_code = (argument or "").strip()
            print("submitted_code:", self.submitted_code)
            ok, msg = self._run_tests(self.submitted_code)
            self.passed = ok
            self.reward = ok
            # For logging & stats, follow a HumanEval-style convention:
            # include "CORRECT" / "INCORRECT" tokens in the final observation.
            self.last_observation = (
                " CORRECT" if ok else f" INCORRECT: {msg}"
            )
            self.terminated = True
        elif action_type in {"Reason", "Implement", "Verify"}:
            # Support the new four-stage action space:
            # - Reason[step]: natural-language reasoning over the algorithm.
            # - Implement[pattern]: partial code skeletons and patterns.
            # - Verify[case]: manual or mental checking of example cases.
            # The environment itself does not change state beyond acknowledging
            # the action; the only graded step is Finish[code].
            self.last_observation = "OK."
        else:
            self.last_observation = (
                "Invalid Action. Valid Actions are:\n"
                "- Reason[step]\n"
                "- Implement[pattern]\n"
                "- Verify[case]\n"
                "- Finish[code]"
            )

        self.curr_step += 1
        self.truncated = self.is_truncated()
        self.terminated = self.is_terminated() or self.truncated
        return self.last_observation, self.reward, self.terminated, self.truncated, self.curr_step

    def success_fn(self) -> bool:
        return bool(self.passed)

