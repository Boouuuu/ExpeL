from typing import Callable, List
import time

from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
import openai


class GPTWrapper:
    def __init__(self, llm_name: str, openai_api_key: str, long_ver: bool):
        self.model_name = llm_name
        self.openai_api_key = openai_api_key
        if long_ver:
            # llm_name = '3.5-turbo-16k'
            llm_name = 'gpt-3.5-turbo'
        self.llm = ChatOpenAI(
            model=llm_name,
            temperature=0.0,
            openai_api_key=openai_api_key,
        )

    def __call__(self, messages: List[ChatMessage], stop: List[str] = [], replace_newline: bool = True) -> str:
        kwargs = {}
        if stop != []:
            kwargs['stop'] = stop
        for i in range(6):
            try:
                # output = self.llm(messages, **kwargs).content.strip('\n').strip()
                output = chatanywhere_llm(messages, self.openai_api_key).strip('\n').strip()
                break
            except openai.error.RateLimitError:
                print(f'\nRetrying {i}...')
                time.sleep(1)
        else:
            raise RuntimeError('Failed to generate response')

        if replace_newline:
            output = output.replace('\n', '')
        return output

def LLM_CLS(llm_name: str, openai_api_key: str, long_ver: bool) -> Callable:
    if 'gpt' in llm_name:
        return GPTWrapper(llm_name, openai_api_key, long_ver)
    else:
        raise ValueError(f"Unknown LLM model name: {llm_name}")

def get_message(messages: List[ChatMessage]) -> str:
    final = []
    # 遍历每个ChatMessage实例，提取role和content
    for msg in messages:
        # 提取核心属性：msg.role（角色）、msg.content（消息内容）
        role_map = {
            "human": "用户",
            "ai": "助手",
            "system": "系统",
            "function": "工具"
        }
        # 优化角色显示（可选，也可直接使用msg.role）
        role_name = role_map.get(msg.role, msg.role)
        # 拼接单条消息（格式可自定义，保证上下文清晰即可）
        single_message = f"{role_name}：{msg.content}"
        prompt_parts.append(single_message)
    
    # 拼接所有消息为完整字符串（换行分隔，提升可读性）
    full_prompt = "\n\n".join(prompt_parts)
    return full_prompt
    return ""
def chatanywhere_llm(task_id: str, messages: List[dict], openai_api_key: str) -> str:
    import http.client
    import json
    conn = http.client.HTTPSConnection("api.chatanywhere.tech")
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": messages
    })
    headers = {
        'Authorization': 'Bearer ' + openai_api_key,
        'Content-Type': 'application/json'
    }
    print(f"\n🔹 Generating for task: {task_id}")
    try:
        conn.request("POST", "/v1/chat/completions", payload, headers)
        res = conn.getresponse()
        data = res.read()
        answer = json.loads(data.decode("utf-8"))
        return answer['choices'][0]['message']['content']
    except Exception as e:
        # 捕获所有其他未预期异常（兜底，防止程序中断）
        print(f"\n❌ Task {task_id} Unexpected Error: {str(e)}")
        return ""