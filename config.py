# -*- coding: utf-8 -*-
"""常量与路径配置"""
import os

# ---------- 文档路径(优先级: --doc > VOCAB_DOC > 同目录默认) ----------
def resolve_doc():
    """按优先级解析文档路径"""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--doc", default=None)
    a, _ = ap.parse_known_args()
    if a.doc:
        return os.path.abspath(a.doc)
    env = os.environ.get("VOCAB_DOC")
    if env:
        return os.path.abspath(env)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "英语学习文档_整理版.docx")


DOC = resolve_doc()
SPEAK_VBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_speak.vbs")

# ---------- 轮播 ----------
INTERVAL_MS = 10000
TICK_MS = 50
MIN_SEC, MAX_SEC = 3, 30

# ---------- 窗口 ----------
WIN_W, WIN_H = 640, 240
BG = "#202028"
FG_DIM = "#888"
FG_ACCENT = "#ffd580"

# ---------- 全局热键 Ctrl+Alt+P ----------
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_ALT = 0x0001
VK_P = 0x50

# ---------- 搜索 ----------
SEARCH_SCORE_MIN = 40
SEARCH_RESULT_LIMIT = 20
