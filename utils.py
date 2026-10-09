import random
import string
from typing import List, Dict, Callable, Tuple, Any, Union
from matplotlib import pyplot as plt
import tiktoken
from langchain.schema import (
    ChatMessage
)

from prompts import FEWSHOTS

import math
import pickle
import re
# 放在 Python 文件 最顶部
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


ENV_NAMES = [
            'pick_and_place',
            'pick_clean_then_place',
            'pick_heat_then_place',
            'pick_cool_then_place',
            'look_at_obj',
            'pick_two_obj'
        ]

TASK_ENV_NAMES = [
    ('clean', 'pick_clean_then_place'),
    ('hot', 'pick_heat_then_place'),
    ('heat', 'pick_heat_then_place'),
    ('cool', 'pick_cool_then_place'),
    ('look', 'look_at_obj'),
    ('examine', 'look_at_obj'),
    ('two', 'pick_two_obj'),
    ('put', 'pick_and_place') # last one must be at last position
]

class Count:
    """
    Class for reflection counting.
    """
    def __init__(self, maximum):
        self.count = 0
        self.maximum = maximum

    def increment(self):
        self.count += 1
        if self.count > self.maximum:
            self.count = self.maximum

    def is_beginning(self):
        return self.count == 1

    def reset(self):
        self.count = 0

    def is_maximum(self):
        return self.count == self.maximum

def random_divide_list(lst: List[Any], k: int):
    """
    Divides the list into chunks, each with maximum length k.

    Args:
        lst: The list to be divided.
        k: The maximum length of each chunk.

    Returns:
        A list of chunks.
    """
    random.shuffle(lst)
    if len(lst) <= k:
        return [lst]
    else:
        num_chunks = math.ceil(len(lst) / k)
        chunk_size = math.ceil(len(lst) / num_chunks)
        return [lst[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]

def shuffled_chunks(lst: List[Any], num_chunks: int):
    """
    Divides the list into chunks as equally as possible.

    Args:
        lst: The list to be divided.
        num_chunks: The number of chunks.

    Returns:
        A list of chunks.
    """
    random.shuffle(lst)
    chunk_size = len(lst) // num_chunks
    remainder = len(lst) % num_chunks
    chunks = [lst[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
    
    # Distribute the remainder elements across the chunks
    if remainder > 0:
        for i in range(remainder):
            chunks[i].append(lst[num_chunks * chunk_size + i])
    
    random.shuffle(chunks)
    return chunks

def token_counter(text: str, llm: str = 'gpt-3.5-turbo', tokenizer: Callable = None) -> int:
    """
    Counts the number of tokens in the text.
    
    Args:
        text: The text to be counted.
        llm: The language model name.
        tokenizer: The tokenizer to be used.
    """
    if not text:
        return 0
    if tokenizer is not None:
        encoded = tokenizer.encode(text)
        return len(encoded) if hasattr(encoded, '__len__') else encoded

    llm_lower = llm.lower()
    if 'gpt' in llm_lower:
        try:
            return len(tiktoken.encoding_for_model(llm).encode(text))
        except KeyError:
            return len(tiktoken.get_encoding('cl100k_base').encode(text))

    # GLM / Qwen / other models: approximate with cl100k_base for truncation checks
    return len(tiktoken.get_encoding('cl100k_base').encode(text))


def prompt_manual_finish_review(
    correct_answer: str,
    submitted_answer: str,
    question: str = "",
    task_idx: int = None,
) -> bool:
    """Print Finish vs ground-truth and wait for human judgment. Returns True if correct."""
    header = f"[Manual Finish Review] TASK {task_idx}" if task_idx is not None else "[Manual Finish Review]"
    print(f"\n{'=' * 60}", flush=True)
    print(header, flush=True)
    print("自动判定：错误（EM 不匹配）", flush=True)
    if question:
        print(f"题目     : {question}", flush=True)
    print(f"标准答案 : {correct_answer}", flush=True)
    print(f"Finish答案: {submitted_answer}", flush=True)
    print(f"{'=' * 60}", flush=True)

    _ACCEPT_CORRECT = {'y', 'yes', 'c', 'correct', 'true', '1', '是', '对', '正确'}
    _ACCEPT_INCORRECT = {'n', 'no', 'w', 'wrong', 'false', '0', '否', '错', '错误'}

    while True:
        choice = input("请人工判定 Finish 答案是否正确？(y=正确 / n=错误): ").strip().lower()
        if choice in _ACCEPT_CORRECT:
            print("[Manual Finish Review] 人工判定：正确\n", flush=True)
            return True
        if choice in _ACCEPT_INCORRECT:
            print("[Manual Finish Review] 人工判定：错误\n", flush=True)
            return False
        print("无效输入，请输入 y（正确）或 n（错误）。", flush=True)


def print_message(message: Union[dict, ChatMessage], token_counter: Callable = None, testing: bool = True, extra_text: str = '') -> None:
    """
    Prints the formatted message.
    
    Args:
        message: The message to be printed (either dict or ChatMessage).
        token_counter: A function that takes in a string and returns the number of tokens in the string.
        testing: Add message type and token count in testing mode.
        extra_text: Extra text to be printed after the message in testing mode.
    """
    # 处理dict格式的消息
    if isinstance(message, dict):
        message_type = message.get('role', 'unknown')
        message_content = message.get('content', '')
    else:
        # 兼容原有的ChatMessage格式
        message_type = message.type
        message_content = message.content
    
    if testing:
        formatted_message = f"$$${message_type}$$$\t{message_content}\t$$${message_type}$$$"
        if token_counter is not None:
            formatted_message += f"\t***{token_counter(message_content)} tokens***"
            formatted_message += extra_text
        print(formatted_message)
    else:
        print(message_content)


def trace_code2math_block(
    title: str,
    content: str,
    *,
    max_len: int = 4000,
) -> None:
    """在 verbose_trace 模式下打印 code2math_code 流程块。"""
    body = (content or "").strip()
    if len(body) > max_len:
        body = body[:max_len] + f"\n... [truncated, total {len(content)} chars]"
    print(f"\n{'=' * 20} [TRACE] {title} {'=' * 20}")
    print(body)
    print("=" * (44 + len(title)))


def trace_prompt_history(
    prompt_history: List[dict],
    label: str,
    benchmark_name: str = None,
    max_preview: int = 120000,
) -> None:
    """
    当 benchmark 为 math2code / math2code_math 时，将 prompt_history 的变化打印到控制台，
    用于跟踪 eval 运行时 self.prompt_history 的演变。
    """
    if benchmark_name not in ('math2code_math', 'physics2code_physics', 'chemistry2code_chemistry', 'code2math_code'):
        return
    print(f"\n>>> [prompt_history] {label}")
    print(f"    len(prompt_history) = {len(prompt_history)}")
    for i, msg in enumerate(prompt_history):
        role = msg.get('role', '?') if isinstance(msg, dict) else getattr(msg, 'type', '?')
        content = msg.get('content', '') if isinstance(msg, dict) else getattr(msg, 'content', '')
        n = len(content)
        preview = (content[:max_preview] + '...') if n > max_preview else content
        preview = preview.replace('\n', ' ')
        print(f"    [{i}] role={role} len={n} | {preview}")
    print("<<<\n")


# 原代码
# def parse_action(string: str):
#     """
#     Parse action string into action type and argument for HotpotQA and Fever.
    
#     Args:
#         string: action string
    
#     Returns:
#         action_type: action type
#         argument: argument
#     """
#     # Support multiline arguments inside [...] (e.g., code blocks in Finish[...])
#     # and allow empty arguments if the caller ever uses Action[].
#     pattern = r'^(\w+)\[(.*)\]$'
#     match = re.match(pattern, string, flags=re.DOTALL)
    
#     if match:
#         action_type = match.group(1)
#         argument = match.group(2)
#         return action_type, argument
    
#     else:
#         return None, None

def parse_action(text: str):
    """
    专门解析 LLM 输出中的 Action（仅支持 Search / Test / Finish）

    支持：
    - 多行代码
    - 嵌套括号
    - 忽略 List[...] / typing[...] 等干扰

    返回：
        (action_type, content) 或 (None, None)
    """

    ACTION_TYPES = ("Search", "Test", "Finish")
    matches = []

    i = 0
    n = len(text)

    while i < n:
        # 检查是否匹配某个 Action 类型
        for action in ACTION_TYPES:
            prefix = action + "["
            if text.startswith(prefix, i):
                start = i + len(prefix)

                # 栈匹配括号
                bracket_count = 1
                j = start

                while j < n and bracket_count > 0:
                    if text[j] == '[':
                        bracket_count += 1
                    elif text[j] == ']':
                        bracket_count -= 1
                    j += 1

                if bracket_count == 0:
                    content = text[start:j-1]
                    matches.append((action, content.strip()))
                    i = j  # 跳到匹配结束
                    break
        else:
            i += 1  # 没匹配到任何 action，继续

    if not matches:
        return None, None

    return matches[-1]

"""
math_em.py - 数学答案等价性判断
整合了两个版本的能力：
  - 原版：Fraction 精确有理数解析（快速路径）
  - 参考版：_strip_string 规范化 + sympy 符号等价 + 列表顺序无关比较

判断层次（is_equiv）：
  1. 预处理：text{...} 提取、千位分隔符移除
  2. _strip_string 规范化后字符串完全相等
  3. 列表/集合顺序无关比较
  4. sympy 符号/数值等价（有理化、负指数、根式等）
  5. normalize_answer 兜底（冠词、标点等非数学文本）
  6. 原始字符串相等

EM() 是对外的主接口，保持与原版签名兼容。
"""

import re
import string as _string
from fractions import Fraction

# ──────────────────────────────────────────────────────────────
# 第一层：字符串规范化辅助函数（来自参考文件，修复 SyntaxWarning）
# ──────────────────────────────────────────────────────────────

def _fix_fracs(string):
    """将 \frac12 / \frac1b 等无括号写法规范化为 \frac{1}{2}。"""
    substrs = string.split("\\frac")
    new_str = substrs[0]
    if len(substrs) > 1:
        substrs = substrs[1:]
        for substr in substrs:
            new_str += "\\frac"
            if substr[0] == "{":
                new_str += substr
            else:
                try:
                    assert len(substr) >= 2
                except Exception:
                    return string
                a = substr[0]
                b = substr[1]
                if b != "{":
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}{" + b + "}" + post_substr
                    else:
                        new_str += "{" + a + "}{" + b + "}"
                else:
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}" + b + post_substr
                    else:
                        new_str += "{" + a + "}" + b
    return new_str


def _fix_a_slash_b(string):
    """将 {a}/{b} 格式规范化为 \frac{a}{b}。"""
    if len(string.split("/")) != 2:
        return string
    a_str, b_str = string.split("/")
    try:
        a = int(a_str)
        b = int(b_str)
        assert string == "{}/{}".format(a, b)
        return "\\frac{" + str(a) + "}{" + str(b) + "}"
    except Exception:
        return string


def _remove_right_units(string):
    """移除 \text{ unit} 形式的单位后缀。"""
    if "\\text{ " in string:
        splits = string.split("\\text{ ")
        assert len(splits) == 2
        return splits[0]
    return string


def _fix_sqrt(string):
    """将 sqrt2 规范化为 sqrt{2}（不带花括号时补齐）。"""
    if "\\sqrt" not in string:
        return string
    splits = string.split("\\sqrt")
    new_string = splits[0]
    for split in splits[1:]:
        if split[0] != "{":
            a = split[0]
            new_substr = "\\sqrt{" + a + "}" + split[1:]
        else:
            new_substr = "\\sqrt" + split
        new_string += new_substr
    return new_string


def _extract_text_content(string):
    r"""
    将 \text{...} 替换为其内容，并去掉外层括号。
    例如：\text{Tuesday} -> Tuesday，\text{(B)} -> B
    """
    def replacer(m):
        inner = m.group(1).strip()
        inner = re.sub(r'^\(([^)]*)\)$', r'\1', inner)
        return inner
    return re.sub(r'\\text\{([^}]*)\}', replacer, string)


def _remove_numeric_separators(string):
    r"""
    移除 LaTeX 数字分隔符 \! 并处理千位逗号。
    例如：85,\!184 -> 85184，1,000,000 -> 1000000
    """
    string = string.replace("\\!", "")
    if re.match(r'^-?\d{1,3}(,\d{3})+$', string):
        string = string.replace(",", "")
    return string


def _strip_string(string):
    """
    将数学表达式字符串规范化为统一形式，便于后续比较。
    处理范围：换行、\\!、dfrac/tfrac、left/right、
              角度符号、$、单位、百分号、前导小数点、
              k= 前缀、sqrt、空格、frac 写法、0.5 特化
    """
    string = string.replace("\n", "")
    string = string.replace("\\!", "")
    string = string.replace("\\\\", "\\")

    # dfrac / tfrac / cfrac → frac
    string = string.replace("tfrac", "frac")
    string = string.replace("dfrac", "frac")
    string = string.replace("cfrac", "frac")

    string = string.replace("\\left", "")
    string = string.replace("\\right", "")

    # 角度
    string = string.replace("^{\\circ}", "")
    string = string.replace("^\\circ", "")

    # 美元符号：转义的 \$ 和裸的 $（$...$、$$...$$）
    string = string.replace("\\$", "")
    string = string.strip("$")

    string = _remove_right_units(string)

    # 百分号
    string = string.replace("\\%", "")
    string = string.replace(r"\%", "")

    # 前导小数点修复
    string = string.replace(" .", " 0.")
    string = string.replace("{.", "{0.")
    if len(string) == 0:
        return string
    if string[0] == ".":
        string = "0" + string

    # 去掉 "k = " 前缀（如 "x = 3" → "3"）
    if len(string.split("=")) == 2:
        if len(string.split("=")[0]) <= 2:
            string = string.split("=")[1]

    string = _fix_sqrt(string)
    string = string.replace(" ", "")
    string = _fix_fracs(string)

    # 0.5 → \frac{1}{2}（特化以覆盖更多等价场景）
    if string == "0.5":
        string = "\\frac{1}{2}"

    string = _fix_a_slash_b(string)
    return string


# ──────────────────────────────────────────────────────────────
# 第二层：sympy 符号/数值等价
# ──────────────────────────────────────────────────────────────

def _latex_to_sympy(s):
    """
    将规范化后的 LaTeX 字符串递归解析为 sympy 表达式。
    支持：frac{a}{b}  sqrt{a}  sqrt[n]{a}  ^{n}  + - *
          隐式系数（如 3*sqrt(7)）、负号、整数/浮点数、单字母变量。
    """
    import sympy as sp

    def _matching_brace(s, start):
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
        raise ValueError(f"unmatched brace in: {s}")

    def _matching_paren(s, start):
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
        raise ValueError(f"unmatched paren in: {s}")

    def _find_top_level_char(s, ch):
        depth = 0
        for i in range(len(s) - 1, -1, -1):
            c = s[i]
            if c in '})':
                depth += 1
            elif c in '{(':
                depth -= 1
            elif c == ch and depth == 0:
                return i
        return -1

    def _split_top_level(s, delimiters):
        parts, depth, current, current_sign = [], 0, [], '+'
        i = 0
        while i < len(s):
            c = s[i]
            if c in '{(':
                depth += 1
            elif c in '})':
                depth -= 1
            elif depth == 0 and c in delimiters and i > 0:
                parts.append((current_sign, ''.join(current).strip()))
                current, current_sign = [], c
                i += 1
                continue
            current.append(c)
            i += 1
        if current:
            parts.append((current_sign, ''.join(current).strip()))
        return parts

    def _split_top_level_mul(s):
        parts, depth, current = [], 0, []
        for c in s:
            if c in '{(':
                depth += 1
            elif c in '})':
                depth -= 1
            elif c == '*' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
                continue
            current.append(c)
        if current:
            parts.append(''.join(current).strip())
        return parts

    def parse_expr(s):
        s = s.strip()
        while s.startswith("(") and s.endswith(")") and _matching_paren(s, 0) == len(s) - 1:
            s = s[1:-1].strip()
        while s.startswith("{") and s.endswith("}") and _matching_brace(s, 0) == len(s) - 1:
            s = s[1:-1].strip()
        terms = _split_top_level(s, ('+', '-'))
        if len(terms) > 1:
            result = None
            for sign, term in terms:
                val = parse_mul(term)
                result = val if result is None else (result + val if sign == '+' else result - val)
            return result
        return parse_mul(s)

    def parse_mul(s):
        s = s.strip()
        factors = _split_top_level_mul(s)
        if len(factors) > 1:
            result = sp.Integer(1)
            for f in factors:
                result = result * parse_pow(f)
            return result
        return parse_pow(s)

    def parse_pow(s):
        s = s.strip()
        idx = _find_top_level_char(s, '^')
        if idx != -1:
            base = parse_atom(s[:idx])
            exp_str = s[idx + 1:].strip()
            if exp_str.startswith("{"):
                close = _matching_brace(exp_str, 0)
                exp = parse_expr(exp_str[1:close])
                tail = exp_str[close + 1:]
            else:
                exp = parse_atom(exp_str[0])
                tail = exp_str[1:]
            result = base ** exp
            if tail:
                result = result * parse_atom(tail)
            return result
        return parse_atom(s)

    def parse_atom(s):
        s = s.strip()
        if not s:
            return sp.Integer(0)

        # \frac{a}{b}
        if s.startswith("\\frac"):
            rest = s[5:].strip()
            if rest.startswith("{"):
                c1 = _matching_brace(rest, 0)
                num = parse_expr(rest[1:c1])
                rest2 = rest[c1 + 1:].strip()
                if rest2.startswith("{"):
                    c2 = _matching_brace(rest2, 0)
                    den = parse_expr(rest2[1:c2])
                    tail = rest2[c2 + 1:]
                    result = num / den
                    return result * parse_expr(tail) if tail.strip() else result
            raise ValueError(f"bad frac: {s}")

        # \sqrt[n]{a} 或 \sqrt{a}
        if s.startswith("\\sqrt"):
            rest = s[5:].strip()
            n = 2
            if rest.startswith("["):
                close_bracket = rest.index("]")
                n = int(rest[1:close_bracket])
                rest = rest[close_bracket + 1:].strip()
            if rest.startswith("{"):
                c = _matching_brace(rest, 0)
                inner = parse_expr(rest[1:c])
                tail = rest[c + 1:]
                result = inner ** sp.Rational(1, n)
                return result * parse_expr(tail) if tail.strip() else result
            raise ValueError(f"bad sqrt: {s}")

        # 负号
        if s.startswith("-"):
            return -parse_atom(s[1:])

        # 整数
        try:
            return sp.Integer(int(s))
        except ValueError:
            pass

        # 浮点数
        try:
            return sp.Float(float(s))
        except ValueError:
            pass

        # 单字母变量
        if re.match(r'^[a-zA-Z]$', s):
            return sp.Symbol(s)

        # 隐式乘法：数字前缀 + 后续原子，如 3\sqrt{7}
        m = re.match(r'^(-?\d+(?:\.\d+)?)(\\?.+)$', s)
        if m:
            return parse_atom(m.group(1)) * parse_atom(m.group(2))

        # 去括号重试
        if s.startswith("(") and s.endswith(")"):
            return parse_expr(s[1:-1])
        if s.startswith("{") and s.endswith("}"):
            return parse_expr(s[1:-1])

        raise ValueError(f"cannot parse atom: '{s}'")

    return parse_expr(s)


def _try_sympy_equiv(s1, s2):
    """
    用 sympy 判断两个规范化后的 LaTeX 字符串是否等价。
    返回 True/False/None（None 表示无法解析，跳过此层）。
    """
    try:
        import sympy as sp
        expr1 = _latex_to_sympy(s1)
        expr2 = _latex_to_sympy(s2)
        diff = sp.simplify(expr1 - expr2)
        if diff == 0:
            return True
        # 数值近似兜底（处理 sympy.simplify 无法化简的情况）
        try:
            val = complex(sp.N(diff, 20))
            if abs(val) < 1e-9:
                return True
        except Exception:
            pass
        return False
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# 第三层：列表 / 集合顺序无关比较
# ──────────────────────────────────────────────────────────────

def _split_list(string):
    """按顶层逗号分割数学列表（不切入花括号/括号内）。"""
    result, depth, current = [], 0, []
    for ch in string:
        if ch in "{(":
            depth += 1
            current.append(ch)
        elif ch in "})":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        result.append("".join(current).strip())
    return result


def _is_list_string(string):
    return len(_split_list(string)) > 1


def _list_equiv(s1, s2):
    """把两个字符串当作集合（顺序无关）比较，元素递归用 is_equiv 判断。"""
    parts1 = _split_list(s1)
    parts2 = _split_list(s2)
    if len(parts1) != len(parts2):
        return False
    used = [False] * len(parts2)
    for p1 in parts1:
        matched = False
        for i, p2 in enumerate(parts2):
            if not used[i] and is_equiv(p1, p2):
                used[i] = True
                matched = True
                break
        if not matched:
            return False
    return True


# ──────────────────────────────────────────────────────────────
# 原版兼容层：normalize_answer（保留，供外部代码使用）
# ──────────────────────────────────────────────────────────────

def normalize_answer(s: str) -> str:
    """
    原版字符串规范化（小写、去标点、去冠词、去多余空白）。
    作为最后兜底层使用。
    """
    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(_string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    return white_space_fix(remove_articles(remove_punc(s.lower())))


# ──────────────────────────────────────────────────────────────
# 主接口
# ──────────────────────────────────────────────────────────────

def is_equiv(str1, str2, verbose=False) -> bool:
    """
    判断两个数学答案字符串是否等价。

    层次：
      1. 预处理（\\text 提取、\\! 千位分隔符）
      2. _strip_string 规范化后字符串完全相等
      3. 列表/集合顺序无关比较
      4. sympy 符号/数值等价
      5. 兜底：原始字符串相等
    """
    if str1 is None and str2 is None:
        return True
    if str1 is None or str2 is None:
        return False

    try:
        def preprocess(s):
            s = _extract_text_content(s)
            s = _remove_numeric_separators(s)
            return s

        str1 = preprocess(str1)
        str2 = preprocess(str2)

        ss1 = _strip_string(str1)
        ss2 = _strip_string(str2)

        if verbose:
            print(f"  stripped: '{ss1}'  vs  '{ss2}'")

        # 1. 规范化后字符串完全相等
        if ss1 == ss2:
            return True

        # 2. 列表/集合顺序无关比较
        if _is_list_string(ss1) or _is_list_string(ss2):
            if _list_equiv(ss1, ss2):
                return True

        # 3. sympy 符号/数值等价
        sympy_result = _try_sympy_equiv(ss1, ss2)
        if sympy_result is True:
            return True
        if sympy_result is False:
            return False

        # 4. normalize_answer 兜底（冠词、标点差异等非数学文本场景）
        if normalize_answer(str1) == normalize_answer(str2):
            return True

        # 5. 最终兜底：原始字符串相等
        return str1 == str2

    except Exception:
        return str1 == str2


def EM(answer: str, key: str) -> bool:
    """
    对外主接口，保持与原版签名兼容。
    直接委托给 is_equiv。
    """
    return is_equiv(answer, key)

def save_trajectories_log(path: str, log: str = None, dicts: list = None, true_log: str = None, save_log: bool = True, save_dict: bool = True, save_true_log: bool = True, run_name: str = 'run', log_mode: str = 'a') -> None:
    """
    Saves the log and the dict to the path.
    
    Args:
        path: The path to save the log and the dictionaries.
        log: The log to be saved.
        dicts: The dict to be saved.
        true_log: The true log to be saved.
        save_log: Whether to save the log.
        save_dict: Whether to save the dictionaries.
        save_true_log: Whether to save the true log.
        run_name: The name of the run.
    """
    if save_log:
        with open(f'{path}\\{run_name}.txt', log_mode, encoding='utf-8') as f:
            f.write(log)
    if save_dict:
        with open(f'{path}\\{run_name}.pkl', 'wb') as f:
            pickle.dump(dicts, f)
    if save_true_log:
        with open(f'{path}\\{run_name}_true.txt', 'w', encoding='utf-8') as f:
            f.write(true_log)

def load_trajectories_log(path: str, load_log: bool = True, load_dict: bool = True, load_true_log: bool = False, run_name: str = 'run') -> Dict[str, Any]:
    """
    Loads the log and the dict from the path.
    
    Args:
        path: The path to load the logs and the dictionaries.
        load_log: Whether to load the log.
        load_dict: Whether to load the dictionaries.
        load_true_log: Whether to load the true log.
        run_name: The name of the run.
    
    Returns:
        A dictionary containing the logs and the dict.
    """
    out = dict()
    if load_log:
        with open(f'{path}\\{run_name}.txt', 'r', encoding='utf-8') as f:
            out['log'] = f.read()
    if load_dict:
        try:
            with open(f'{path}\\{run_name}.pkl', 'rb') as f:
                out['dicts'] = pickle.load(f)
        except (EOFError, pickle.UnpicklingError, FileNotFoundError) as e:
            print(f'Warning: Corrupted or missing pickle file. Starting with empty data. Error: {e}')
            out['dicts'] = []
    if load_true_log:
        with open(f'{path}\\{run_name}_true.txt', 'r', encoding='utf-8') as f:
            out['true_log'] = f.read()
        
    return out

def parse_log(log_path: str):
    with open(log_path, 'r', encoding='utf-8') as f:
        text = f.read()

    blocks = re.split(r'#######################################', text)
    tasks = {}

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 提取任务编号和反思轮次
        m = re.search(r'TASK (\d+) Reflection (\d+)', block)
        if not m:
            continue
        task_id = int(m.group(1))
        ref_round = int(m.group(2))

        # ----- 修改开始：取最后一个 Question，并从其后找第一个 Thought/Action -----
        # 找到所有 Question
        q_matches = list(re.finditer(r'Question:\s*(.+?)(?=\nThought|\nAction|$)', block, re.DOTALL))
        if q_matches:
            last_q = q_matches[-1]
            question = last_q.group(1).strip()
            # 从最后一个 Question 结束位置开始截取剩余文本
            remaining = block[last_q.end():]
            lines_remaining = remaining.split('\n')
            start_idx = None
            for i, line in enumerate(lines_remaining):
                if re.match(r'^(?i)thought(?:\s+\d+)?:', line) or re.match(r'^(?i)action(?:\s+\d+)?:', line):
                    start_idx = i
                    break
            if start_idx is not None:
                trajectory_text = '\n'.join(lines_remaining[start_idx:])
            else:
                trajectory_text = ''
        else:
            # 没有 Question，使用原逻辑（从块开头找第一个 Thought/Action）
            question = None
            lines = block.split('\n')
            start_idx = None
            for i, line in enumerate(lines):
                if re.match(r'^(?i)thought(?:\s+\d+)?:', line) or re.match(r'^(?i)action(?:\s+\d+)?:', line):
                    start_idx = i
                    break
            if start_idx is not None:
                trajectory_text = '\n'.join(lines[start_idx:])
            else:
                trajectory_text = ''
        # ----- 修改结束 -----

        # 判断本轮结果（仍然基于整个 block）
        if 'Answer is CORRECT' in block:
            result = 'CORRECT'
        elif 'Answer is INCORRECT' in block:
            result = 'INCORRECT'
        else:
            result = None

        # 存入 tasks
        if task_id not in tasks:
            tasks[task_id] = {'reflections': []}
        tasks[task_id]['reflections'].append({
            'round': ref_round,
            'question': "Question: " + question,
            'trajectory': trajectory_text,
            'result': result,
            # 如果需要 model_answer 可以再提取，但此处未使用
        })

    return tasks

def get_last_completed_task_from_log(log_text: str) -> int:
    '''从log文件中解析最后一个完成的任务编号。'''
    pattern = r'TASK (\d+) Reflection 0'
    matches = re.findall(pattern, log_text)
    if not matches:
        return -1
    return int(matches[-1])


def format_math2code_log(s: str) -> str:
    """Insert newlines before Observation/Action/Thought blocks for readable math2code_math logs."""
    for pat in [r'Observation\s*\d+\s*:', r'Action\s*\d+\s*:', r'Thought\s*\d+\s*:']:
        s = re.sub(r'(?<!\n)(?=' + pat + r')', '\n', s)
    return s


def split_logs_by_task(text: str, num_tasks: int) -> List[List[str]]:
    """
    Splits the log text by task.
    
    Args:
        text: The log text.
        num_tasks: The number of tasks.
        
    Returns:
        A list of lists of log texts, each list corresponding to a task.
    """
    remaining_text = text
    parsed_result = []
    for task_i in range(num_tasks+1):
        if task_i == num_tasks:
            pattern_i = r'########################################\nEND TRIAL'
        else:
            pattern_i = rf'#######################################\n.*TASK {str(task_i)} '
        matches_i = re.split(pattern_i, remaining_text)
        remaining_text = matches_i[-1]
        parsed_result.append(matches_i[1:-1])
        if task_i != 0:
            parsed_result[task_i-1].append(matches_i[0])

    # remove the last empty list
    parsed_result.pop()

    return parsed_result

def recompute_stats(parsed_result: List[List[str]], benchmark: str, trial: int = -1) -> Dict[str, int]:
    """
    Recomputes the stats from the parsed log text.
    
    Args:
        parsed_result: The parsed log text.
        benchmark: The benchmark name.
        trial: The number of trials.
        
    Returns:
        The stats for the given benchmark.
    """
    stats = {"success": 0, "fail": 0, "halted": 0} if benchmark != 'alfworld' else {"success": 0, "fail": 0}

    for task_i in range(len(parsed_result)):
        trajectories = parsed_result[task_i]
        last_trajectory = trajectories[min(trial, len(trajectories) - 1)].strip()
        last_step = last_trajectory.split('\n')[-1]

        if benchmark in ['hotpotqa', 'math2code_math', 'physics2code_physics', 'chemistry2code_chemistry', 'code2math_code']:
            if ' CORRECT' in last_step or 'Answer is correct.' in last_step:
                stats["success"] += 1
            elif 'INCORRECT' in last_step or 'Answer is incorrect.' in last_step:
                stats["fail"] += 1
            else:
                stats["halted"] += 1
        elif benchmark == 'alfworld':
            if 'SOLVED' in last_step:
                stats["success"] += 1
            else:
                stats["fail"] += 1
        elif benchmark == 'webshop':
            if ': 1.0' in last_step or 'Your score' in last_step:
                stats["success"] += 1
            else:
                stats["halted"] += 1
        elif benchmark == 'fever':
            if 'reward = 1' in last_step:
                stats["success"] += 1
            elif 'reward = 0' in last_step:
                stats["fail"] += 1
            else:
                stats["halted"] += 1
        else:
            raise NotImplementedError(f'recompute_stats for {benchmark} not implemented')
        
    return stats

def plot_trial_stats(parsed_result: List[List[str]], benchmark: str, max_trials: int = 4, save_path: str = None) -> Dict[str, List[int]]:
    """
    Plots the stats from the parsed log text.
    
    Args:
        parsed_result: The parsed log text.
        benchmark: The benchmark name.
        max_trials: The number of trials.
        save_path: The path to save the figure.
        
    Returns:
        The stats for the given benchmark.
    """
    results = dict()
    colors = {'success': 'green', 'fail': 'red', 'halted': 'orange'}

    for i in range(max_trials):
        stats = recompute_stats(parsed_result, benchmark, i)
        for key, value in stats.items():
            results[key] = results.get(key, []) + [value]

    if benchmark == 'alfworld':
        assert len(parsed_result) == 134
        results = {k: [round(x / 134 * 100, 2) for x in v] for k, v in results.items()}
    else:
        num_tasks = len(parsed_result)
        if num_tasks == 100:
            results = {k: [round(x / 100 * 100, 2) for x in v] for k, v in results.items()}
        # math2code / math2code_math: keep raw counts

    for i, (key, value) in enumerate(results.items()):
        plt.plot(value, label=key, marker='o', color=colors[key])

    # annotate all points with their values next to them
    for i in range(max_trials):
        for key, value in results.items():
            plt.annotate(value[i], (i, value[i]), textcoords="offset points", xytext=(0,10), ha='center')

    plt.legend(loc='best')
    plt.xlabel("Reflection numbers")
    plt.ylabel("Task SR %")
    plt.xticks(range(max_trials))
    plt.show()
    if save_path:
        plt.savefig(save_path)
    
    return results


def print_and_plot_progress_stats(
    success: int,
    fail: int,
    halted: int,
    save_path: str,
    run_name: str = "",
    total_tasks: int = None,
) -> None:
    """Print cumulative success/fail/halted counts and save a progress chart locally."""
    completed = success + fail + halted
    if completed == 0:
        return

    total_str = f" / {total_tasks}" if total_tasks else ""
    header = f"[Progress Report] {run_name} — {completed}{total_str} tasks completed"
    summary = (
        f"\n{'=' * 60}\n"
        f"{header}\n"
        f"  Success : {success:>4}  ({success / completed * 100:.1f}%)\n"
        f"  Fail    : {fail:>4}  ({fail / completed * 100:.1f}%)\n"
        f"  Halted  : {halted:>4}  ({halted / completed * 100:.1f}%)\n"
        f"  Total   : {completed:>4}\n"
        f"{'=' * 60}"
    )
    print(summary, flush=True)

    labels = ['Success', 'Fail', 'Halted']
    values = [success, fail, halted]
    colors = ['#2ecc71', '#e74c3c', '#f39c12']

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    bars = axes[0].bar(labels, values, color=colors)
    axes[0].set_title(f'Task Outcomes ({completed} completed)')
    axes[0].set_ylabel('Count')
    for bar, val in zip(bars, values):
        if val > 0:
            axes[0].text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(val),
                ha='center',
                va='bottom',
            )

    non_zero = [(label, val, color) for label, val, color in zip(labels, values, colors) if val > 0]
    if non_zero:
        axes[1].pie(
            [item[1] for item in non_zero],
            labels=[item[0] for item in non_zero],
            colors=[item[2] for item in non_zero],
            autopct='%1.1f%%',
            startangle=90,
        )
    axes[1].set_title('Distribution')

    fig.suptitle(header, fontsize=11)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"[Progress Report] Chart saved to: {save_path}", flush=True)


def get_env_name_from_gamefile(gamefile: str) -> Union[str, None]:
    """
    Gets the environment name from the gamefile for ALFWorld.

    Args:
        gamefile: The gamefile.

    Returns:
        The environment name.
    """
    for k in ENV_NAMES:
        if k in gamefile:
            return k

def get_env_name_from_task(task: str, benchmark: str) -> Union[str, None]:
    """
    Gets the environment name from the task instruction for ALFWorld.

    Args:
        task: The task.
        benchmark: The benchmark name.

    Returns:
        The environment name.
    """
    if benchmark == 'alfworld':
        for k, v in TASK_ENV_NAMES:
            if k in task:
                return v
    else:
        return benchmark

def alfworld_results_per_env_name(agent: Dict[str, Any]) -> Dict[str, int]:
    """
    Computes the results per environment name for ALFWorld from agent dict.
    
    Args:
        agent: The agent dictionary.
        
    Returns:
        The results per environment name.
    """
    tasks = agent['tasks']
    succeeded_trial_history = agent['succeeded_trial_history']
    failed_trial_history = agent['failed_trial_history']
    
    results = {k: 0 for k in ENV_NAMES}
    totals = {k: 0 for k in ENV_NAMES}
    seen = {t['task']: 0 for t in tasks}
    for task in tasks:
        t = task['task']
        env_name = get_env_name_from_gamefile(task['env_kwargs']['gamefile'])
        if len(succeeded_trial_history[t]) > seen[t]:
            results[env_name] += 1
            totals[env_name] += 1
            seen[t] += 1
        elif len(failed_trial_history[t]) > 0:
            totals[env_name] += 1
    
    return {k: round(results[k] / totals[k], 2) if totals[k] != 0 else 0 for k in results.keys()}

def alfworld_results_per_env_name_log(log: str, num_tasks: int, num_trials: int) -> Dict[str, int]:
    """
    Computes the results per environment name for ALFWorld from log text.
    
    Args:
        log: The log text.
        num_tasks: The number of tasks.
        num_trials: The number of trials.
    
    Returns:
        The results per environment name.
    """
    results = {k: [0, 0, 0, 0] for k in ENV_NAMES}
    totals = {k: [0, 0, 0, 0] for k in ENV_NAMES}

    parsed_results = split_logs_by_task(log, num_tasks)
    for i in range(num_trials):
        for task in parsed_results:
            if 'You are in the middle of a room' not in task[i if i < len(task) else -1]:
                continue
            task_desc = re.findall(r'Your task is to: (.*)', task[i if i < len(task) else -1])[0]
            env_name = get_env_name_from_task(task_desc, 'alfworld')
            if env_name is None:
                raise ValueError(f'env_name is None for task {task_desc}')
            if 'SOLVED' in task[i if i < len(task) else -1].strip().split('\n')[-1]:
                results[env_name][i] += 1
            totals[env_name][i] += 1

    assert all([sum([totals[k][i] for k in ENV_NAMES]) == num_tasks for i in range(num_trials)])
    print(totals)
    
    return {k: [round(results[k][i] / totals[k][i], 2) if totals[k][i] != 0 else 0 for i in range(num_trials)] for k in ENV_NAMES}

def get_webshop_mean_score(log: str, num_tasks: int, num_trials: int) -> float:
    """
    Computes the mean score for WebShop from log text.
    
    Args:
        log: The log text.
        num_tasks: The number of tasks.
        num_trials: The number of trials.
    
    Returns:
        The mean score.
    """
    parsed_result = split_logs_by_task(text=log, num_tasks=num_tasks)
    
    assert len(parsed_result) == num_tasks
    return sum([
        max([
            float(parsed_result[k][i].strip().split('\n')[-1].split()[-1] 
                if 'Your score' in parsed_result[k][i].strip().split('\n')[-1] else 0) 
            for i in range(min(len(parsed_result[k]), num_trials))
            ]
        ) for k in range(len(parsed_result))]
    ) / len(parsed_result)

def get_webshop_mean_scores(log: str, num_tasks: int, num_trials: int) -> float:
    """
    Computes the mean scores for WebShop from log text.

    Args:
        log: The log text.
        num_tasks: The number of tasks.
        num_trials: The number of trials.
    
    Returns:
        The mean scores.
    """
    return [get_webshop_mean_score(log, num_tasks, i) for i in range(1, num_trials + 1)]

def get_fewshot_max_tokens(benchmark: str) -> int:
    """
    Gets the maximum number of tokens in the fewshot tasks for the given benchmark.
    
    Args:
        benchmark: The benchmark name.
    
    Returns:
        The maximum number of tokens.
    """
    fewshots = FEWSHOTS[benchmark]
    if isinstance(fewshots, dict):
        return max([max([token_counter(f) for f in fs]) for fs in fewshots.values()])
    elif isinstance(fewshots, list):
        return max([token_counter(f) for f in fewshots])

def get_split_eval_idx_list(agent_dict: Dict[str, Any], n_folds: int) -> List[List[int]]:
    """
    Gets the split evaluation index list.
    
    Args:
        agent_dict: The agent dictionary.
        n_folds: The number of folds.
    
    Returns:
        The split evaluation index list.
    """
    # For eval-only runs (or when explicitly set), a single fold means "evaluate all tasks".
    # The no-overlap invariant is trivially satisfied for 1 fold.
    if n_folds <= 1:
        return [list(range(len(agent_dict.get('tasks', []))))]

    eval_idx_list = [[] for _ in range(n_folds)]
    env_names = set(x['env_name'] for x in agent_dict['tasks'])
    task2idx = agent_dict['task2idx']

    # compare success/failure
    compare_dict = {env_name: [] for env_name in env_names}
    success_dict = {env_name: [] for env_name in env_names}
    fail_dict = {env_name: [] for env_name in env_names}
    for task, trials in agent_dict['succeeded_trial_history'].items():
        # 检查键是否存在
        if task not in agent_dict['failed_trial_history']:
            agent_dict['failed_trial_history'][task] = []
        
        if len(trials) > 0:
            if len(agent_dict['failed_trial_history'][task]) > 0:
                compare_dict[get_env_name_from_task(task, agent_dict['benchmark_name'])].append(task2idx[task])
            else:
                success_dict[get_env_name_from_task(task, agent_dict['benchmark_name'])].append(task2idx[task])
        else:
            # 只有在有失败试验时才添加到fail_dict
            if len(agent_dict['failed_trial_history'][task]) > 0:
                fail_dict[get_env_name_from_task(task, agent_dict['benchmark_name'])].append(task2idx[task])
            # 如果既没有成功也没有失败，跳过这个任务
            else:
                print(f'task {task} has no failed trials')
                continue

    # split into n_folds
    j = 0
    for idx_list in list(compare_dict.values()) + list(success_dict.values()) + list(fail_dict.values()):
        random.shuffle(idx_list)
        for idx in idx_list:
            eval_idx_list[j % n_folds].append(idx)
            j += 1
    
    # Ensure there are no duplicates across folds.
    flat = [i for fold in eval_idx_list for i in fold]
    assert len(flat) == len(set(flat))
    
    return eval_idx_list

def mode_results(benchmark: str, log: str, num_tasks: int, mode: str) -> Any:
    """
    Computes the statistic results for the given mode.
    
    Args:
        benchmark: The benchmark name.
        log: The log text.
        num_tasks: The number of tasks.
        mode: The mode.
    
    Returns:
        The results.
    """
    parsed_result = split_logs_by_task(text=log, num_tasks=num_tasks)
    if 'react' in mode:
        parsed_result = [x[0] for x in parsed_result]
    elif 'reflection' in mode:
        pattern = r'reflection(\d+)'
        res = re.findall(pattern, mode)
        if len(res) > 0:
            i = int(res[0])
        else:
            pattern = r'(\d+)reflection'
            res = re.findall(pattern, mode)
            if len(res) > 0:
                i = int(res[0])
            else:
                i = 0
        parsed_result = [x[i if i < len(x) else -1] for x in parsed_result]

    if 'token' in mode:
        f_trial = token_counter
    elif 'count' in mode:
        f_trial = lambda x: 1
    else:
        raise NotImplementedError(f'mode must contain token or count')

    invalid = None
    if 'invalid' in mode:
        if benchmark == 'alfworld':
            invalid = 'nothing happens'
        elif benchmark == 'webshop':
            invalid = 'invalid action' 
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'physics2code_physics', 'chemistry2code_chemistry', 'code2math_code']:
            invalid = 'invalid action'
        mode += 'observation'

    if 'thought' in mode:
        if benchmark == 'webshop':
            lambda_filter = lambda y: y.strip().startswith('Action: think[')
        elif benchmark == 'alfworld':
            lambda_filter = lambda y: y.strip().startswith('> think:')
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'physics2code_physics', 'chemistry2code_chemistry', 'code2math_code']:
            lambda_filter = lambda y: y.strip().startswith('Thought')
        else:
            raise NotImplementedError(f'benchmark {benchmark} not implemented')
    elif 'action' in mode:
        if benchmark == 'webshop':
            lambda_filter = lambda y: y.strip().startswith('Action: click[') or y.strip().startswith('Action: search[') # valid actions
        elif benchmark == 'alfworld':
            lambda_filter = lambda y: y.strip().startswith('> ') and not y.strip().startswith('> think:') # valid and invalid actions
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'physics2code_physics', 'chemistry2code_chemistry', 'code2math_code']:
            lambda_filter = lambda y: y.strip().startswith('Action')
        else:
            raise NotImplementedError(f'benchmark {benchmark} not implemented')
    elif 'observation' in mode:
        if benchmark == 'webshop':
            lambda_filter = lambda y: y.strip().startswith('Observation:')
        elif benchmark == 'alfworld':
            lambda_filter = lambda y: not y.strip().startswith('> ')
        elif benchmark in ['hotpotqa', 'fever', 'math2code_math', 'physics2code_physics', 'chemistry2code_chemistry', 'code2math_code']:
            lambda_filter = lambda y: y.strip().startswith('Observation')
        else:
            raise NotImplementedError(f'benchmark {benchmark} not implemented')
    else:
        lambda_filter = lambda y: True

    if 'step' in mode:
        if invalid is not None:
            parsed_result = [y for x in parsed_result for y in x.strip().split('\n') if lambda_filter(y) and invalid in y.lower()]
        else:
            parsed_result = [y for x in parsed_result for y in x.strip().split('\n') if lambda_filter(y)]
        
    elif 'traj' in mode:
        if invalid is not None:
            parsed_result = [[y for y in x.strip().split('\n') if lambda_filter(y) and invalid in y.lower()] for x in parsed_result]
        else:
            parsed_result = [[y for y in x.strip().split('\n') if lambda_filter(y)] for x in parsed_result]
        assert len(parsed_result) == num_tasks
    else:
        raise NotImplementedError('mode must contain traj or step')

    if 'sum' in mode:
        f_return = sum
    elif 'mean' in mode:
        f_return = lambda x: sum(x) / len(x) if len(x) > 0 else 0
    elif 'list' in mode:
        f_return = lambda x: x
    else:
        raise NotImplementedError('mode must contain sum, mean or list')
    
    if 'print' in mode:
        print(parsed_result)

    if len(parsed_result) > 0 and isinstance(parsed_result[0], List):
        return f_return([sum([f_trial(trial) for trial in result]) for result in parsed_result])
    
    return f_return([f_trial(trial) for trial in parsed_result])
