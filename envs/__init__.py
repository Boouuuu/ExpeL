import joblib
import json
import random
import json

from .base import BaseEnv
from .hotpotqa.hotpotqa import QAEnv
from .fever.fever import FeverEnv
from .alfworld.alfworld import AlfworldEnv
from .webshop.webshop import WebshopEnv
from .math2code.math2code import Math2CodeEnv
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
    math2code=lambda cfg: [
        {
        'task': f'{cfg.benchmark.task_prefix}{row["question"]}',
        'env_kwargs': {
            'question': row['question'],
            'key': row.get('key', ''),
            'test_cases': row.get('test_cases', []),
        },
        'env_name': 'math2code',
    } for row in json.load(open(cfg.benchmark.task_file, "r"))],
)

ENVS = dict(hotpotqa=QAEnv, fever=FeverEnv, alfworld=AlfworldEnv, webshop=WebshopEnv, math2code=Math2CodeEnv)
