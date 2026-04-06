"""Code2Math 代码阶段：ReAct，动作 Test / Finish（HumanEval 风格数据）。"""
from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional, Tuple

from envs.base import BaseEnv
from utils import parse_action


class CodeTrainEnv(BaseEnv):
    """
    - Test[<python code>]: 在解释器中执行代码；对顶层 `assert` 逐条统计通过/失败。
    - Finish[<python code>]: 用当前任务的 `entry_point` 与官方 `test`（check(candidate)）评测。
    """

    def __init__(
        self,
        question: Optional[str] = None,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        key: Optional[str] = None,
        problem: Optional[Dict[str, Any]] = None,
        max_steps: int = 6,
    ):
        self.problem: Optional[Dict[str, Any]] = problem
        if self.problem is not None:
            self.question = str(self.problem.get("prompt", question or ""))
            self.entry_point: Optional[str] = self.problem.get("entry_point")
            self.test_snippet: str = str(self.problem.get("test", ""))
        else:
            self.question = str(question or "")
            self.entry_point = None
            self.test_snippet = ""

        self.test_cases = list(test_cases or [])
        self.key = key
        self.max_steps = max_steps
        self.task = (
            "Code completion (ReAct). Actions:\n"
            "(1) Test[<code>]: run with the Python interpreter. Put your implementation plus "
            "`assert` checks in the brackets; the observation lists passing / failing asserts.\n"
            "(2) Finish[<code>]: submit the final implementation; graded with hidden HumanEval-style tests."
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
        code = (code or "").strip()
        if not code or "\n" in code:
            return code
        while ":    " in code:
            code = code.replace(":    ", ":\n    ")
        for kw in ["if", "for", "while", "elif", "else", "return", "try", "except", "with", "raise"]:
            code = code.replace(f"    {kw} ", f"\n    {kw} ")
            code = code.replace(f"    {kw}:", f"\n    {kw}:")
        return code.strip()

    def _split_top_level_prelude_and_asserts(self, code: str, tree: ast.Module) -> Tuple[str, List[str]]:
        prelude_parts: List[str] = []
        assert_sources: List[str] = []
        for node in tree.body:
            seg = ast.get_source_segment(code, node)
            if seg is None:
                continue
            if isinstance(node, ast.Assert):
                assert_sources.append(seg.strip())
            else:
                prelude_parts.append(seg.strip())
        prelude = "\n\n".join(prelude_parts)
        return prelude, assert_sources

    def _describe_assert_failure(self, assert_src: str, ns: Dict[str, Any]) -> str:
        src = assert_src.strip()
        try:
            tree = ast.parse(src)
            stmt = tree.body[0]
            if isinstance(stmt, ast.Assert):
                test = stmt.test
                if (
                    isinstance(test, ast.Compare)
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.Eq)
                    and len(test.comparators) == 1
                ):
                    left_expr = ast.Expression(test.left)
                    ast.fix_missing_locations(left_expr)
                    left_val = eval(compile(left_expr, "<code2math_assert_lhs>", "eval"), ns, ns)
                    return f"{src} # output: {left_val!r}"
        except Exception:
            pass
        return f"{src} # error: AssertionError"

    def _run_test_action(self, raw_code: str) -> str:
        code = self._normalize_code(raw_code or "")
        if not code:
            return "Tests passing:\nNone\n\nTests failing:\nEmpty Test[...] code."
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Tests passing:\nNone\n\nTests failing:\n(SyntaxError: {e})"

        prelude, assert_sources = self._split_top_level_prelude_and_asserts(code, tree)
        ns: Dict[str, Any] = {"__builtins__": __builtins__}

        if prelude.strip():
            try:
                exec(compile(prelude, "<code2math_test_prelude>", "exec"), ns, ns)
            except Exception as e:
                return (
                    "Tests passing:\nNone\n\nTests failing:\n"
                    f"(prelude execution error: {type(e).__name__}: {e})"
                )

        if not assert_sources:
            try:
                exec(compile(code, "<code2math_test_full>", "exec"), ns, ns)
            except Exception as e:
                return (
                    "Tests passing:\nNone\n\nTests failing:\n"
                    f"(execution error: {type(e).__name__}: {e})"
                )
            return "Tests passing:\nNone\n\nTests failing:\nNone"

        passing: List[str] = []
        failing: List[str] = []
        for a_src in assert_sources:
            try:
                exec(compile(a_src, "<code2math_test_assert>", "exec"), ns, ns)
                passing.append(a_src)
            except AssertionError:
                failing.append(self._describe_assert_failure(a_src, ns))
            except Exception as e:
                failing.append(f"{a_src} # error: {type(e).__name__}: {e}")

        def block_lines(items: List[str]) -> str:
            return "None" if not items else "\n".join(items)

        return (
            "Tests passing:\n"
            f"{block_lines(passing)}\n\n"
            "Tests failing:\n"
            f"{block_lines(failing)}"
        )

    def _run_humaneval_tests(self, code: str) -> Tuple[bool, str]:
        if self.problem is None:
            return False, "missing problem metadata"

        entry_point = self.entry_point or self.problem.get("entry_point")
        if not entry_point:
            return False, "missing entry_point"

        code = self._normalize_code(code)
        if not code:
            return False, "empty code"

        test_snippet = self.test_snippet or str(self.problem.get("test", ""))
        if not test_snippet.strip():
            return False, "empty test snippet"

        check_program = f"{code}\n\n{test_snippet}\n\ncheck({entry_point})"
        global_ns: Dict[str, Any] = {"__builtins__": __builtins__}
        try:
            exec(compile(check_program, "<code2math_finish>", "exec"), global_ns, global_ns)
        except Exception:
            return False, "tests failed"
        return True, "ok"

    def _run_legacy_tests(self, code: str) -> Tuple[bool, str]:
        code = self._normalize_code(code)
        if not code:
            return False, "empty code"

        fn_name = self._extract_function_name(code)
        if not fn_name:
            return False, "no function definition"

        safe_globals: Dict[str, Any] = {"__builtins__": __builtins__}
        local_ns: Dict[str, Any] = {}
        try:
            exec(compile(code, "<code2math_legacy>", "exec"), safe_globals, local_ns)
        except Exception:
            return False, "execution error"

        fn = local_ns.get(fn_name) or safe_globals.get(fn_name)
        if not callable(fn):
            return False, "function not callable"

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
            except Exception:
                return False, f"case {i} error"

            if out != expected:
                return False, f"case {i} mismatch"

        return True, "ok"

    def _run_finish_tests(self, code: str) -> bool:
        if self.problem is not None:
            ok, _ = self._run_humaneval_tests(code)
            return ok
        ok, _ = self._run_legacy_tests(code)
        return ok

    def step(self, action: str) -> Tuple[str, bool, bool, bool, int]:
        action_type, argument = parse_action(action)
        if action_type == "Finish":
            self.submitted_code = (argument or "").strip()
            ok = self._run_finish_tests(self.submitted_code)
            self.passed = ok
            self.reward = ok
            self.last_observation = "Answer is correct." if ok else "Answer is incorrect."
            self.terminated = True
        elif action_type == "Test":
            self.last_observation = self._run_test_action(argument or "")
        else:
            self.last_observation = (
                "Invalid Action. Valid Actions are:\n"
                "- Test[<python code>]\n"
                "- Finish[<python code>]"
            )

        self.curr_step += 1
        self.truncated = self.is_truncated()
        self.terminated = self.is_terminated() or self.truncated
        return self.last_observation, self.reward, self.terminated, self.truncated, self.curr_step

    def success_fn(self) -> bool:
        return bool(self.passed)
