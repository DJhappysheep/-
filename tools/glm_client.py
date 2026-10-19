"""
智谱 GLM API 封装
用 requests 直接调智谱 API，手动 UTF-8 编码绕过 Windows 编码问题
"""
import requests
import json
from config import ZHIPU_API_KEY, ZHIPU_BASE_URL, MODEL_TEXT, MODEL_VISION


def _call_api(data: dict) -> str:
    """统一调用智谱 API，返回 AI 回复文本"""
    url = ZHIPU_BASE_URL + "chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }

    # 手动 JSON 序列化 + UTF-8 编码，绕过 requests 的 latin-1 问题
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")

    response = requests.post(url, headers=headers, data=body, timeout=60)
    response.encoding = "utf-8"

    if response.status_code != 200:
        raise Exception(f"API 调用失败 ({response.status_code}): {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


def chat_text(prompt: str, system: str = "") -> str:
    """
    文本对话
    用途：出题、批改、讲解

    prompt: 用户提问
    system: 系统人设（可选）
    返回: AI 回复的文本
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": MODEL_TEXT,
        "messages": messages,
    }

    return _call_api(data)


def chat_vision(image_base64: str, prompt: str) -> str:
    """
    多模态对话（图片 + 文字）
    用途：识别错题图片

    image_base64: base64 编码的图片字符串
    prompt: 要问 AI 什么
    返回: AI 回复的文本
    """
    data = {
        "model": MODEL_VISION,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        }],
    }

    return _call_api(data)
