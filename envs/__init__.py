import joblib
import json
import random
import json

from .base import BaseEnv
from .hotpotqa.hotpotqa import QAEnv
from .fever.fever import FeverEnv
from .alfworld.alfworld import AlfworldEnv
from .webshop.webshop import WebshopEnv
from .math2code_math.math_train_env import MathTrainEnv
from .code2math_code.code_train_env import CodeTrainEnv
from utils import get_env_name_from_gamefile

# Taken from ReAct Github
idxs = list(range(7405))
random.Random(233).shuffle(idxs)

INIT_TASKS_FN = dict(
    hotpotqa=lambda cfg: [
        {
        'task': f'{cfg.benchmark.task_prefix}{row["question"]}',
        'env_kwargs': {
            'question': row['question'],
            'key': row['answer'],
        },
        'env_name': 'hotpotqa',
    } for _, row in joblib.load(cfg.benchmark.task_file).reset_index(drop=True).iterrows()],
    # 100 tasks for fever
    fever=lambda cfg: [{
        'task': cfg.benchmark.task_prefix + FeverEnv(idx).reset().replace('Claim: ', ''),
        'env_kwargs': {
            'idx': idx,
        },
        'env_name': 'fever',
    } for idx in idxs[:100]],
    alfworld=lambda cfg: [
        {
        'task': f'{cfg.benchmark.task_prefix}{row["goal"]}',
        'env_kwargs': {
            'config': cfg.benchmark,
            "gamefile": row["gamefile"],
        },
        'env_name': get_env_name_from_gamefile(row['gamefile'])
        } for row in json.load(open(cfg.benchmark.task_file, "r"))
    ],
    webshop=lambda cfg: [
        {
        'task': f'{cfg.benchmark.task_prefix}{row["task"]}',
        'env_kwargs': {
            'session_idx': row["session_idx"],
        },
        'env_name': 'webshop'
        } for row in json.load(open(cfg.benchmark.task_file, "r"))
    ],
    math2code_math=lambda cfg: [
        {
        'task': f'{cfg.benchmark.task_prefix}{row["question"]}',
        'env_kwargs': {
            'question': row['question'],
            'key': row['key'],
        },
        'env_name': 'math2code_math',
    } for row in json.load(open(cfg.benchmark.task_file, "r", encoding="utf-8"))],
    math2code=lambda cfg: [
        # math2code now uses HumanEval-style data in JSONL format.
        # Each line is a JSON object with at least: task_id, prompt,
        # entry_point, canonical_solution, test.
        {
        'task': f'{cfg.benchmark.task_prefix}{problem["prompt"]}',
        'env_kwargs': {
            # Pass the full HumanEval problem dict into the env so that it
            # can evaluate Finish[code] using the official tests.
            'problem': problem,
        },
        'env_name': 'math2code',
    }
    for problem in (
        json.loads(line)
        for line in open(cfg.benchmark.task_file, "r", encoding="utf-8")
        if line.strip()
    )],
    code2math_code=lambda cfg: [
        {
        'task': f'{cfg.benchmark.task_prefix}{problem["prompt"]}',
        'env_kwargs': {
            'problem': problem,
        },
        'env_name': 'code2math_code',
    }
    for problem in (
        json.loads(line)
        for line in open(cfg.benchmark.task_file, "r", encoding="utf-8")
        if line.strip()
    )],
)

ENVS = dict(
    hotpotqa=QAEnv,
    fever=FeverEnv,
    alfworld=AlfworldEnv,
    webshop=WebshopEnv,
    math2code_math=MathTrainEnv,
    code2math_code=CodeTrainEnv,
)
