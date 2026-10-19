"""
易学 · 打包版启动器（exe 入口）
作用：以编程方式启动 Streamlit，双击 exe 即自动打开浏览器
"""
import os
import sys
import threading
import webbrowser

# 先显式导入项目模块，让 PyInstaller 能收集到它们依赖的第三方库
# （app.py 由 Streamlit 在运行时动态加载，打包器静态分析看不到它）
import config  # noqa: F401
import tools.glm_client  # noqa: F401
import tools.image_utils  # noqa: F401
import tools.course_search  # noqa: F401
import tools.error_book  # noqa: F401
import tools.ui_theme  # noqa: F401

import streamlit.web.cli as stcli

PORT = "8501"


def _resource_path(relative: str) -> str:
    """打包后资源在临时解压目录(_MEIPASS)，开发时在项目目录"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def main():
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_PORT"] = PORT
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    app_path = _resource_path("app.py")

    print("=" * 48)
    print("  易学 已启动，浏览器会自动打开")
    print("  地址：http://localhost:%s" % PORT)
    print("  使用期间请勿关闭本窗口，关闭即退出程序")
    print("=" * 48)

    # 稍等服务器就绪再打开浏览器
    threading.Timer(2.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
