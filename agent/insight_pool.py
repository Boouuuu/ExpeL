"""
JSON insight pool + Verifier 辅助：与 retrieval.extract_rules_by_type / fusion_similar 配合。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from retrieval import extract_rules_by_type, fusion_similar

VALID_TYPES = frozenset({"THINKING", "METHOD", "TECHNIQUE"})
VERIFIER_RECALL = 3


def canonical_insights_pool_path(base_dir: Union[str, Path]) -> Path:
    """固定 insight pool 路径：在 base_dir 下的 insights.json（原地读写，不按 run_name 新建）。"""
    return Path(base_dir) / "insights.json"


def insights_json_path(logging_dir: str, run_name: str = None) -> Path:
    """兼容旧调用：pool 文件统一为 logging_dir 父目录下的 insights.json。"""
    del run_name
    return canonical_insights_pool_path(Path(logging_dir).parent)


def ensure_insights_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def load_pool(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        return []
    return [_normalize_rule_obj(x) for x in data if isinstance(x, dict)]


def save_pool(path: Path, pool: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")

import re

def _fix_bad_escapes(s: str) -> str:
    # 逐对扫描：`\X`（X 为合法转义字符）视为已配对、原样保留（含 LLM 写出的 `\\` 双反斜杠），
    # 只把后面不跟合法转义字符的孤立反斜杠替换成 `\\`。
    # 旧实现按单个反斜杠独立判断，会把合法的 `\\g` 弄成 `\\\g`（非法转义），导致整条 insight 解析失败被静默丢弃。
    return re.sub(
        r'\\["\\/bfnrtu]|\\',
        lambda m: m.group(0) if len(m.group(0)) == 2 else '\\\\',
        s,
    )

def _normalize_rule_obj(obj: Dict[str, Any]) -> Dict[str, str]:
    t = str(obj.get("type", "")).strip().upper()
    if t not in VALID_TYPES:
        t = "TECHNIQUE"
    if t == "THINKING":
        return {
            "type": t,
            "insight": str(obj.get("insight", "") or "").strip(),
        }
    return {
        "type": t,
        "trigger": str(obj.get("trigger", "") or "").strip(),
        "insight": str(obj.get("insight", "") or "").strip(),
    }

def parse_insight_json_objects(llm_text: str) -> List[Dict[str, str]]:
    """从 critique LLM 输出中解析若干条 insight JSON（不要求 ADD/EDIT 前缀）。"""
    llm_text = _fix_bad_escapes(llm_text)
    out: List[Dict[str, str]] = []
    dec = json.JSONDecoder()
    i = 0
    n = len(llm_text)
    while i < n:
        brace = llm_text.find("{", i)
        if brace == -1:
            break
        try:
            obj, end = dec.raw_decode(llm_text, brace)
        except json.JSONDecodeError:
            i = brace + 1
            continue
        i = end
        if isinstance(obj, dict):
            ins = str(obj.get("insight", "") or "").strip()
            t = str(obj.get("type", "")).strip().upper()
            if ins and t in VALID_TYPES:
                out.append(_normalize_rule_obj(obj))
    return out

def pool_to_rule_lines(pool: List[Dict[str, Any]]) -> List[str]:
    """与 Expel 内部 rule_items 对齐：每行一条紧凑 JSON。"""
    return [
        json.dumps(r, ensure_ascii=False, separators=(",", ":"))
        for r in pool
        if r.get("insight")
    ]


def _insight_sig(r: Dict[str, Any]) -> Tuple[str, str, str]:
    return (r.get("type", ""), r.get("trigger", ""), r.get("insight", ""))


def _match_pool_rows_by_fusion_output(
    pool: List[Dict[str, Any]], fusion_text: str, rule_type: str
) -> List[Dict[str, Any]]:
    """将 fusion_similar 返回的 '1. insight' 行映射回完整 JSON 对象。"""
    if not fusion_text.strip():
        return []
    lines = [ln.strip() for ln in fusion_text.splitlines() if ln.strip()]
    hits: List[Dict[str, Any]] = []
    seen = set()
    for ln in lines:
        m = re.match(r"^\d+\.\s*(.+)$", ln)
        insight_line = m.group(1).strip() if m else ln
        for row in pool:
            if row.get("type", "").upper() != rule_type.upper():
                continue
            if row.get("insight", "") in insight_line or insight_line in row.get("insight", ""):
                sig = _insight_sig(row)
                if sig not in seen:
                    seen.add(sig)
                    hits.append(row)
                break
    return hits


def retrieve_similar_insights(
    json_path: str, proposed: Dict[str, Any], max_recall: int = VERIFIER_RECALL
) -> List[Dict[str, Any]]:
    """基于当前磁盘上的见解库检索与 proposed 同类型的相似条目（fusion_similar）。"""
    hits = retrieve_similar_for_proposed_list(json_path, [proposed], max_recall=max_recall)
    print(f"[retrieve_similar_insights] Hits: {len(hits)}")
    print("hits:", hits)
    return hits[0]["retrieved_similar"] if hits else []


def retrieve_similar_for_proposed_list(
    json_path: str,
    proposed_list: List[Dict[str, Any]],
    max_recall: int = VERIFIER_RECALL,
) -> List[Dict[str, Any]]:
    """为每条 candidate 分别做同类型召回，返回 [{proposed, retrieved_similar}, ...]。"""
    path = Path(json_path)
    pool = load_pool(path)
    if pool:
        extract_rules_by_type(str(path))

    results: List[Dict[str, Any]] = []
    for proposed in proposed_list:
        print(f"[retrieve_similar_for_proposed_list] Proposed: {proposed}")
        similar: List[Dict[str, Any]] = []
        same_type = [
            r for r in pool
            if r.get("type", "").upper() == proposed.get("type", "").upper()
        ]
        if same_type:
            if proposed.get("type", "").upper() == "THINKING":
                q = f"{proposed.get('insight', '')}".strip()
            else:
                q = f"{proposed.get('trigger', '')}".strip()
            if q:
                fusion_out = fusion_similar(
                    q, proposed.get("type", "TECHNIQUE"), max_recall=max_recall
                )
                print(f"[retrieve_similar_for_proposed_list] Fusion output:\n{fusion_out}")
                similar = _match_pool_rows_by_fusion_output(
                    pool, fusion_out, proposed.get("type", "TECHNIQUE")
                )
                print(f"[retrieve_similar_for_proposed_list] Retrieved {len(similar)} similar insights.")
                print("Similar insights:", similar)
        results.append({"proposed": proposed, "retrieved_similar": similar})
    print(f"[retrieve_similar_for_proposed_list] {len(proposed_list)} candidates, {sum(len(r['retrieved_similar']) for r in results)} total retrieved.")
    print("Results:", results)
    return results


def _extract_json_object(text: str) -> Optional[dict]:
    text = text.strip()
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        dec = json.JSONDecoder()
        brace = text.find("{")
        if brace == -1:
            return None
        try:
            obj, _ = dec.raw_decode(text, brace)
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None


def parse_verifier_operations(verifier_llm_output: str) -> List[Dict[str, Any]]:
    obj = _extract_json_object(verifier_llm_output)
    if not obj:
        return []
    ops = obj.get("operations")
    if not isinstance(ops, list):
        return []
    cleaned = []
    for o in ops:
        if isinstance(o, dict) and o.get("op"):
            cleaned.append(o)
    return cleaned


def apply_verifier_operations(
    pool: List[Dict[str, Any]], operations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """按顺序应用 verifier 的 JSON 操作（remove → edit → add）。"""
    pool = [dict(x) for x in pool]

    def find_idx_by_insight(target: str) -> int:
        target = (target or "").strip()
        if not target:
            return -1
        for i, r in enumerate(pool):
            if r.get("insight", "") == target:
                return i
        for i, r in enumerate(pool):
            if target in r.get("insight", "") or r.get("insight", "") in target:
                return i
        return -1

    removes = [o for o in operations if str(o.get("op", "")).lower() == "remove"]
    edits = [o for o in operations if str(o.get("op", "")).lower() == "edit"]
    adds = [o for o in operations if str(o.get("op", "")).lower() == "add"]

    for o in removes:
        tgt = o.get("target_insight") or o.get("target") or ""
        j = find_idx_by_insight(str(tgt))
        if j >= 0:
            pool.pop(j)

    for o in edits:
        tgt = o.get("target_insight") or o.get("target") or ""
        rule = o.get("rule")
        if not isinstance(rule, dict):
            continue
        j = find_idx_by_insight(str(tgt))
        if j >= 0:
            pool[j] = _normalize_rule_obj(rule)

    for o in adds:
        rule = o.get("rule")
        if not isinstance(rule, dict):
            continue
        nr = _normalize_rule_obj(rule)
        if not nr.get("insight"):
            continue
        if all(_insight_sig(nr) != _insight_sig(x) for x in pool):
            pool.append(nr)

    return pool


def run_batch_insight_verifier(
    llm_fn: Callable[[List[dict]], str],
    verification_instruction: str,
    retrieval_payload: List[Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]]]:
    """一轮 Verifier 对话处理本批全部 candidate 的 operations。"""
    user = verification_instruction.format(
        new_insights_with_retrieval=json.dumps(
            retrieval_payload, ensure_ascii=False, indent=2
        ),
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert responsible for merging insights into a shared knowledge pool."
            ),
        },
        {"role": "user", "content": user},
    ]
    print(f"\n[Verifier] messages={json.dumps(messages, ensure_ascii=False, indent=2)}\n")
    raw = llm_fn(messages)
    ops = parse_verifier_operations(raw)
    return raw, ops


def merge_pool_with_proposed_batch(
    pool: List[Dict[str, Any]],
    proposed_list: List[Dict[str, Any]],
    json_path: Path,
    llm_fn: Callable[[List[dict]], str],
    verification_instruction: str,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    对本批全部新见解：逐条召回相似项 → 一轮 Verifier → 一次性写回 json_path。
    """
    ensure_insights_file(json_path)
    save_pool(json_path, pool)

    log_piece = ""
    if not proposed_list:
        return pool, log_piece

    retrieval_payload = retrieve_similar_for_proposed_list(
        str(json_path), proposed_list, max_recall=VERIFIER_RECALL
    )
    v_raw, ops = run_batch_insight_verifier(
        llm_fn, verification_instruction, retrieval_payload
    )
    log_piece += (
        f"\n[Verifier batch] candidates={len(proposed_list)}\n{v_raw}\n"
    )

    if not ops:
        for prop in proposed_list:
            nr = _normalize_rule_obj(prop)
            if nr.get("insight") and all(_insight_sig(nr) != _insight_sig(x) for x in pool):
                pool.append(nr)
        log_piece += "[Verifier] no operations parsed; appended all proposed as ADD fallback.\n"
    else:
        pool = apply_verifier_operations(pool, ops)

    save_pool(json_path, pool)
    return pool, log_piece


def merge_pool_with_proposed(
    pool: List[Dict[str, Any]],
    proposed: Dict[str, Any],
    json_path: Path,
    llm_fn: Callable[[List[dict]], str],
    verification_instruction: str,
) -> Tuple[List[Dict[str, Any]], str]:
    """单条兼容入口，内部走 batch 路径。"""
    return merge_pool_with_proposed_batch(
        pool, [proposed], json_path, llm_fn, verification_instruction
    )
