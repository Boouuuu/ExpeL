from typing import Callable, List
import time
import os
import random
import threading

from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
import openai
import requests
import json
import http.client


def _direct_requests_session() -> requests.Session:
    """Bypass system/env HTTP proxy — required for domestic APIs like open.bigmodel.cn."""
    session = requests.Session()
    session.trust_env = False
    return session


def _ts() -> str:
    """心跳打印用的时间戳。"""
    return time.strftime('%H:%M:%S')


def _heartbeat_sleep(seconds: float, msg: str, interval: float = 15.0) -> None:
    """退避/重试等待：打印带时间戳的开始、进度（每 interval 秒）、结束，避免看起来像卡死。"""
    print(f'[{_ts()}] {msg}，等待约 {seconds:.0f}s ...', flush=True)
    end = time.monotonic() + seconds
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))
        remaining = end - time.monotonic()
        if remaining > 0:
            print(f'[{_ts()}] 仍在退避等待，还需约 {remaining:.0f}s', flush=True)
    print(f'[{_ts()}] 等待结束，继续重试。', flush=True)


def _post_with_heartbeat(session, url: str, timeout, heartbeat: float = 15.0, **kwargs) -> requests.Response:
    """发送 POST；请求阻塞期间每 heartbeat 秒打印一次已等待时长（带时间戳）。"""
    start = time.monotonic()
    stop = threading.Event()

    def _beat():
        while not stop.wait(heartbeat):
            print(f'[{_ts()}] 仍在等待 API 响应，已等待 {time.monotonic() - start:.0f}s ...', flush=True)

    t = threading.Thread(target=_beat, daemon=True)
    t.start()
    try:
        response = session.post(url, timeout=timeout, **kwargs)
    finally:
        stop.set()
    print(f'[{_ts()}] 收到 API 响应，本次请求耗时 {time.monotonic() - start:.1f}s', flush=True)
    return response


# 智谱 API Key 池：碰到 429 限流时自动轮换下一个 Key（按需增删）
GLM_API_KEYS = [
    ("jiajia", os.environ.get("BIGMODEL_API_KEY"))
]
_glm_key_idx = 0  # 模块级状态：轮换后后续请求直接使用新 Key，避免反复碰壁


def current_glm_key():
    return GLM_API_KEYS[_glm_key_idx % len(GLM_API_KEYS)]


def advance_glm_key():
    global _glm_key_idx
    _glm_key_idx = (_glm_key_idx + 1) % len(GLM_API_KEYS)


def generate_one_completion(model_name: str, messages: List[dict]) -> str:
    if 'glm' in model_name:
        return generate_glm_completion(messages)
    elif 'qwen' in model_name:
        return generate_qwen_completion(messages)
    elif 'gpt' in model_name:
        return generate_gpt_completion(messages)
    raise ValueError(f"Unsupported model: {model_name}")


def replace_invalid_roles(messages):
    """
    批量替换messages中的非法角色名：
    - human → user（用户角色）
    - ai → assistant（助手/AI角色）
    支持嵌套结构，深拷贝保护原数据
    
    Args:
        messages (list): 原始消息列表，每个元素是含"role"键的字典
    
    Returns:
        list: 替换后的合法消息列表
    """
    import copy
    processed_messages = copy.deepcopy(messages)
    
    # 定义非法角色到合法角色的映射
    role_mapping = {
        "human": "user",    # 人类提问者 → user
        "ai": "assistant"   # AI回复者 → assistant
    }
    
    for msg in processed_messages:
        # 仅处理字典类型且包含role字段的元素
        if isinstance(msg, dict) and "role" in msg:
            # 如果当前role在映射表中，替换为合法值
            if msg["role"] in role_mapping:
                msg["role"] = role_mapping[msg["role"]]
    
    return processed_messages
def generate_qwen_completion(messages):
    openai.api_key = os.environ.get("ALIYUN_API_KEY")
    openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    messages = replace_invalid_roles(messages)
    # 打印messages以便调试
    print("="*20 + " Prompt History " + "="*20)
    for msg in messages:
        print(f"Role: {msg['role']}\nContent:\n{msg['content']}")
    print("="*56)
    completion = openai.ChatCompletion.create(
        model="qwen3-14b",
        messages=messages,
        enable_thinking=False,
        stream=False,
        temperature=0.1,  # 新增：可选，控制回复随机性
        headers={
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        },
        stop=["Observation"]
    )

    # print(f"\n🔹 Generating for task: {task_id}")
    print(f"\n🔹 LLM response: \"{completion.choices[0].message.content}\"")  # 打印完整响应以便调试
    # 修正：直接取属性，而非转JSON字符串（更高效）
    return completion.choices[0].message.content
def generate_guiji_completion5(prompt: str, temperature: float = 0.1) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a student trying to solve math problems. Please follow the instructions provided to solve the [TASK]."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    GUIJI_API_KEY = os.environ.get("GUIJI_API_KEY")
    openai.api_key = GUIJI_API_KEY
    openai.api_base = "https://api.siliconflow.cn/v1"

    # client = OpenAI(
    #     api_key=GUIJI_API_KEY,
    #     base_url="https://api.siliconflow.cn/v1"
    # )
    response = openai.ChatCompletion.create(
        model="Qwen/Qwen3-14B",
        messages=messages,
        temperature=temperature,
        stream=False,
        enable_thinking = False
        # extra_body={"enable_thinking": False}
    )
    return response.choices[0]["message"]["content"]
def generate_glm_completion2(messages):
    openai.api_key = os.environ.get("ALIYUN_API_KEY")
    openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    messages = replace_invalid_roles(messages)
    # 打印messages以便调试
    print("="*20 + " Prompt History " + "="*20)
    for msg in messages:
        print(f"Role: {msg['role']}\nContent:\n{msg['content']}")
    print("="*56)
    model="deepseek-v4.1-flash"
    api_error = None
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            enable_thinking=False,
            # reasoning_effort="low",
            max_completion_tokens = 4096,
            stream=False,
            temperature=0.7,  # 新增：可选，控制回复随机性
            headers={
                "Authorization": f"Bearer {openai.api_key}",
                "Content-Type": "application/json"
            },
            stop=["Observation"]
        )
    except Exception as e:
        api_error = e
        # ---- 详细打印 API 调用错误：异常类型 / HTTP 状态码 / API 错误码 / 错误信息 / 响应体 ----
        print("="*20 + f" API Error [{_ts()}] " + "="*20, flush=True)
        print(f"异常类型: {type(e).__module__}.{type(e).__name__}", flush=True)
        # openai v0 风格的错误对象带有 http_status / code / param 属性
        http_status = getattr(e, 'http_status', None)
        api_code = getattr(e, 'code', None)
        api_param = getattr(e, 'param', None)
        if http_status is not None:
            print(f"HTTP 状态码: {http_status}", flush=True)
        if api_code is not None:
            print(f"API 错误码: {api_code}", flush=True)
        if api_param is not None:
            print(f"API 错误参数: {api_param}", flush=True)
        print(f"错误信息: {e}", flush=True)
        # requests 风格的异常（底层 transport 抛出的情况）
        resp = getattr(e, 'response', None)
        if resp is not None:
            print(f"HTTP 状态码: {getattr(resp, 'status_code', None)}", flush=True)
            try:
                print(f"响应体: {resp.text[:2000]}", flush=True)
            except Exception:
                pass
        # 未知异常类型时补充 traceback，方便定位
        if not isinstance(e, (openai.error.OpenAIError, requests.exceptions.RequestException)):
            import traceback
            traceback.print_exc()
        print("="*56, flush=True)
        return ""  # 返回空串，交由外层 GPTWrapper 按原有逻辑重试

    if api_error is None:
        # print(f"\n🔹 Generating for task: {task_id}")
        print("="*20 + " LLM Response " + "="*20)
        print(f"{completion.choices[0].message.content}")  # 打印完整响应以便调试
        print("="*56)
        # 修正：直接取属性，而非转JSON字符串（更高效）
        return completion.choices[0].message.content
    return ""

def generate_glm_completion(messages):
    messages = replace_invalid_roles(messages)
    print("="*20 + " Prompt History " + "="*20)
    for msg in messages:
        print(f"Role: {msg['role']}\nContent:\n{msg['content']}")
    print("="*56)
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    payload = {
        "model": "glm-5.3",
        "messages": messages,
        "stream": False,
        "temperature": 1,
        "top_p": 0.95,
        # "max_tokens": 4096,
        # "thinking": {"type": "disabled"},
        "reasoning_effort": "low",
        "thinking": {"type": "enabled"},
        "response_format": {"type": "text"},
        "stop": ["Observation"],
    }
    session = _direct_requests_session()
    # 逐个尝试 Key 池：遇到 429 立即切换到下一个 Key，无需等外层退避
    last_err = None
    for _ in range(len(GLM_API_KEYS)):
        key_name, api_key = current_glm_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        time.sleep(0.5)  # Add a delay of 0.5 seconds before the API call
        try:
            attempt = (_glm_key_idx % len(GLM_API_KEYS)) + 1
            print(f'[{_ts()}] 调用 {payload["model"]}（Key="{key_name}"，第 {attempt}/{len(GLM_API_KEYS)} 个），读超时最长 120s ...', flush=True)
            response = _post_with_heartbeat(session, url, timeout=(10, 120), json=payload, headers=headers)
            # 打印状态码与响应体片段（错误看原因，成功留存档便于确认错误码）
            print(f'[{_ts()}] HTTP 状态码: {response.status_code}', flush=True)
            print(f'[{_ts()}] 响应体片段: {response.text[:2000]}', flush=True)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 429:
                detail = ''
                try:
                    detail = e.response.text[:200]
                except Exception:
                    pass
                next_name = GLM_API_KEYS[(_glm_key_idx + 1) % len(GLM_API_KEYS)][0]
                print(f'\n[{_ts()}] [429] Key "{key_name}" 被限流，自动切换到下一个 Key "{next_name}"... detail: {detail}', flush=True)
                advance_glm_key()
                last_err = e
                continue
            raise
        break
    else:
        # 所有 Key 都被限流：抛给外层 GPTWrapper 做指数退避后重来
        print(f'\n[429] 全部 {len(GLM_API_KEYS)} 个 Key 均被限流，交由外层退避重试...')
        raise last_err
    # try:
    #     print("llm response:", response.text)
    # except UnicodeEncodeError:
    #     print("llm response:", response.text.encode('utf-8', errors='replace').decode('utf-8'))

    llm_response = json.loads(response.text)
    content_json_str = llm_response["choices"][0]["message"]["content"]
    try:
        content_data = json.loads(content_json_str)
        if isinstance(content_data, list):
            answer = None
            for item in content_data:
                if isinstance(item, dict) and "answer" in item:
                    answer = item.get("answer")
                    break
            if answer is None:
                answer = content_json_str
        elif isinstance(content_data, dict):
            answer = content_data.get("answer", content_json_str)
        else:
            answer = content_json_str
        return answer.strip() if answer else ""

    except json.JSONDecodeError:
        answer = content_json_str
        return answer.strip() if answer else ""

class GPTWrapper:
    def __init__(self, llm_name: str, openai_api_key: str, long_ver: bool):
        self.model_name = llm_name
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.0,
            openai_api_key=openai_api_key,
        )

    def __call__(self, messages: List[dict], stop: List[str] = [], replace_newline: bool = True) -> str:
        kwargs = {}
        if stop != []:
            kwargs['stop'] = stop
        max_attempts = 10
        for i in range(max_attempts):
            try:
                output = generate_one_completion(self.model_name, messages)
                if output == "":
                    _heartbeat_sleep(2, f'API call failed, retrying {i+1}/{max_attempts}')
                    continue
                output = output.strip('\n').strip()
                break
            except openai.error.RateLimitError:
                _heartbeat_sleep(2, f'Rate limit error, retrying {i+1}/{max_attempts}')
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                if status == 429:
                    # 智谱限流：指数退避 + 随机抖动，避免重试风暴
                    detail = ''
                    try:
                        detail = e.response.text[:200]
                    except Exception:
                        pass
                    wait = min(10 * (2 ** i), 120) + random.uniform(0, 5)
                    retry_after = None
                    if e.response is not None:
                        retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                    print(f'\n[{_ts()}] Rate limited (429), retrying {i+1}/{max_attempts}... detail: {detail}')
                    _heartbeat_sleep(wait, f'退避等待（指数退避 {wait:.1f}s）')
                else:
                    _heartbeat_sleep(3, f'HTTP error ({status}), retrying {i+1}/{max_attempts}')
            except requests.exceptions.RequestException as e:
                print(f'\n[{_ts()}] Network/API error ({type(e).__name__}: {e}), retrying {i+1}/{max_attempts}...')
                _heartbeat_sleep(2, f'网络异常后重试 {i+1}/{max_attempts}')
        else:
            raise RuntimeError(f'Failed to generate response after {max_attempts} attempts')

        if replace_newline:
            output = output.replace('\n', '')
        return output

def LLM_CLS(llm_name: str, openai_api_key: str, long_ver: bool) -> Callable:
    return GPTWrapper(llm_name, openai_api_key, long_ver)

def get_message(messages: List[dict]) -> List[dict]:
    final_messages = []
    # 遍历每个dict消息，转换role和content
    # print(messages)
    for msg in messages:
        # 提取核心属性：msg['role']（角色）、msg['content']（消息内容）
        role_map = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "function": "function"
        }
        # 转换角色名称为OpenAI API标准格式
        role_name = role_map.get(msg.get('role', 'user'), msg.get('role', 'user'))
        message = {
            "role": role_name,
            "content": msg.get('content', ''),
        }
        # 拼接单条消息（格式可自定义，保证上下文清晰即可）
        final_messages.append(message)
    return final_messages

def generate_gpt_completion(messages: List[dict]) -> str:
    conn = http.client.HTTPSConnection("api.chatanywhere.tech")
    messages = get_message(messages)
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": messages
    })
    openai_api_key = os.environ["OPENAI_API_KEY"]
    headers = {
        'Authorization': 'Bearer ' + openai_api_key,
        'Content-Type': 'application/json'
    }
    try:
        conn.request("POST", "/v1/chat/completions", payload, headers)
        res = conn.getresponse()
        data = res.read()
        answer = json.loads(data.decode("utf-8"))
        
        # 检查响应是否包含错误
        if 'error' in answer:
            print(f"\n❌ API Error: {answer['error']}")
            return ""
        
        # 检查响应是否包含choices
        if 'choices' not in answer:
            print(f"\n❌ Unexpected Response Format: {answer}")
            return ""
        
        return answer['choices'][0]['message']['content']
    except KeyError as e:
        # 键错误，打印完整响应以便调试
        print(f"\n❌ KeyError: {str(e)}")
        print(f"Response: {answer if 'answer' in locals() else 'No response'}")
        return ""
    except json.JSONDecodeError as e:
        # JSON解析错误
        print(f"\n❌ JSON Decode Error: {str(e)}")
        print(f"Raw data: {data.decode('utf-8') if 'data' in locals() else 'No data'}")
        return ""
    except Exception as e:
        # 捕获所有其他未预期异常（兜底，防止程序中断）
        print(f"\n❌ Unexpected Error: {str(e)}")
        return ""
