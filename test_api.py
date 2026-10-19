"""测试智谱 API 调用，打印完整错误"""
import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ZHIPU_API_KEY", "")
print(f"API Key 长度: {len(api_key)}")
print(f"API Key 前10个字符 repr: {repr(api_key[:10])}")
print(f"API Key 是否纯 ASCII: {api_key.isascii()}")
print()

import requests
import json

url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json; charset=utf-8",
}
data = {
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "你好，说一句话"}],
}

# 方式1：手动 UTF-8 编码
body = json.dumps(data, ensure_ascii=False).encode("utf-8")
print(f"body 类型: {type(body)}, 长度: {len(body)}")
print(f"headers: {headers}")
print()

try:
    print("正在调用 API...")
    response = requests.post(url, headers=headers, data=body, timeout=60)
    print(f"状态码: {response.status_code}")
    print(f"返回前200字符: {response.text[:200]}")
except Exception as e:
    import traceback
    print("出错了！完整 traceback：")
    traceback.print_exc()
