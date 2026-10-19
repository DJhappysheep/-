"""界面美化模块：统一全局样式、页头、步骤条。

用法：
    inject_theme()              # 每个页面调一次，注入全局样式
    render_header(标题, 副标题)  # 顶部渐变页头
    render_steps(当前步骤序号)    # 步骤条，序号从 1 开始
"""

import streamlit as st

BRAND = "#3B6EF6"
STEPS = ["选知识点", "看课程", "做检测", "看结果"]

_CSS = """
<style>
/* ---------- 全局字体与底色 ---------- */
.stApp {
    background: #FFFFFF;
    font-family: "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", "Segoe UI", Roboto, sans-serif;
    color: #1F2733;
}

/* ---------- 隐藏 Streamlit 默认装饰，去掉 demo 感 ---------- */
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ---------- 主容器宽度与留白 ---------- */
.block-container {
    padding-top: 2.2rem !important;
    padding-bottom: 3rem !important;
    max-width: 900px !important;
}

/* ---------- 卡片容器（st.container(border=True)） ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #e0e0e0 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* ---------- 顶部页头 ---------- */
.hero {
    background: linear-gradient(135deg, #EEF3FF 0%, #F8FAFF 100%);
    border: 1px solid #E3E9F7;
    border-radius: 14px;
    padding: 20px 26px;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 24px;
    font-weight: 700;
    color: #1F2733;
    margin: 0 0 6px 0;
    letter-spacing: .5px;
}
.hero-sub {
    font-size: 13px;
    color: #6B7688;
    margin: 0;
}

/* ---------- 步骤条 ---------- */
.steps {
    display: flex;
    gap: 8px;
    margin: 0 0 18px 0;
    flex-wrap: wrap;
}
.step {
    flex: 1 1 0;
    min-width: 108px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 13px;
    padding: 9px 8px;
    background: #FFFFFF;
    color: #97A1B2;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.step-dot {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    background: #F0F2F6;
    color: #97A1B2;
}
.step.active {
    border-color: #3B6EF6;
    background: #F5F8FF;
    color: #3B6EF6;
    font-weight: 600;
}
.step.active .step-dot { background: #3B6EF6; color: #FFFFFF; }
.step.done { color: #1FA463; border-color: #CFEADB; background: #F6FCF9; }
.step.done .step-dot { background: #1FA463; color: #FFFFFF; }

/* ---------- 卡片小标题 ---------- */
.card-title {
    font-size: 15px;
    font-weight: 600;
    color: #1F2733;
    margin: 2px 0 10px 0;
    display: flex;
    align-items: center;
}
.card-title .idx {
    display: inline-block;
    width: 20px;
    height: 20px;
    line-height: 20px;
    text-align: center;
    border-radius: 6px;
    background: #EEF3FF;
    color: #3B6EF6;
    font-size: 12px;
    font-weight: 700;
    margin-right: 8px;
}

/* ---------- 按钮 ---------- */
.stButton > button {
    border-radius: 10px !important;
    border: 1px solid #e0e0e0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    font-weight: 500;
    transition: all .15s ease;
    padding: 9px 18px !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    border-color: #3B6EF6 !important;
    color: #3B6EF6 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.10);
}
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background: #3B6EF6 !important;
    border: 1px solid #3B6EF6 !important;
    color: #FFFFFF !important;
    box-shadow: 0 3px 10px rgba(59, 110, 246, 0.28);
}
.stButton > button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background: #2F5DE0 !important;
    color: #FFFFFF !important;
}

/* ---------- 输入控件 ---------- */
.stTextInput input {
    border-radius: 10px !important;
    border: 1px solid #e0e0e0 !important;
    background: #FFFFFF;
}
.stTextInput input:focus {
    border-color: #3B6EF6 !important;
    box-shadow: 0 0 0 3px rgba(59, 110, 246, 0.12) !important;
}

/* ---------- 单选项做成卡片 ---------- */
div[data-testid="stRadio"] label {
    background: #FFFFFF;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 9px 14px;
    margin-bottom: 6px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    transition: all .15s ease;
}
div[data-testid="stRadio"] label:hover { border-color: #3B6EF6; }
div[data-testid="stRadio"] label p { font-size: 14px; }

/* ---------- 指标卡 ---------- */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* ---------- 折叠面板 ---------- */
div[data-testid="stExpander"] details {
    border: 1px solid #e0e0e0 !important;
    border-radius: 10px !important;
    background: #FFFFFF;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* ---------- 提示条与分隔线 ---------- */
div[data-testid="stAlert"] { border-radius: 10px; }
hr { border-color: #EEF0F4; }

/* ---------- B 站跳转按钮 ---------- */
.bili-btn {
    display: block;
    text-align: center;
    background: #00A1D6;
    color: #FFFFFF !important;
    font-size: 17px;
    font-weight: 600;
    padding: 14px 20px;
    border-radius: 10px;
    text-decoration: none;
    box-shadow: 0 3px 10px rgba(0, 161, 214, 0.28);
    transition: all .15s ease;
}
.bili-btn:hover {
    background: #0089B8;
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(0, 161, 214, 0.35);
    color: #FFFFFF !important;
}
</style>
"""


def inject_theme():
    """注入全局样式（禁止浏览器翻译 + 统一视觉）"""
    st.markdown(
        '<meta name="google" content="notranslate" />'
        '<meta name="translate" content="no" />',
        unsafe_allow_html=True,
    )
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str):
    """渲染顶部页头"""
    st.markdown(
        f'<div class="hero">'
        f'<div class="hero-title">{title}</div>'
        f'<p class="hero-sub">{subtitle}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_steps(current: int):
    """渲染步骤条，current 从 1 开始"""
    parts = ['<div class="steps">']
    for i, name in enumerate(STEPS, start=1):
        if i < current:
            cls, dot = "step done", "✓"
        elif i == current:
            cls, dot = "step active", str(i)
        else:
            cls, dot = "step", str(i)
        parts.append(f'<div class="{cls}"><span class="step-dot">{dot}</span>{name}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def card_title(idx: str, text: str):
    """卡片内小标题，idx 可以是 1/2/3 或图标"""
    st.markdown(
        f'<div class="card-title"><span class="idx">{idx}</span>{text}</div>',
        unsafe_allow_html=True,
    )
