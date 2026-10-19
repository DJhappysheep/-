"""
课程检索工具
从本地 JSON 课程库中按知识点搜索课程
"""
import json
import os

# 课程库路径
COURSES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "courses.json")


def load_courses() -> list:
    """加载课程库 JSON"""
    with open(COURSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def search_courses(knowledge_point: str, grade: str = "") -> list:
    """
    按知识点搜索课程

    knowledge_point: 知识点名称（如"现在完成时"）
    grade: 年级筛选（可选，如"八年级"）
    返回: 匹配的课程列表
    """
    all_courses = load_courses()
    results = []

    for course in all_courses:
        # 知识点匹配（支持模糊匹配）
        if knowledge_point in course["知识点"] or course["知识点"] in knowledge_point:
            # 如果指定了年级，进一步筛选
            if grade and grade not in course.get("年级", ""):
                continue
            results.append(course)

    return results


def search_with_fallback(knowledge_point: str, grade: str = "", subject: str = "英语") -> dict:
    """
    生成 B 站搜索链接（一键跳转到 B 站搜索结果页）

    knowledge_point: 知识点名称（如"现在完成时"、"一元二次方程"）
    grade: 年级（可选，如"八年级"）
    subject: 学科（"英语" 或 "数学"）

    返回:
    {
        "知识点": "现在完成时",
        "搜索词": "现在完成时 初中英语 讲解",
        "搜索链接": "https://search.bilibili.com/..."
    }
    """
    # 构建 B 站搜索词
    search_keyword = f"{knowledge_point} 初中{subject} 讲解"
    if grade:
        search_keyword = f"{knowledge_point} {grade} 初中{subject} 讲解"

    from urllib.parse import quote
    search_url = f"https://search.bilibili.com/all?keyword={quote(search_keyword)}"

    return {
        "知识点": knowledge_point,
        "搜索词": search_keyword,
        "搜索链接": search_url,
    }


# 测试用：直接运行这个文件可以看到搜索结果
if __name__ == "__main__":
    result = search_with_fallback("现在完成时", "八年级")
    print(f"知识点: {result['知识点']}")
    print(f"匹配到 {len(result['匹配课程'])} 个课程:")
    for c in result["匹配课程"]:
        print(f"  - {c['课程标题']} ({c['来源']})")
    print(f"兜底搜索词: {result['搜索词']}")
    print(f"兜底搜索链接: {result['搜索链接']}")
