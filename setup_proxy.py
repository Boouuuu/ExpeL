"""
设置代理的工具函数
在导入其他模块之前调用此函数以设置代理
"""
import os
import requests

def setup_proxy(proxies=None):
    """
    设置代理
    Args:
        proxies: dict, 代理配置，例如 {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
    """
    if proxies is None:
        try:
            from proxy_config import PROXIES
            proxies = PROXIES
        except:
            proxies = None
    
    if proxies:
        # 设置环境变量（某些库会使用）
        if 'http' in proxies:
            os.environ['HTTP_PROXY'] = proxies['http']
        if 'https' in proxies:
            os.environ['HTTPS_PROXY'] = proxies['https']
        
        # 设置 requests 的默认代理
        requests.Session.proxies = proxies
        
        print(f"✓ 代理已设置: {proxies}")
    else:
        print("✗ 未设置代理，使用直连")
    
    return proxies

def test_wikipedia_connection():
    """
    测试是否能连接到维基百科
    """
    import requests
    headers = {
        "User-Agent": "curl/8.4.0",
        "Accept": "*/*",
        "Host": "en.wikipedia.org",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br",
        # 移除可能触发反爬的头：Referer、Accept-Language等
    }
    try:
        # response = requests.get('https://en.wikipedia.org/wiki/Main_Page', timeout=10)
        # 模拟curl的请求方式：允许重定向、延长超时
        response = requests.get(
            'https://en.wikipedia.org/wiki/Main_Page',
            timeout=(10, 30),  # (连接超时10秒, 读取超时30秒)
            allow_redirects=True,  # 允许重定向（curl默认开启，Python也需开启）
            verify=False,
            headers=headers
        )
        if response.status_code == 200:
            print("✓ 维基百科连接测试成功")
            return True
        else:
            print(f"✗ 维基百科连接测试失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 维基百科连接测试失败: {e}")
        return False

if __name__ == '__main__':
    # 测试
    print("测试代理设置...")
    setup_proxy()
    test_wikipedia_connection()


import requests
import time

# ===================== 请手动修改这两个参数 =====================
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"  # 智谱GLM标准地址
API_KEY = os.environ.get("OPENAI_API_KEY", "")
# =================================================================

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 极简测试请求，token量很小，排除超长prompt导致断开
payload = {
    "model": "glm-4.7",  # 按需改成你使用的模型 glm-3-turbo / glm-4
    "messages": [
        {"role": "user", "content": "你好，简单自我介绍一句话"}
    ],
    "temperature": 0.7,
    "max_tokens": 128
}

def test_glm_api():
    print("===== 开始测试GLM API连接 =====")
    try:
        # 设置超长超时，避免请求超时被断开
        response = requests.post(
            url=API_URL,
            json=payload,
            headers=headers,
            timeout=90
        )
        print(f"HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            print("✅ API 连通正常，接口无网络/连接问题！")
            res_data = response.json()
            print("模型返回内容：")
            print(res_data["choices"][0]["message"]["content"])
        elif response.status_code == 401:
            print("❌ 鉴权失败：你的API Key错误、过期或权限不足")
            print("返回详情：", response.text)
        elif response.status_code == 429:
            print("❌ 请求限流：调用频率太高/额度用尽，稍后重试")
            print("返回详情：", response.text)
        else:
            print(f"❌ 接口返回异常，错误信息：{response.text}")

    except requests.exceptions.ConnectionResetError:
        print("❌ 报错 10054 远程主机强制关闭连接：网络拦截/服务商断连/代理冲突")
    except requests.exceptions.ConnectionError:
        print("❌ 完全无法建立连接：检查网络、关闭VPN/代理、防火墙")
    except requests.exceptions.Timeout:
        print("❌ 请求超时，服务器长时间无响应")
    except Exception as e:
        print(f"❌ 未知错误：{type(e).__name__}, 详情：{e}")

if __name__ == "__main__":
    test_glm_api()
    print("\n===== 测试结束 =====")