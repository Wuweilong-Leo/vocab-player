# -*- coding: utf-8 -*-
"""从 .docx 学习文档读取词条"""
import re
from docx import Document
from config import DOC

# 匹配词条末尾的 /音标/ 词性
TRAIL_RE = re.compile(
    r"(?:^|\s)/([^/]+)/(?:\s+(phr\.?v\.?|phr\.|n\.|adj\.|adv\.|v\.|phrase|句|conj\.))?\s*$",
    re.I,
)


def load_entries():
    """读取文档,返回 [(en, zh, usage), ...] 列表"""
    entries = []
    try:
        doc = Document(DOC)
        for t in doc.tables:
            if len(t.rows) < 2:
                continue
            if t.rows[0].cells[0].text.strip() != "英文":
                continue
            for r in t.rows[1:]:
                cells = [c.text.strip() for c in r.cells]
                if not cells or not cells[0]:
                    continue
                en = cells[0]
                zh = cells[1] if len(cells) > 1 else ""
                usage = cells[2] if len(cells) > 2 else ""
                entries.append((en, zh, usage))
    except Exception as e:
        entries = [("（读取学习文档失败）", str(e)[:80], DOC)]
    if not entries:
        entries = [("（暂无词条）", "请先向学习文档添加单词", "")]
    return entries


def clean_for_speech(text):
    """把词条 /ipa/ 词性 转成适合朗读的纯文本"""
    m = TRAIL_RE.search(text)
    if m:
        text = text[: m.start()]
    text = text.strip()
    text = text.replace("sb", "somebody").replace("sth", "something")
    text = text.replace("/", " or ")
    text = re.sub(r"\s+", " ", text).strip()
    return text
