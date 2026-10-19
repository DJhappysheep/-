"""
初中错题工具 - MVP v0.4（向导式分页）
英语/数学双科 | 图片识别 + 手动输入 + B站搜课 + 出题检测 + 错题本

页面流转：
  home（选择学科+输入知识点/上传图片）
    → learn（B站一键跳转学习）
      → quiz（出题检测 + 答题 + 批改结果）
  book（错题本，随时可从首页进入）

运行方式：streamlit run app.py
"""
import sys
import os

# 修复 Windows 编码问题（防止 ASCII 编码错误）
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import streamlit as st
import json
import re
from tools.glm_client import chat_vision, chat_text
from tools.image_utils import compress_image, image_to_base64
from tools.course_search import search_with_fallback
from tools.error_book import add_wrong_question, get_all_wrong_questions, mark_mastered, delete_question, get_stats
from tools.ui_theme import inject_theme, render_header, card_title

# ====== JSON 清洗工具 ======
def clean_json_text(raw: str) -> str:
    """清洗 AI 返回的文本，提取合法 JSON：
    1. 去掉 markdown 代码块围栏（```json ... ```）
    2. 修复 LaTeX 反斜杠（如 \\( x^2 \\)）导致的非法 JSON 转义
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    # 反斜杠后不是合法 JSON 转义字符时，补成双反斜杠（变成字面量）
    text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
    return text.strip()


def strip_latex(text):
    """去掉 LaTeX 定界符，便于阅读：\\( x^2 \\) -> x^2"""
    if not isinstance(text, str):
        return text
    for d in ["\\(", "\\)", "\\[", "\\]", "\\("]:
        text = text.replace(d, "")
    return text


def normalize_question(q) -> bool:
    """规范化单道题的选项：
    1. 选项 key 统一映射为 A/B/C/D
    2. 选项值去掉 'A.' 'B、' '答：' '答。' 等多余前缀
    3. 校验正确答案必须存在于选项中
    返回 True=题目有效，False=题目有问题应丢弃
    """
    opts = q.get("选项", {})
    if not isinstance(opts, dict) or len(opts) < 2:
        return False

    letters = ["A", "B", "C", "D"]
    # key 不是标准 A-D 时，按顺序重映射
    if any(k not in letters for k in opts.keys()):
        opts = {letters[i]: str(v) for i, (k, v) in enumerate(opts.items()) if i < 4}

    # 清理选项值里的脏前缀
    cleaned = {}
    for k, v in opts.items():
        v = str(v).strip()
        v = re.sub(r'^[A-Da-d]\s*[.、．:：。]\s*', '', v)   # 去掉 "A. " "B、" 前缀
        v = re.sub(r'^答\s*[.、．:：。]?\s*', '', v)         # 去掉 "答：" "答。" 前缀
        cleaned[k] = v
    q["选项"] = cleaned

    # 正确答案校验：必须是存在的选项 key
    if q.get("正确答案", "") not in cleaned:
        return False
    return True


# ====== 出题函数（英语/数学共用入口） ======
def generate_quiz(kp: str, subj: str):
    """调 AI 出题，返回 (题目列表, 被过滤数, 错误信息)。成功时错误信息为 None。"""
    if subj == "英语":
        prompt = f"""You are an English teacher. Create 3 multiple-choice questions about: {kp}

CRITICAL RULES:
- Questions MUST be in ENGLISH (not Chinese!)
- Options MUST be in ENGLISH (not Chinese!)
- Only the explanation can be in Chinese
- This is for Chinese students learning English, so all English sentences must be proper

Example format:
Question: "_____ you ever _____ to Beijing?" (present perfect)
A. Have, been
B. Did, go
C. Do, go
D. Will, go
Answer: A
Explanation: 现在完成时结构是 have/has + 过去分词

Now create 3 questions about {kp}. Return ONLY this JSON:

{{
  "题目": [
    {{
      "题号": 1,
      "题干": "_____ English sentence here _____",
      "选项": {{"A": "English option", "B": "English option", "C": "English option", "D": "English option"}},
      "正确答案": "A",
      "解析": "中文解析"
    }}
  ]
}}"""
    else:
        prompt = f"""你是初中数学老师，请针对知识点「{kp}」出 3 道选择题。

要求：
1. 题目和选项都用中文，数学公式用普通文字或符号表述（如 x²、√2、½、≤）
2. 不要使用 LaTeX 语法（禁止反斜杠符号）
3. 选项内容里不要带 "A." "答：" 这类前缀，只写选项本身
4. 难度由简过渡到单到适中，符合初中生水平
5. 每题 4 个选项（A/B/C/D）
6. 出完题后自己重新解一遍，确保正确答案确实在选项中且唯一，不一致就修正后再输出
7. 给出正确答案和详细解析（含解题步骤）

示例：
题干: 解一元二次方程 x² - 5x + 6 = 0 的根是多少？
选项: {{"A": "2 和 3", "B": "-2 和 3", "C": "2 和 -3", "D": "-2 和 -3"}}
正确答案: A
解析: 因式分解 (x-2)(x-3)=0，所以 x=2 或 x=3

只返回 JSON，不要其他文字：

{{
  "题目": [
    {{
      "题号": 1,
      "题干": "数学题目内容",
      "选项": {{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}},
      "正确答案": "A",
      "解析": "解题步骤和原因"
    }}
  ]
}}"""

    quiz_text = chat_text(prompt)
    clean = clean_json_text(quiz_text)

    try:
        quiz_json = json.loads(clean)
    except json.JSONDecodeError:
        return [], 0, f"JSON 解析失败，AI 原文：{quiz_text[:500]}"

    raw_questions = quiz_json.get("题目", quiz_json.get("questions", []))
    valid, dropped = [], 0
    for q in raw_questions:
        q["题干"] = strip_latex(q.get("题干", ""))
        q["解析"] = strip_latex(q.get("解析", ""))
        if isinstance(q.get("选项"), dict):
            q["选项"] = {k: strip_latex(v) for k, v in q["选项"].items()}
        if normalize_question(q):
            valid.append(q)
        else:
            dropped += 1

    if not valid:
        return [], dropped, "AI 出的题目格式全部无效，请重新出题"
    return valid, dropped, None


# ====== 页面配置 ======
st.set_page_config(
    page_title="初中错题工具",
    page_icon="📚",
    layout="centered",
)

# ====== 全局样式（美化主题 + 禁止浏览器翻译） ======
inject_theme()


# ====== 页面状态初始化 ======
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "quiz_id" not in st.session_state:
    st.session_state["quiz_id"] = 0


def go_home():
    """回到首页，清空本次学习状态"""
    for k in ["knowledge_point", "grade", "subject", "quiz", "result", "recognize_result"]:
        st.session_state.pop(k, None)
    st.session_state["page"] = "home"


# ====== 页面标题 ======
render_header(
    "易  学",
    "英语 / 数学 · 拍照识题 · B站学课 · 出题检测 · 自动整理错题本",
)


# ============================================================
# 页面 1：home - 选择学科 + 输入知识点streamlit run app.py
# ============================================================
if st.session_state["page"] == "home":
    with st.container(border=True):
        card_title("1", "选择学科")
        subject = st.radio(
            "学科",
            ["🔤 英语", "🔢 数学"],
            horizontal=True,
            label_visibility="collapsed",
        )
        subject_name = "英语" if "英语" in subject else "数学"

        card_title("2", "选择输入方式")
        input_mode = st.radio(
            "输入方式",
            ["📝 手动输入知识点", "📷 上传错题图片"],
            horizontal=True,
            label_visibility="collapsed",
        )

    # ---------- 方式 A：手动输入 ----------
    if input_mode == "📝 手动输入知识点":
        with st.container(border=True):
            card_title("3", f"输入初中{subject_name}知识点")

            placeholder = "例如：现在完成时" if subject_name == "英语" else "例如：一元二次方程"
            knowledge_point = st.text_input(
                "知识点",
                placeholder=placeholder,
                help=f'输入初中{subject_name}的知识点名称',
                label_visibility="collapsed",
            )

            grade = st.selectbox(
                "年级",
                ["", "七年级", "八年级", "九年级"],
                placeholder="请选择年级（可不选）",
                help="选择年级可以让搜索更精准"
            )

            st.caption("💡 常用知识点（点击直接开始学习）：")
            if subject_name == "英语":
                common_points = ["现在完成时", "一般过去时", "被动语态", "定语从句", "宾语从句"]
            else:
                common_points = ["一元二次方程", "二次函数", "勾股定理", "全等三角形", "因式分解"]
            cols = st.columns(len(common_points))
            for i, point in enumerate(common_points):
                if cols[i].button(point, key=f"quick_{subject_name}_{point}", use_container_width=True):
                    st.session_state["knowledge_point"] = point
                    st.session_state["grade"] = grade
                    st.session_state["subject"] = subject_name
                    st.session_state["page"] = "learn"
                    st.rerun()

            st.write("")
            if st.button(
                "🔍 开始学习",
                type="primary",
                use_container_width=True,
                disabled=not knowledge_point,
            ):
                st.session_state["knowledge_point"] = knowledge_point
                st.session_state["grade"] = grade
                st.session_state["subject"] = subject_name
                st.session_state["page"] = "learn"
                st.rerun()

    # ---------- 方式 B：上传图片识别 ----------
    else:
        with st.container(border=True):
            card_title("3", f"上传一张初中{subject_name}错题图片")

            tab_camera, tab_album = st.tabs(["📷 拍照", "🖼️ 从相册选图"])
            with tab_camera:
                uploaded_file = st.camera_input(
                    "点击拍照",
                    help="手机点击直接调起相机拍照；电脑点击调用摄像头",
                )
            with tab_album:
                uploaded_file = st.file_uploader(
                    f"选择一张{subject_name}错题图片",
                    type=['jpg', 'jpeg', 'png', 'webp'],
                    help="支持 jpg/png/webp 格式",
                    label_visibility="collapsed",
                )

            if uploaded_file is not None:
                st.image(uploaded_file, caption="已选图片", width=400)

                raw_bytes = uploaded_file.getvalue()
                compressed = compress_image(raw_bytes)
                st.caption(f"原图 {len(raw_bytes) // 1024}KB -> 压缩后 {len(compressed) // 1024}KB")

                if st.button("🔍 开始识别", type="primary", use_container_width=True):
                    with st.spinner("AI 正在看图，请等几秒..."):
                        try:
                            b64 = image_to_base64(compressed)

                            if subject_name == "英语":
                                prompt = """请识别这张图片中的初中英语题目，返回 JSON 格式：
{
  "学科": "初中英语",
  "年级": "七年级/八年级/九年级",
  "知识点": "具体知识点，如'现在完成时'、'定语从句'",
  "题目原文": "题目完整文字",
  "题型": "选择题/填空题/阅读理解/完形填空/作文/其他"
}
只返回 JSON，不要其他文字。"""
                            else:
                                prompt = """请识别这张图片中的初中数学题目，返回 JSON 格式：
{
  "学科": "初中数学",
  "年级": "七年级/八年级/九年级",
  "知识点": "具体知识点，如'一元二次方程'、'二次函数'、'勾股定理'",
  "题目原文": "题目完整文字（数学公式用文字表述，如x²、√2）",
  "题型": "选择题/填空题/计算题/证明题/应用题/其他"
}
只返回 JSON，不要其他文字。"""

                            result_text = chat_vision(b64, prompt)

                            try:
                                result_json = json.loads(clean_json_text(result_text))

                                kp = result_json.get("知识点", "")
                                if not kp:
                                    st.error("AI 没识别出知识点，请换个更清晰的图片试试")
                                    st.json(result_json)
                                else:
                                    st.session_state["knowledge_point"] = kp
                                    st.session_state["grade"] = result_json.get("年级", "")
                                    st.session_state["subject"] = subject_name
                                    st.session_state["recognize_result"] = result_json
                                    st.session_state["page"] = "learn"
                                    st.rerun()

                            except json.JSONDecodeError:
                                st.error("识别结果解析失败，AI 原文：")
                                st.text_area("AI 返回", result_text, height=200)

                        except Exception as e:
                            st.error(f"❌ 识别失败：{e}")
                            st.caption("可能原因：API key 未配置、网络问题、图片格式不支持")
                            with st.expander("查看错误详情"):
                                st.text(str(e))

    # ---------- 错题本入口 ----------
    st.write("")
    with st.container(border=True):
        st.markdown("##### 📕 我的错题本")
        st.caption("做错的题会自动收集到这里，方便随时复习")
        if st.button("打开我的错题本", use_container_width=True):
            st.session_state["page"] = "book"
            st.rerun()


# ============================================================
# 页面 2：learn - B 站一键跳转学习
# ============================================================
elif st.session_state["page"] == "learn":
    kp = st.session_state.get("knowledge_point", "")
    gr = st.session_state.get("grade", "")
    subj = st.session_state.get("subject", "英语")

    with st.container(border=True):
        card_title("1", "本次学习内容")
        st.markdown(f"#### {kp}")
        st.caption(f"初中{subj}" + (f" · {gr}" if gr else ""))
        if st.session_state.get("recognize_result"):
            with st.expander("🔍 查看图片识别详情"):
                st.json(st.session_state["recognize_result"])

    search_result = search_with_fallback(kp, gr, subj)

    with st.container(border=True):
        card_title("2", "去 B 站看讲解视频")
        st.caption(f"搜索词：{search_result['搜索词']}")
        st.markdown(f"""
        <a class="bili-btn" href="{search_result['搜索链接']}" target="_blank">
            ▶ 在 B 站学习「{kp}」
        </a>
        """, unsafe_allow_html=True)
        st.caption("点击后在 B 站搜索结果里挑一个讲得清楚的视频，看完回来做检测")

    with st.container(border=True):
        card_title("3", "学完了，做个检测")
        st.caption("AI 会根据这个知识点出 3 道选择题，检验掌握情况")
        if st.button("📝 出题检测", type="primary", use_container_width=True):
            with st.spinner("AI 正在出题，请等几秒..."):
                try:
                    questions, dropped, error = generate_quiz(kp, subj)
                    if error:
                        st.error(f"出题失败：{error}")
                    else:
                        st.session_state["quiz"] = questions
                        st.session_state["quiz_id"] += 1
                        st.session_state.pop("result", None)
                        st.session_state["page"] = "quiz"
                        if dropped:
                            st.toast(f"⚠️ {dropped} 道题格式异常已自动过滤")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 出题失败：{e}")
                    with st.expander("查看错误详情"):
                        st.text(str(e))

    st.write("")
    if st.button("⬅️ 返回重新选择知识点"):
        go_home()
        st.rerun()


# ============================================================
# 页面 3：quiz - 答题 + 批改
# ============================================================
elif st.session_state["page"] == "quiz":
    kp = st.session_state.get("knowledge_point", "")
    subj = st.session_state.get("subject", "英语")
    questions = st.session_state.get("quiz", [])
    quiz_id = st.session_state.get("quiz_id", 0)

    # ---------- 已提交：显示批改结果 ----------
    if "result" in st.session_state:
        result = st.session_state["result"]
        total = result["总题数"]
        score = result["得分"]

        with st.container(border=True):
            st.markdown("#### 检测结果")
            c1, c2 = st.columns([1, 2])
            c1.metric("得分", f"{score} / {total}")
            with c2:
                st.write("")
                st.progress(score / total if total else 0)
                if score == total:
                    st.success("🎉 全部正确，这个知识点掌握得很好！")
                else:
                    st.warning(f"答错 {total - score} 题，错题已自动收进错题本")

        for i, item in enumerate(result["details"]):
            with st.container(border=True):
                if item["正确"]:
                    st.success(f"第 {i+1} 题　✅ 正确")
                else:
                    st.error(f"第 {i+1} 题　❌ 错误：你选了 {item['你的答案']}，正确答案是 {item['正确答案']}")
                st.caption(f"解析：{item['解析']}")

        if score == total:
            st.balloons()

        st.write("")
        c1, c2, c3 = st.columns(3)
        if c1.button("🔄 重新出一套题", type="primary", use_container_width=True):
            with st.spinner("AI 正在重新出题..."):
                try:
                    new_questions, dropped, error = generate_quiz(kp, subj)
                    if error:
                        st.error(f"出题失败：{error}")
                    else:
                        st.session_state["quiz"] = new_questions
                        st.session_state["quiz_id"] += 1
                        st.session_state.pop("result", None)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 出题失败：{e}")
        if c2.button("⬅️ 返回学习页", use_container_width=True):
            st.session_state["page"] = "learn"
            st.rerun()
        if c3.button("🏠 学习新知识点", use_container_width=True):
            go_home()
            st.rerun()

    # ---------- 未提交：显示答题区 ----------
    else:
        with st.container(border=True):
            st.markdown(f"#### {kp}")
            st.caption(f"初中{subj} · 共 {len(questions)} 题 · 选好后点最下方提交")

        for i, q in enumerate(questions):
            with st.container(border=True):
                card_title(str(i + 1), "选择题")
                st.markdown(q.get("题干", ""))

                options = q.get("选项", {})
                st.radio(
                    "你的答案",
                    options=list(options.keys()),
                    format_func=lambda k: f"{k}. {options.get(k, '')}",
                    key=f"q_{quiz_id}_{i}",
                    label_visibility="collapsed",
                )

        st.write("")
        c1, c2 = st.columns([2, 1])
        submit = c1.button("✅ 提交答案", type="primary", use_container_width=True)
        back = c2.button("⬅️ 返回学习页", use_container_width=True)

        if back:
            st.session_state["page"] = "learn"
            st.rerun()

        if submit:
            # 收集答案并批改
            details = []
            correct_count = 0
            for i, q in enumerate(questions):
                user_ans = st.session_state.get(f"q_{quiz_id}_{i}", "")
                correct_ans = q.get("正确答案", "")
                is_right = (user_ans == correct_ans)
                if is_right:
                    correct_count += 1
                details.append({
                    "正确": is_right,
                    "你的答案": user_ans,
                    "正确答案": correct_ans,
                    "解析": q.get("解析", "无解析"),
                })

                # 错题写入 SQLite
                if not is_right:
                    add_wrong_question(
                        knowledge_point=f"{subj}·{kp}",
                        question=q.get("题干", ""),
                        user_answer=user_ans,
                        correct_answer=correct_ans,
                        explanation=q.get("解析", ""),
                    )

            st.session_state["result"] = {
                "details": details,
                "得分": correct_count,
                "总题数": len(questions),
            }
            st.rerun()


# ============================================================
# 页面 4：book - 错题本
# ============================================================
elif st.session_state["page"] == "book":
    st.markdown("#### 📕 我的错题本")
    st.caption("做错的题会自动收集到这里，随时可以复习")

    stats = get_stats()

    c1, c2 = st.columns(2)
    c1.metric("累计错题", f"{stats['总数']} 道")
    c2.metric("未掌握", f"{stats['未掌握']} 道")

    if stats["按知识点"]:
        with st.expander("📊 薄弱知识点排行（按错题数量）"):
            for item in stats["按知识点"]:
                st.markdown(f"- **{item['知识点']}**：错了 {item['错题数']} 题")

    only_unmastered = st.checkbox("只看未掌握的错题", value=True)
    wrong_list = get_all_wrong_questions(only_unmastered=only_unmastered)

    if not wrong_list:
        st.info("暂无错题，快去首页检测几个知识点吧！")
    else:
        for w in wrong_list:
            mastered_tag = "✅ 已掌握" if w["已掌握"] else "❌ 未掌握"
            with st.expander(f"[{mastered_tag}] {w['知识点']} | {w['时间']}"):
                st.markdown(f"**题干：** {w['题干']}")
                st.markdown(f"**你的答案：** {w['你的答案']}　|　**正确答案：** {w['正确答案']}")
                st.info(f"**解析：** {w['解析']}")
                b1, b2 = st.columns(2)
                if not w["已掌握"]:
                    if b1.button("标记为已掌握", key=f"master_{w['id']}", use_container_width=True):
                        mark_mastered(w["id"], mastered=True)
                        st.rerun()
                else:
                    if b1.button("标记为未掌握", key=f"unmaster_{w['id']}", use_container_width=True):
                        mark_mastered(w["id"], mastered=False)
                        st.rerun()
                if b2.button("删除此题", key=f"del_{w['id']}", use_container_width=True):
                    delete_question(w["id"])
                    st.rerun()

    st.write("")
    if st.button("🏠 返回首页", type="primary", use_container_width=True):
        st.session_state["page"] = "home"
        st.rerun()
