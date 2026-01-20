# 代理设置说明

## 问题

在中国大陆访问维基百科（en.wikipedia.org）通常会被封锁，导致程序无法正常运行，出现如下错误：

```
Connection aborted
HTTPConnectionPool: Max retries exceeded
Failed to establish a new connection
```

## 解决方案

### 方法1：使用代理（推荐）

#### 步骤1：启动代理工具

常用的代理工具：
- **Clash for Windows**
- **V2Ray**
- **Shadowsocks**
- 其他VPN工具

启动代理后，通常代理地址为：`http://127.0.0.1:7890`（端口可能不同，请查看代理工具的设置）

#### 步骤2：配置代理

编辑 `proxy_config.py` 文件：

```python
# 取消注释并填入你的代理地址
PROXIES = {
    'http': 'http://127.0.0.1:7890',    # 替换为你的代理地址和端口
    'https': 'http://127.0.0.1:7890'    # 替换为你的代理地址和端口
}
```

**常见代理端口：**
- Clash for Windows: 7890
- V2Ray: 10808
- Shadowsocks: 1080

#### 步骤3：测试连接

运行测试脚本：

```bash
python setup_proxy.py
```

如果看到 "✓ 维基百科连接测试成功"，说明配置正确。

#### 步骤4：运行程序

正常运行你的程序即可，代理会自动生效。

### 方法2：使用系统代理

如果你已经在系统级别设置了代理，可以不修改 `proxy_config.py`，程序会自动使用系统代理。

### 方法3：临时设置环境变量

在运行程序前设置环境变量：

**Windows (PowerShell):**
```powershell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"
python train.py
```

**Windows (CMD):**
```cmd
set HTTP_PROXY=http://127.0.0.1:7890
set HTTPS_PROXY=http://127.0.0.1:7890
python train.py
```

**Linux/Mac:**
```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
python train.py
```

## 常见问题

### Q: 我不知道我的代理地址

A: 打开你的代理工具，查看 "端口" 或 "Port" 设置。通常在 "设置" 或 "配置" 中可以找到。

### Q: 代理设置后仍然无法连接

A: 
1. 确认代理工具正在运行
2. 确认代理地址和端口正确
3. 在代理工具中开启 "系统代理" 或 "TUN模式"
4. 尝试在浏览器中访问 https://en.wikipedia.org 测试代理是否工作

### Q: 我在国外/有直连访问

A: 保持 `proxy_config.py` 中的 `PROXIES = None` 即可，程序会直连访问。

## 技术细节

程序通过以下方式支持代理：

1. `setup_proxy.py` 在程序启动时设置环境变量和 requests 默认代理
2. `proxy_config.py` 存储代理配置
3. `wikienv.py` 在请求时使用配置的代理

所有HTTP/HTTPS请求都会通过设置的代理服务器转发。
