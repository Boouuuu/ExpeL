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
            # llm_name = 'gpt-3.5-turbo'
            llm_name = 'gpt-4o'
        self.llm = ChatOpenAI(
            model=llm_name,
            temperature=0.0,
            openai_api_key=openai_api_key,
        )

    def __call__(self, messages: List[dict], stop: List[str] = [], replace_newline: bool = True) -> str:
        kwargs = {}
        if stop != []:
            kwargs['stop'] = stop
        for i in range(6):
            try:
                # output = self.llm(messages, **kwargs).content.strip('\n').strip()
                output = chatanywhere_llm(messages, self.openai_api_key)
                if output == "":  # API调用失败
                    print(f'\nAPI call failed, retrying {i+1}/6...')
                    time.sleep(2)  # 等待2秒后重试
                    continue
                output = output.strip('\n').strip()
                break
            except openai.error.RateLimitError:
                print(f'\nRate limit error, retrying {i+1}/6...')
                time.sleep(2)
        else:
            raise RuntimeError('Failed to generate response after 6 attempts')

        if replace_newline:
            output = output.replace('\n', '')
        return output

def LLM_CLS(llm_name: str, openai_api_key: str, long_ver: bool) -> Callable:
    if 'gpt' in llm_name:
        return GPTWrapper(llm_name, openai_api_key, long_ver)
    else:
        raise ValueError(f"Unknown LLM model name: {llm_name}")

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

def chatanywhere_llm(messages: List[dict], openai_api_key: str) -> str:
    import http.client
    import json
    conn = http.client.HTTPSConnection("api.chatanywhere.tech")
    messages = get_message(messages)
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": messages
    })
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