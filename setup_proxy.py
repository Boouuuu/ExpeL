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
