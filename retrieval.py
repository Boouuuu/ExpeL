"""
retrieval.py
============
规则检索模块：BM25 关键词检索 + BGE 语义检索 + 加权 RRF 融合。

对外暴露的主要接口：
  - extract_rules_by_type(rule_path)   —— 加载规则文件，初始化缓存（必须先调用）
  - fusion_similar(query, rule_type, max_recall=None)   —— 主检索：BM25 + BGE + wRRF（推荐）
  - semantic_similar(query, rule_type, max_recall=None) —— 纯语义检索
  - keyword_similar(query, rule_type, max_recall=None)  —— 纯关键词检索
"""

import json
import re
import warnings
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================

# ✅ 决策: bge-base-en-v1.5
#   - 规模 < 1000 条，base 精度完全够用，large 的增量收益在小库上不显著
#   - CPU 部署：base ~400MB / 推理约 30ms，large ~1.3GB / 推理约 90ms（CPU 3x 差距）
#   - 精度仍大幅优于 all-MiniLM-L6-v2（MTEB 检索任务 +5~8 分）
#   若未来迁移至 GPU 或库规模超过 5000 条，可改为 'BAAI/bge-large-en-v1.5'
MODEL_NAME = "BAAI/bge-base-en-v1.5"
# BGE 模型需要在查询前加前缀以区分 query 和 passage（训练规范）
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# RRF 平滑系数（通常取 60，值越大对高排名的奖励越平滑）
RRF_K = 60

# ── 加权 RRF 权重（关键词优先策略）────────────────────────────
#
# 关键词权重 > 语义权重的理由：
#   - 规则库为英文专业术语 + 数学公式，精确关键词命中比语义泛化更可靠
#   - BGE 语义模型可能把 "eigenvalue" 泛化到相关但不精确的条目
#   - BM25 对 LaTeX token（\nabla, \frac 等）的精确匹配能力更强
#
# 调整建议：
#   关键词更重要 → 增大 BM25_WEIGHT（如 0.7），减小 SEM_WEIGHT（如 0.3）
#   语义更重要   → 反之
#   两者等重     → 均设为 0.5（退化为标准 RRF）
# ────────────────────────────────────────────────────────────────
BM25_WEIGHT: float = 0.8   # 关键词权重（主导）
SEM_WEIGHT:  float = 0.2   # 语义权重（辅助验证，防止纯关键词碰巧重叠）

# ── 动态召回门控 ────────────────────────────────────────────────
#
# 两道门共同决定召回数量，无需手动指定 top_k：
#
#   门控 1 - BM25 主门槛 BM25_THRESHOLDS（归一化分，值域 [0,1]）：
#       关键词匹配的绝对下界。
#       含义：候选的 BM25 分必须达到当次最高 BM25 分的一定比例。
#       参考值（归一化后）：
#         >= 0.40  关键词强命中（多个核心词精确匹配）
#         0.20~0.40  部分命中（1~2 个关键词匹配）
#         < 0.20  关键词几乎未命中，即使语义相关也不要
#
#   门控 2 - 语义兜底门槛 SEM_THRESHOLDS（BGE 余弦，值域 [0,1]）：
#       防止"关键词碰巧重叠但语义完全错误"的误召回。
#       设得比原来低，只做兜底过滤，不做主筛选。
#       BGE-base 参考值：< 0.35 基本不相关。
#
#   门控 3 - 加权 RRF 相对衰减 RRF_DROP_RATIO：
#       只保留加权 RRF 分不低于「最高分 * (1 - DROP_RATIO)」的结果。
# ────────────────────────────────────────────────────────────────
BM25_THRESHOLDS = {
    "THINKING":  0.5,   # BM25 归一化主门槛
    "METHOD":    0.5,
    "TECHNIQUE": 0.5,
}

SEM_THRESHOLDS = {
    "THINKING":  0.38,   # 语义兜底门槛（比之前低，只做反向过滤）
    "METHOD":    0.5,
    "TECHNIQUE": 0.5,
}

# RRF 相对衰减率（越小越严格，召回越少但噪声越低）
RRF_DROP_RATIO: float = 0.1

# 安全上限：即使全部通过两道门，最多也只召回这么多条（防止极端情况）
MAX_RECALL: int = 3


def reset_rule_retrieval_cache() -> None:
    """切换规则文件前清空缓存，避免混用旧索引（保留已加载的 BGE 模型）。"""
    model = _global_cache.get("model")
    for key in list(_global_cache.keys()):
        if key == "model":
            continue
        if key.endswith("_texts") or key.endswith("_insights") or key.endswith("_corpus"):
            _global_cache[key] = []
        else:
            _global_cache[key] = None
    _global_cache["model"] = model


# 全局缓存
_global_cache: dict = {
    "model": None,
    "thinking_embeddings":  None,
    "thinking_texts":       [],   # insight（同时作为匹配键和返回值）
    "thinking_insights":    [],   # 同 thinking_texts，保持接口统一
    "thinking_bm25":        None,
    "thinking_bm25_corpus": [],
    "method_embeddings":    None,
    "method_texts":         [],   # trigger（匹配键）
    "method_insights":      [],   # trigger: insight（返回值）
    "method_bm25":          None,
    "method_bm25_corpus":   [],
    "technique_embeddings": None,
    "technique_texts":      [],   # trigger（匹配键）
    "technique_insights":   [],   # trigger: insight（返回值）
    "technique_bm25":       None,
    "technique_bm25_corpus":[],
}


# ============================================================
# 1. 文本清洗工具
# ============================================================

def clean_text(text: str) -> str:
    """通用清洗：去除多余空白，保留标点和数学符号结构"""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_latex_tokens(text: str) -> List[str]:
    """
    从 LaTeX 公式中提取有意义的数学 token，用于增强 BM25 关键词匹配。
    例: "$\\nabla f(x)$" → ["nabla", "f", "x"]
         "$$\\frac{a}{b}$$" → ["frac", "a", "b"]
    """
    formulas = re.findall(r'\$\$[^$]+\$\$|\$[^$]+\$', text)
    tokens = []
    for formula in formulas:
        inner = re.sub(r'\$+', '', formula)
        commands = re.findall(r'\\([a-zA-Z]+)', inner)
        tokens.extend(commands)
        identifiers = re.findall(r'\b[a-zA-Z]\b', inner)
        tokens.extend(identifiers)
    return tokens


def tokenize_for_bm25(text: str) -> List[str]:
    """
    BM25 分词：
    1. 去掉 LaTeX 公式主体（避免 $ 符号污染），但先提取其中的 token
    2. 英文按空格+标点分词
    3. 过滤长度 < 2 的 token
    """
    latex_tokens = extract_latex_tokens(text)
    text_no_latex = re.sub(r'\$\$[^$]+\$\$|\$[^$]+\$', ' ', text)
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-']*[a-zA-Z0-9]|[a-zA-Z0-9]", text_no_latex)
    words = [w.lower() for w in words if len(w) >= 2]
    all_tokens = words + [t.lower() for t in latex_tokens if len(t) >= 2]
    return all_tokens


# ============================================================
# 2. BGE 嵌入模型
# ============================================================

def init_bge_model() -> SentenceTransformer:
    """
    初始化 BGE-base-en-v1.5（约 400MB）。
    CPU 单次推理约 30ms，< 1000 条库首次全量 encode 约 15-30s，后续全部走缓存。
    """
    if _global_cache["model"] is None:
        print(f"🔧 初始化 BGE 模型: {MODEL_NAME}（首次下载较大，后续复用）...")
        _global_cache["model"] = SentenceTransformer(MODEL_NAME, device='cpu')
    return _global_cache["model"]


def embed_passages(texts: Union[str, List[str]]) -> np.ndarray:
    """
    对知识库规则（passages）做嵌入，去掉 LaTeX 主体后编码。
    BGE passage 侧不加前缀。
    """
    model = init_bge_model()
    if isinstance(texts, str):
        texts = [texts]
    clean = [re.sub(r'\$\$[^$]+\$\$|\$[^$]+\$', '', t).strip() for t in texts if t.strip()]
    if not clean:
        return np.array([])
    return model.encode(clean, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)


def embed_query(query_text: str) -> np.ndarray:
    """
    对查询文本做嵌入。
    ✅ BGE 规范：query 侧需加前缀，passage 侧不加。
    """
    model = init_bge_model()
    clean = re.sub(r'\$\$[^$]+\$\$|\$[^$]+\$', '', query_text).strip()
    if not clean:
        return np.array([])
    prefixed = BGE_QUERY_PREFIX + clean
    return model.encode([prefixed], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)


# ============================================================
# 3. BM25 索引构建
# ============================================================

def build_bm25_index(texts: List[str]) -> Tuple[BM25Okapi, List[List[str]]]:
    """
    对规则文本列表构建 BM25 索引。
    含 LaTeX token 增强：数学符号也参与 BM25 匹配。
    """
    corpus = [tokenize_for_bm25(t) for t in texts]
    bm25 = BM25Okapi(corpus)
    return bm25, corpus


def bm25_scores(bm25: BM25Okapi, query_text: str) -> np.ndarray:
    """
    计算 query 对全部规则的 BM25 分数（已归一化到 [0,1]）。
    """
    query_tokens = tokenize_for_bm25(query_text)
    if not query_tokens:
        return np.zeros(len(bm25.doc_len))
    raw_scores = bm25.get_scores(query_tokens)
    max_score = raw_scores.max()
    if max_score > 0:
        raw_scores = raw_scores / max_score
    return raw_scores


# ============================================================
# 4. RRF 融合
# ============================================================

def reciprocal_rank_fusion(
    score_arrays: List[np.ndarray],
    weights: List[float],
    k: int = RRF_K,
) -> np.ndarray:
    """
    加权倒数排名融合（Weighted RRF）。

    公式: wRRF(d) = Σ  weight_i / (k + rank_i(d))

    参数:
        score_arrays: 每路检索的分数数组列表，顺序为 [bm25_scores, sem_scores]
        weights:      对应每路的权重，顺序需与 score_arrays 一致
        k:            平滑系数，默认 60
    """
    assert len(score_arrays) == len(weights), "score_arrays 和 weights 长度必须一致"
    n = len(score_arrays[0])
    fused = np.zeros(n)
    for scores, w in zip(score_arrays, weights):
        ranking = np.argsort(scores)[::-1]
        rank_of = np.empty(n, dtype=int)
        rank_of[ranking] = np.arange(n)
        fused += w / (k + rank_of + 1)
    return fused


# ============================================================
# 5. 规则加载 & 缓存初始化
# ============================================================

def extract_rules_by_type(rule_path: str) -> Tuple[List[str], List[str], List[str]]:
    """
    加载 JSON 规则文件，分类提取，并初始化 BGE 嵌入缓存 + BM25 索引。

    匹配键 vs 返回值的区别：
      THINKING  : 匹配键 = insight，返回值 = insight（trigger 不存在）
      METHOD    : 匹配键 = trigger，否则 insight；返回值 = insight
      TECHNIQUE : 同 METHOD

    返回:
      (thinking_texts, method_texts, technique_texts)
    """
    if not Path(rule_path).exists():
        raise FileNotFoundError(f"规则文件不存在：{rule_path}")

    with open(rule_path, 'r', encoding='utf-8') as f:
        rules_data = json.load(f)

    reset_rule_retrieval_cache()

    thinking_texts,  thinking_insights  = [], []
    method_texts,    method_insights    = [], []
    technique_texts, technique_insights = [], []

    for item in rules_data:
        r_type  = item.get('type', '').upper()
        insight = item.get('insight', '').strip()
        if not insight:
            continue

        trigger = str(item.get('trigger', '') or '').strip()
        if not trigger:
            trigger = insight

        if r_type == 'THINKING':
            thinking_texts.append(insight)
            thinking_insights.append(insight)
        elif r_type == 'METHOD':
            method_texts.append(trigger.strip())
            method_insights.append(f"{trigger}: {insight}")
        elif r_type == 'TECHNIQUE':
            technique_texts.append(trigger.strip())
            technique_insights.append(f"{trigger}: {insight}")

    print(f"\n📊 加载规则: THINKING({len(thinking_texts)}) | METHOD({len(method_texts)}) | TECHNIQUE({len(technique_texts)})")

    for rtype, texts, insights in [
        ("thinking",  thinking_texts,  thinking_insights),
        ("method",    method_texts,    method_insights),
        ("technique", technique_texts, technique_insights),
    ]:
        print(f"  → 构建 {rtype} 嵌入 + BM25 索引（匹配键示例: {texts[0][:60] if texts else 'N/A'}）...")
        if not texts:
            _global_cache[f"{rtype}_embeddings"] = np.array([])
            _global_cache[f"{rtype}_texts"] = []
            _global_cache[f"{rtype}_insights"] = []
            _global_cache[f"{rtype}_bm25"] = None
            _global_cache[f"{rtype}_bm25_corpus"] = []
            continue
        _global_cache[f"{rtype}_embeddings"]  = embed_passages(texts)
        _global_cache[f"{rtype}_texts"]       = texts
        _global_cache[f"{rtype}_insights"]    = insights
        bm25_idx, corpus = build_bm25_index(texts)
        _global_cache[f"{rtype}_bm25"]        = bm25_idx
        _global_cache[f"{rtype}_bm25_corpus"] = corpus

    print("✅ 缓存初始化完成")
    return thinking_texts, method_texts, technique_texts


# ============================================================
# 6. 内部辅助：缓存读取
# ============================================================

def _get_cache(rule_type: str):
    """
    取出对应类型的缓存，返回四元组：
      (embeddings, texts, insights, bm25)
      - texts   : 相似度计算用的文本（METHOD/TECHNIQUE 为 problem_type）
      - insights: 最终返回给调用方的文本（始终为 insight）
    """
    key = rule_type.lower()
    return (
        _global_cache.get(f"{key}_embeddings", np.array([])),
        _global_cache.get(f"{key}_texts",    []),
        _global_cache.get(f"{key}_insights", []),
        _global_cache.get(f"{key}_bm25",     None),
    )


# ============================================================
# 7. 核心检索函数（对外接口）
# ============================================================

def fusion_similar(query_text: str, rule_type: str = "METHOD", max_recall: int = None) -> str:
    """
    主检索函数（关键词优先 + 动态召回版）：
    BM25 关键词检索（主） + BGE 语义检索（辅） → 加权 RRF 融合 → 三重门控动态截断

    召回逻辑（三道门依次过滤）：
      门控 1 - BM25 主门槛（BM25_THRESHOLDS）：关键词归一化分的绝对下界
      门控 2 - 语义兜底门槛（SEM_THRESHOLDS）：防止关键词碰巧重叠但语义错误的误召回
      门控 3 - 加权 RRF 相对衰减（RRF_DROP_RATIO）：只保留最高分附近的结果

    参数:
      query_text: 查询文本
      rule_type:  "THINKING" | "METHOD" | "TECHNIQUE"

    返回:
      召回的 insight 列表拼接成的字符串，未命中则返回 ""
    """
    rule_type = rule_type.upper()
    cap = max_recall if max_recall is not None else MAX_RECALL
    if rule_type not in BM25_THRESHOLDS or not query_text.strip():
        print("❌ 参数错误：规则类型仅支持 THINKING/METHOD/TECHNIQUE，且查询文本不能为空")
        return ""

    rule_emb, rule_texts, rule_insights, bm25_idx = _get_cache(rule_type)
    if len(rule_emb) == 0 or not rule_texts or bm25_idx is None:
        print(f"❌ 无 {rule_type.lower()} 类型的规则数据")
        return ""

    bm25_sims = bm25_scores(bm25_idx, query_text)

    query_emb = embed_query(query_text)
    if len(query_emb) == 0:
        print("❌ 查询文本清洗后为空，无法匹配")
        return ""
    sem_sims = util.cos_sim(query_emb, rule_emb).numpy()[0]

    fused_sims = reciprocal_rank_fusion(
        [bm25_sims, sem_sims],
        weights=[BM25_WEIGHT, SEM_WEIGHT],
    )

    bm25_threshold = BM25_THRESHOLDS[rule_type]
    sem_threshold  = SEM_THRESHOLDS[rule_type]
    rrf_cutoff     = float(fused_sims.max()) * (1.0 - RRF_DROP_RATIO)

    sorted_indices = np.argsort(fused_sims)[::-1]
    print_content, return_content = [], []

    for idx in sorted_indices:
        rrf_score  = float(fused_sims[idx])
        bm25_score = float(bm25_sims[idx])
        sem_score  = float(sem_sims[idx])

        if rrf_score < rrf_cutoff:
            break
        if bm25_score < bm25_threshold:
            continue
        if sem_score < sem_threshold:
            continue

        rank        = len(return_content) + 1
        match_key   = rule_texts[idx]
        insight_val = rule_insights[idx]
        print_content.append(
            f"{rank}. [matched: {match_key}]\n"
            f"   → {insight_val}\n"
            f"   关键词(BM25): {round(bm25_score, 3)}"
            f"  |  语义(BGE): {round(sem_score, 3)}"
            f"  |  加权RRF: {round(rrf_score, 4)}"
        )
        return_content.append(f"{rank}. {insight_val}")

        if len(return_content) >= cap:
            break

    if return_content:
        print(f"\n{rule_type} Rules — 动态召回 {len(return_content)} 条 (BM25主导+BGE辅助+wRRF):\n")
        print("\n".join(print_content))
        return "\n".join(return_content)
    else:
        if not rule_texts:
            print("❌ 未找到相关规则（规则库为空）")
            return ""
        best_bm25 = round(float(bm25_sims[sorted_indices[0]]), 3)
        best_sem  = round(float(sem_sims[sorted_indices[0]]), 3)
        best_rrf  = round(float(fused_sims[sorted_indices[0]]), 4)
        best_key  = rule_texts[sorted_indices[0]]
        print(
            f"❌ 未找到相关规则\n"
            f"   最优候选: [{best_key}] BM25={best_bm25}(门槛={bm25_threshold})"
            f" | 语义={best_sem}(门槛={sem_threshold})"
            f" | wRRF={best_rrf}(截断={round(rrf_cutoff,4)})"
        )
        return ""


def semantic_similar(query_text: str, rule_type: str = "METHOD", max_recall: int = None) -> str:
    """
    纯语义检索（动态召回版）。
    门控：语义硬门槛 + 相对衰减（与 fusion_similar 策略一致）。

    参数:
      query_text: 查询文本
      rule_type:  "THINKING" | "METHOD" | "TECHNIQUE"

    返回:
      召回的 insight 列表拼接成的字符串，未命中则返回 ""
    """
    rule_type = rule_type.upper()
    cap = max_recall if max_recall is not None else MAX_RECALL
    if rule_type not in SEM_THRESHOLDS or not query_text.strip():
        print("❌ 参数错误")
        return ""

    rule_emb, rule_texts, rule_insights, _ = _get_cache(rule_type)
    if len(rule_emb) == 0 or not rule_texts:
        print(f"❌ 无 {rule_type.lower()} 类型的规则数据")
        return ""

    query_emb = embed_query(query_text)
    if len(query_emb) == 0:
        return ""

    similarities = util.cos_sim(query_emb, rule_emb).numpy()[0]

    sem_threshold  = SEM_THRESHOLDS[rule_type]
    score_cutoff   = float(similarities.max()) * (1.0 - RRF_DROP_RATIO)
    sorted_indices = np.argsort(similarities)[::-1]

    print_content, return_content = [], []
    for idx in sorted_indices:
        score = float(similarities[idx])
        if score < score_cutoff:
            break
        if score < sem_threshold:
            continue
        rank        = len(return_content) + 1
        match_key   = rule_texts[idx]
        insight_val = rule_insights[idx]
        print_content.append(
            f"{rank}. [matched: {match_key}]\n"
            f"   → {insight_val}\n"
            f"   语义相似度(BGE): {round(score, 3)}"
        )
        return_content.append(f"{rank}. {insight_val}")
        if len(return_content) >= cap:
            break

    if return_content:
        print(f"\n{rule_type} Rules — 动态召回 {len(return_content)} 条:\n")
        print("\n".join(print_content))
        return "\n".join(return_content)
    else:
        if not rule_texts:
            print("❌ 未找到相似规则（规则库为空）")
            return ""
        print(f"❌ 未找到相似规则（最优: [{rule_texts[sorted_indices[0]]}] 语义={round(float(similarities[sorted_indices[0]]), 3)}，门槛={sem_threshold}）")
        return ""


def keyword_similar(query_text: str, rule_type: str = "METHOD", max_recall: int = None) -> str:
    """
    纯关键词检索（动态召回版）。
    BM25 归一化分数硬门槛 + 相对衰减双重门控，与 fusion_similar 策略一致。

    参数:
      query_text: 查询文本
      rule_type:  "THINKING" | "METHOD" | "TECHNIQUE"

    返回:
      召回的 insight 列表拼接成的字符串，未命中则返回 ""
    """
    rule_type = rule_type.upper()
    cap = max_recall if max_recall is not None else MAX_RECALL
    if rule_type not in SEM_THRESHOLDS or not query_text.strip():
        print("❌ 参数错误")
        return ""

    _, rule_texts, rule_insights, bm25_idx = _get_cache(rule_type)
    if not rule_texts or bm25_idx is None:
        print(f"❌ 无 {rule_type.lower()} 类型的规则数据")
        return ""

    scores = bm25_scores(bm25_idx, query_text)

    bm25_threshold = BM25_THRESHOLDS[rule_type]
    score_cutoff   = float(scores.max()) * (1.0 - RRF_DROP_RATIO)
    sorted_indices = np.argsort(scores)[::-1]

    print_content, return_content = [], []
    for idx in sorted_indices:
        score = float(scores[idx])
        if score < score_cutoff:
            break
        if score < bm25_threshold:
            continue
        rank        = len(return_content) + 1
        match_key   = rule_texts[idx]
        insight_val = rule_insights[idx]
        print_content.append(
            f"{rank}. [matched: {match_key}]\n"
            f"   → {insight_val}\n"
            f"   BM25 分数(归一化): {round(score, 3)}"
        )
        return_content.append(f"{rank}. {insight_val}")
        if len(return_content) >= cap:
            break

    if return_content:
        print(f"\nBM25 关键词匹配 — 动态召回 {len(return_content)} 条：")
        print("\n".join(print_content))
        return "\n".join(return_content)
    else:
        if not rule_texts:
            print("❌ 未找到相关规则（规则库为空）")
            return ""
        print(f"❌ 未找到相关规则（最优: [{rule_texts[sorted_indices[0]]}] BM25={round(float(scores[sorted_indices[0]]), 3)}，门槛={bm25_threshold}）")
        return ""

model = init_bge_model()