"""
错题本工具 - SQLite 持久化存储
功能：添加错题、查询错题、标记已掌握、删除错题、统计
"""
import sqlite3
import os
import sys
from datetime import datetime

# 打包成 exe 后，数据库放在 exe 同目录（可读写、可持久化）；
# 开发环境仍用项目根目录/data
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "error_book.db")


def _get_conn():
    """获取数据库连接（自动建目录建表）"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            knowledge_point TEXT NOT NULL,
            question TEXT NOT NULL,
            user_answer TEXT,
            correct_answer TEXT,
            explanation TEXT,
            is_mastered INTEGER DEFAULT 0
        )
    """)
    return conn


def add_wrong_question(knowledge_point, question, user_answer, correct_answer, explanation):
    """添加一道错题，返回记录 id"""
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO wrong_questions (created_at, knowledge_point, question, user_answer, correct_answer, explanation) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"), knowledge_point, question, user_answer, correct_answer, explanation),
    )
    conn.commit()
    qid = cur.lastrowid
    conn.close()
    return qid


def get_all_wrong_questions(only_unmastered=False):
    """查询错题列表（默认全部，可选只看未掌握），按时间倒序"""
    conn = _get_conn()
    if only_unmastered:
        rows = conn.execute(
            "SELECT id, created_at, knowledge_point, question, user_answer, correct_answer, explanation, is_mastered "
            "FROM wrong_questions WHERE is_mastered = 0 ORDER BY id DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, created_at, knowledge_point, question, user_answer, correct_answer, explanation, is_mastered "
            "FROM wrong_questions ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [
        {
            "id": r[0], "时间": r[1], "知识点": r[2], "题干": r[3],
            "你的答案": r[4], "正确答案": r[5], "解析": r[6], "已掌握": bool(r[7]),
        }
        for r in rows
    ]


def mark_mastered(qid, mastered=True):
    """标记某道错题为已掌握/未掌握"""
    conn = _get_conn()
    conn.execute("UPDATE wrong_questions SET is_mastered = ? WHERE id = ?", (1 if mastered else 0, qid))
    conn.commit()
    conn.close()


def delete_question(qid):
    """删除某道错题"""
    conn = _get_conn()
    conn.execute("DELETE FROM wrong_questions WHERE id = ?", (qid,))
    conn.commit()
    conn.close()


def get_stats():
    """统计：总错题数、未掌握数、按知识点分组的数量"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM wrong_questions").fetchone()[0]
    unmastered = conn.execute("SELECT COUNT(*) FROM wrong_questions WHERE is_mastered = 0").fetchone()[0]
    by_kp = conn.execute(
        "SELECT knowledge_point, COUNT(*) AS n FROM wrong_questions WHERE is_mastered = 0 "
        "GROUP BY knowledge_point ORDER BY n DESC"
    ).fetchall()
    conn.close()
    return {"总数": total, "未掌握": unmastered, "按知识点": [{"知识点": k, "错题数": n} for k, n in by_kp]}
