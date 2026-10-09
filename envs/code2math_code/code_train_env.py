"""Code2Math 代码阶段：ReAct，动作 Test / Finish（HumanEval 风格数据）。

支持两种题目格式，由 _is_program_style() 自动判别：
- HumanEval 风格（有 prompt/entry_point，check(candidate) 直接调用函数对象）：
  Test 逐条执行 assert；Finish 在同进程 exec 中 check(entry_point)。
- 整程序风格（CF 题，带 input_output 用例，check(candidate) 接收程序源码字符串
  并用 subprocess 跑 stdin/stdout）：
  Test/Finish 均将提交代码写入临时文件、用 subprocess 注入 stdin 并比对 stdout。
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from envs.base import BaseEnv
from utils import parse_action, trace_code2math_block


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
        verbose_trace: bool = False,
        success_criterion: Optional[str] = None,
    ):
        self.verbose_trace = verbose_trace
        # 'class_solution': Finish is considered correct iff the submitted code starts with
        # `class Solution` (placeholder correctness; real testing is done offline later).
        self.success_criterion = success_criterion
        self.problem: Optional[Dict[str, Any]] = problem
        if self.problem is not None:
            # self.question = str(self.problem.get("prompt", question or ""))
            self.question = str(self.problem.get("problem_description", "")) + str(self.problem.get("starter_code", question or ""))
            # self.question = str(self.problem.get("instruct_prompt", ""))

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
        self.last_action_detail = ""

    def _extract_function_name(self, code: str) -> str | None:
        m = re.search(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", code, flags=re.MULTILINE)
        return m.group(1) if m else None

    def _is_program_style(self) -> bool:
        """判断当前 problem 是否为整程序（CF stdin/stdout）风格。

        命中条件（任一）：
        - problem 带非空 input_output 用例列表；
        - test 代码段里的 check 使用 subprocess（该数据集的 check 期望源码字符串）。
        其余情况（如原版 HumanEval：check 直接调用 candidate 函数）返回 False，
        走保留的原有逻辑。
        """
        if self.problem is None:
            return False
        cases = self.problem.get("input_output")
        if isinstance(cases, str):
            try:
                cases = json.loads(cases)
            except json.JSONDecodeError:
                cases = None
        if cases:
            return True
        test_snippet = self.test_snippet or str(self.problem.get("test", ""))
        return "subprocess" in test_snippet

    def _get_input_output_cases(self) -> List[Dict[str, Any]]:
        cases = (self.problem or {}).get("input_output") or []
        if isinstance(cases, str):
            try:
                cases = json.loads(cases)
            except json.JSONDecodeError:
                return []
        return [c for c in cases if isinstance(c, dict)]

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

    def _run_program_test_action(self, raw_code: str) -> str:
        """整程序风格 Test：用 subprocess 逐个跑 input_output 用例（注入 stdin、比对 stdout）。

        不在训练进程内 exec 提交代码，避免 input()/sys.stdin.read() 阻塞终端或
        死循环卡死训练；subprocess 自带超时。
        """
        code = self._normalize_code(raw_code or "")
        if not code:
            return "Tests passing:\nNone\n\nTests failing:\nEmpty Test[...] code."
        try:
            ast.parse(code)
        except SyntaxError as e:
            return f"Tests passing:\nNone\n\nTests failing:\n(SyntaxError: {e})"

        cases = self._get_input_output_cases()
        if not cases:
            return (
                "Tests passing:\nNone\n\nTests failing:\n"
                "(No public input_output cases available for this problem.)"
            )

        passing: List[str] = []
        failing: List[str] = []
        for i, case in enumerate(cases):
            inp = str(case.get("input", ""))
            expected = str(case.get("output", "")).strip()
            labeled = f"case {i + 1}: input={inp!r} expected_output={expected!r}"
            path = None
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
                    f.write(code)
                    path = f.name
                p = subprocess.run(
                    [sys.executable, path],
                    input=inp,
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                failing.append(f"{labeled} # error: Timeout (10s)")
                continue
            except Exception as e:
                failing.append(f"{labeled} # error: {type(e).__name__}: {e}")
                continue
            finally:
                if path:
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
            if p.returncode != 0:
                err_lines = (p.stderr or "").strip().splitlines()
                failing.append(f"{labeled} # runtime error: {err_lines[-1] if err_lines else 'unknown stderr'}")
            elif p.stdout.strip() == expected:
                passing.append(labeled)
            else:
                failing.append(f"{labeled} # got={p.stdout!r}")

        def block_lines(items: List[str]) -> str:
            return "None" if not items else "\n".join(items)

        return (
            "Tests passing:\n"
            f"{block_lines(passing)}\n\n"
            "Tests failing:\n"
            f"{block_lines(failing)}"
        )

    def _run_test_action(self, raw_code: str) -> str:
        # 整程序风格（CF）：走 subprocess 用例运行；HumanEval 风格保留下方 assert 逻辑。
        if self._is_program_style():
            return self._run_program_test_action(raw_code)
        code = self._normalize_code(raw_code or "")
        if not code:
            return "Tests passing:\nNone\n\nTests failing:\nEmpty Test[...] code."
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Tests passing:\nNone\n\nTests failing:\n(SyntaxError: {e})"

        prelude, assert_sources = self._split_top_level_prelude_and_asserts(code, tree)
        ns: Dict[str, Any] = {"__builtins__": __builtins__}

        # 防护：临时截断 stdin，避免残留的 input()/sys.stdin.read() 阻塞终端等待用户输入
        # （EOFError 会作为执行错误如实报告）。整程序风格已在上方走 subprocess，不受影响。
        real_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        try:
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
        finally:
            sys.stdin = real_stdin

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

        code = self._normalize_code(code)
        if not code:
            return False, "empty code"

        test_snippet = self.test_snippet or str(self.problem.get("test", ""))
        if not test_snippet.strip():
            return False, "empty test snippet"

        prompt_prelude = str(self.problem.get("prompt", ""))
        if self._is_program_style():
            # 整程序风格（CF）：数据自带的 check(candidate) 期望收到程序源码字符串，
            # 由 check 内部写临时文件 + subprocess 运行（自带超时与 stdin 注入）。
            candidate_src = f"{prompt_prelude}\n\n{code}" if prompt_prelude.strip() else code
            check_program = f"{test_snippet}\n\ncheck({candidate_src!r})"
        else:
            # HumanEval 风格：check 直接接收同命名空间中定义的 candidate 函数。
            entry_point = self.entry_point or self.problem.get("entry_point")
            if not entry_point:
                return False, "missing entry_point"
            check_program = f"{prompt_prelude}\n\n{code}\n\n{test_snippet}\n\ncheck({entry_point})"
        global_ns: Dict[str, Any] = {"__builtins__": __builtins__}
        try:
            exec(compile(check_program, "<code2math_finish>", "exec"), global_ns, global_ns)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
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

    def _trace_action(self, action_type: str, argument: str, detail: str = "") -> None:
        if not self.verbose_trace:
            return
        meta = []
        if self.problem is not None:
            for key in ("task_id", "entry_point"):
                val = self.problem.get(key)
                if val:
                    meta.append(f"{key}={val}")
        header = f"step {self.curr_step}"
        if meta:
            header += f" | {', '.join(meta)}"
        trace_code2math_block(
            f"{header} | Action={action_type}",
            f"Submitted code:\n{(argument or '').strip() or '(empty)'}\n\n"
            f"{detail}".strip(),
        )

    def step(self, action: str) -> Tuple[str, bool, bool, bool, int]:
        action_type, argument = parse_action(action)
        self.last_action_detail = ""
        if action_type == "Finish":
            self.submitted_code = (argument or "").strip()
            if self.success_criterion == 'class_solution':
                ok = self.submitted_code.startswith('class Solution')
                detail = f"starts_with_class_solution={ok}"
            elif self.problem is not None:
                ok, detail = self._run_humaneval_tests(self.submitted_code)
            else:
                ok, detail = self._run_legacy_tests(self.submitted_code)
            self.last_action_detail = detail
            self.passed = ok
            self.reward = ok
            if ok:
                self.last_observation = "Answer is correct."
            else:
                # 附带失败原因，便于 agent 在反思/批评阶段针对性修正
                self.last_observation = f"Answer is incorrect.\n(Detail: {detail})"
            self.terminated = True
            self._trace_action(
                action_type,
                self.submitted_code,
                f"Finish evaluation: {'PASS' if ok else 'FAIL'}\nDetail: {detail}",
            )
        elif action_type == "Test":
            self.last_observation = self._run_test_action(argument or "")
            self.last_action_detail = self.last_observation
            self._trace_action(action_type, argument or "", self.last_observation)
        else:
            self.last_observation = (
                "Invalid Action. Valid Actions are:\n"
                "- Test[<python code>]\n"
                "- Finish[<python code>]"
            )
            self.last_action_detail = self.last_observation
            self._trace_action(action_type or "Invalid", argument or "", self.last_observation)

        self.curr_step += 1
        self.truncated = self.is_truncated()
        self.terminated = self.is_terminated() or self.truncated
        return self.last_observation, self.reward, self.terminated, self.truncated, self.curr_step

    def success_fn(self) -> bool:
        return bool(self.passed)
