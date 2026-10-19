"""
配置文件：API key 和模型设置
智谱开放平台：https://open.bigmodel.cn
"""
import os
import sys
from dotenv import load_dotenv

# 打包成 exe 后，以 exe 所在目录为基准；否则用项目根目录
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 从 .env 文件加载环境变量（显式指定路径，保证 exe 也能读到）
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ====== 智谱 API 配置 ======
# 优先读云端 Streamlit Secrets（手机/云端部署用），没有则读本地 .env（exe/开发用）
# 用 try 包裹，避免非 Streamlit 环境（如直接跑 test_api.py）报错
try:
    import streamlit as st
    ZHIPU_API_KEY = st.secrets.get("ZHIPU_API_KEY", "") or os.getenv("ZHIPU_API_KEY", "")
except Exception:
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# 文本模型（用于出题、批改、讲解）
# 智谱免费模型，名称请以智谱控制台为准
MODEL_TEXT = "glm-4-flash"

# 多模态模型（用于图片识别）
# 智谱免费视觉模型，名称请以智谱控制台为准
MODEL_VISION = "glm-4v-flash"

# ====== 错题检查项 ======
# 启动时检查 API key 是否配置
if not ZHIPU_API_KEY:
    import warnings
    warnings.warn("未配置 ZHIPU_API_KEY，请复制 .env.example 为 .env 并填入 API key")
