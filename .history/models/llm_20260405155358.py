from typing import Callable, List
import time

from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
import openai


# client = openai.OpenAI(
#     # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
#     api_key="sk-a3b1a801d70747a0b7d3b2797a14ab05",
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
# )

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
# def generate_one_completion(messages):
#     # jiajia
#     # openai.api_key = "sk-a3b1a801d70747a0b7d3b2797a14ab05"
#     openai.api_key = "sk-afa113e744a345899ad27f3452c08ffa"
#     openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
#     messages = replace_invalid_roles(messages)
#     # completion = client.chat.completions.create(
#     completion = openai.ChatCompletion.create(
#         model="glm-4.6",
#         messages=messages,
#         extra_body={"enable_thinking": False},
#         stream=False,
#         temperature=0.2,  # 新增：可选，控制回复随机性
#         max_tokens=4096,   # 新增：可选，限制回复长度
#         headers={
#             "Authorization": f"Bearer {openai.api_key}",
#             "Content-Type": "application/json"
#         }
#     )
#     # print(f"\n🔹 Generating for task: {task_id}")
#     # 修正：直接取属性，而非转JSON字符串（更高效）
#     return completion.choices[0].message.content

import requests
import json
def generate_one_completion(messages):
    messages = replace_invalid_roles(messages)
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    payload = {
        "model": "glm-4.7",
        "messages": messages,
        "stream": False,
        "temperature": 0.1,
        "thinking": { "type": "disabled" },
        "response_format": { "type": "text" }
    }
    headers = {
        "Authorization": "Bearer 8e9538dc2cad4a958edcc94295daba15.FRhIeGeqFkFLcDCq",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # 捕获HTTP请求错误
    try:
        # 尝试正常打印
        print("llm response:", response.text)
    except UnicodeEncodeError:
        # 编码失败时，替换无法编码的字符（或忽略）
        print("llm response:", response.text.encode('utf-8', errors='replace').decode('utf-8'))
    # 第一步:解析LLM返回的顶层JSON
    llm_response = json.loads(response.text)
    # 提取content字段(此时是JSON字符串)
    content_json_str = llm_response["choices"][0]["message"]["content"]
    try:
        content_data = json.loads(content_json_str)
        # 核心:适配content_data为列表的情况(如 [[0], {xxx:xxx, answer:xxx}])
        if isinstance(content_data, list):
            # 遍历列表中的每个元素,找包含answer的字典
            answer = None
            for item in content_data:
                if isinstance(item, dict) and "answer" in item:
                    answer = item.get("answer")
                    break
            # 若列表中没找到answer,返回原字符串兜底
            if answer is None:
                answer = content_json_str
        
        # 兼容content_data为字典的情况
        elif isinstance(content_data, dict):
            answer = content_data.get("answer", content_json_str)
        
        # 其他类型(如字符串/数字)直接返回
        else:
            answer = content_json_str
        return answer.strip() if answer else ""       

    except json.JSONDecodeError:
        # 如果content不是有效JSON,直接返回原字符串
        answer = content_json_str
        return answer.strip() if answer else ""       
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误:{e}")
        return ""

class GPTWrapper:
    def __init__(self, llm_name: str, openai_api_key: str, long_ver: bool):
        self.model_name = llm_name
        self.openai_api_key = openai_api_key
        if long_ver:
            # llm_name = '3.5-turbo-16k'
            # llm_name = 'gpt-3.5-turbo'
            llm_name = 'gpt-3.5-turbo'
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
                # output = chatanywhere_llm(messages, self.openai_api_key)
                output = generate_one_completion(messages)
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