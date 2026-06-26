# -*- coding: utf-8 -*-
"""
单词轮播小工具 (含按键发音)
- 从学习文档(.docx)读取词条(分类表,表头为"英文")
- 置顶无边框小窗口,10 秒自动切换,随机顺序加深印象
- 一轮播完自动重新读取文档(可拾取新增词条)并重新打乱
发音:
  - 点窗口右上角 🔊 按钮  = 朗读当前词
  - 全局热键 Ctrl+Alt+P    = 任何时候朗读当前显示的词
  - 焦点在窗口时按 P      = 朗读当前词
  (用 wscript + SAPI.SpVoice 朗读,无需安装任何依赖)
操作:
  左键单击窗口  = 下一个
  右键单击窗口  = 上一个
  左键拖动      = 移动窗口
  空格          = 暂停/继续
  Esc 或点 ×    = 退出
文档路径(优先级):
  1. 命令行参数 --doc <路径>
  2. 环境变量 VOCAB_DOC
  3. 脚本同目录下的 英语学习文档_整理版.docx
"""
import os
import re
import random
import subprocess
import threading
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk
from docx import Document

def resolve_doc():
    """按优先级解析文档路径: --doc 参数 > VOCAB_DOC 环境变量 > 同目录默认名"""
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
INTERVAL_MS = 10000
TICK_MS = 50
MIN_SEC, MAX_SEC = 3, 30   # 速度滑块范围(秒)
WIN_W, WIN_H = 640, 240

# 全局热键 Ctrl+Alt+P
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_ALT = 0x0001
VK_P = 0x50

TRAIL_RE = re.compile(
    r"(?:^|\s)/([^/]+)/(?:\s+(phr\.?v\.?|phr\.|n\.|adj\.|adv\.|v\.|phrase|句|conj\.))?\s*$", re.I
)


def load_entries():
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
    """把 col0(词条 /ipa/ 词性) 转成适合朗读的纯文本"""
    m = TRAIL_RE.search(text)
    if m:
        text = text[:m.start()]
    text = text.strip()
    text = text.replace("sb", "somebody").replace("sth", "something")
    text = text.replace("/", " or ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


class _MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD), ("pt", wintypes.POINT)]


class VocabPlayer:
    def __init__(self, root):
        self.root = root
        self.entries = []
        self.order = []
        self.pos = 0
        self.paused = False
        self.progress = 0
        self.after_id = None
        self.cur_en = ""
        self.hotkey_ok = False
        self._controls = set()   # 按钮/控件区,点击它们不触发切换/拖动
        self.interval = INTERVAL_MS  # 当前展示间隔(ms)

        self._setup_window()
        self._build_ui()
        self.reload()
        self._start_hotkey()
        self.tick()

    # ---------- 语音 ----------
    def speak(self):
        if not self.cur_en:
            return
        text = clean_for_speech(self.cur_en)
        if not text:
            return
        try:
            safe = text.replace('"', '""').replace("\n", " ")
            with open(SPEAK_VBS, "w", encoding="utf-8") as f:
                f.write('Set v = CreateObject("SAPI.SpVoice")\n')
                f.write('On Error Resume Next\n')
                f.write('v.Rate = -2\n')
                f.write('v.Speak "' + safe + '"\n')
            subprocess.Popen(["wscript.exe", "//B", "//Nologo", SPEAK_VBS],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _start_hotkey(self):
        def run():
            try:
                user32 = ctypes.windll.user32
                ok = user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT, VK_P)
                if not ok:
                    return
                self.hotkey_ok = True
                msg = _MSG()
                while True:
                    r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                    if r <= 0:
                        break
                    if msg.message == WM_HOTKEY:
                        try:
                            self.speak()
                        except Exception:
                            pass
                user32.UnregisterHotKey(None, 1)
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    # ---------- 窗口 ----------
    def _setup_window(self):
        r = self.root
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.96)
        r.configure(bg="#202028")
        sw = r.winfo_screenwidth()
        r.geometry(f"{WIN_W}x{WIN_H}+{sw - WIN_W - 24}+24")
        r.minsize(WIN_W, WIN_H)

        self._drag_start = None
        self._drag_moved = False
        r.bind("<ButtonPress-1>", self._on_press)
        r.bind("<B1-Motion>", self._on_drag)
        r.bind("<ButtonRelease-1>", self._on_release)
        r.bind("<Button-3>", lambda e: self.prev())
        r.bind("<space>", lambda e: self.toggle_pause())
        r.bind("<Escape>", lambda e: self.quit())
        r.bind("<Button-2>", lambda e: self.toggle_pause())
        r.bind("<p>", lambda e: self.speak())
        r.bind("<P>", lambda e: self.speak())

    def _build_ui(self):
        r = self.root
        bar = tk.Frame(r, bg="#202028")
        bar.pack(side="top", fill="x", padx=8, pady=(6, 0))
        self._controls.add(bar)
        # 左侧序号:当前第几个 / 共几个
        self.lbl_pos = tk.Label(bar, text="", fg="#888", bg="#202028",
                                font=("Segoe UI", 9))
        self.lbl_pos.pack(side="left")
        self._controls.add(self.lbl_pos)
        # 🔊 发音按钮放最右
        spk = tk.Label(bar, text="🔊", fg="#ffd580", bg="#202028",
                       font=("Segoe UI", 11), cursor="hand2", padx=6)
        spk.pack(side="right")
        spk.bind("<Button-1>", lambda e: self.speak())
        self._controls.add(spk)
        for txt, cmd in (("✕", self.quit), ("⏸", self.toggle_pause), ("◀", self.prev), ("⇻", self.next)):
            b = tk.Label(bar, text=txt, fg="#888", bg="#202028",
                         font=("Segoe UI", 11), cursor="hand2", padx=6)
            b.pack(side="right")
            b.bind("<Button-1>", lambda e, c=cmd: c())
            self._controls.add(b)

        # 速度滑块行
        spd = tk.Frame(r, bg="#202028")
        spd.pack(fill="x", padx=16, pady=(0, 0))
        self._controls.add(spd)
        tk.Label(spd, text="⏱", fg="#666", bg="#202028",
                 font=("Segoe UI", 9)).pack(side="left")
        self.speed_var = tk.IntVar(value=INTERVAL_MS // 1000)
        self.speed_scale = tk.Scale(spd, from_=MIN_SEC, to=MAX_SEC,
                                    orient="horizontal", variable=self.speed_var,
                                    command=self._on_speed, showvalue=True,
                                    length=200, sliderlength=18,
                                    bg="#202028", fg="#888", troughcolor="#333",
                                    highlightthickness=0, bd=0,
                                    font=("Segoe UI", 8))
        self.speed_scale.pack(side="left", padx=(2, 4))
        tk.Label(spd, text="秒/词", fg="#666", bg="#202028",
                 font=("Segoe UI", 9)).pack(side="left")
        self._controls.add(self.speed_scale)

        self.lbl_en = tk.Label(r, text="", fg="#ffffff", bg="#202028",
                              font=("Segoe UI", 18, "bold"), anchor="w",
                              justify="left", wraplength=WIN_W - 32)
        self.lbl_en.pack(fill="x", padx=16, pady=(4, 0))

        self.lbl_zh = tk.Label(r, text="", fg="#ffd580", bg="#202028",
                              font=("Microsoft YaHei", 13), anchor="w",
                              justify="left", wraplength=WIN_W - 32)
        self.lbl_zh.pack(fill="x", padx=16)

        self.lbl_usage = tk.Label(r, text="", fg="#9aa0a6", bg="#202028",
                                  font=("Microsoft YaHei", 10), anchor="w",
                                  justify="left", wraplength=WIN_W - 32)
        self.lbl_usage.pack(fill="x", padx=16)

        self.bar = ttk.Progressbar(r, mode="determinate", maximum=100)
        self.bar.pack(side="bottom", fill="x")
        self.bar["value"] = 0

    # ---------- 数据 ----------
    def reload(self):
        self.entries = load_entries()
        self.order = list(range(len(self.entries)))
        random.shuffle(self.order)
        self.pos = 0
        self.show()

    def current(self):
        if not self.order:
            return ("", "", "")
        idx = self.order[self.pos % len(self.order)]
        return self.entries[idx]

    def show(self):
        en, zh, usage = self.current()
        self.cur_en = en
        self.lbl_en.config(text=en)
        self.lbl_zh.config(text=zh)
        self.lbl_usage.config(text=usage)
        n = len(self.order)
        self.lbl_pos.config(text=f"{self.pos + 1} / {n}" if n else "")

    # ---------- 切换 ----------
    def next(self):
        self.progress = 0
        self.bar["value"] = 0
        if not self.order:
            return
        self.pos += 1
        if self.pos >= len(self.order):
            self.reload()
            return
        self.show()

    def prev(self):
        self.progress = 0
        self.bar["value"] = 0
        if not self.order:
            return
        self.pos = max(0, self.pos - 1)
        self.show()

    def toggle_pause(self):
        self.paused = not self.paused

    def _on_speed(self, val):
        self.interval = int(val) * 1000

    def quit(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

    # ---------- 计时 ----------
    def tick(self):
        if not self.paused:
            self.progress += TICK_MS
            self.bar["value"] = min(100, self.progress / self.interval * 100)
            if self.progress >= self.interval:
                self.next()
        self.after_id = self.root.after(TICK_MS, self.tick)

    # ---------- 鼠标 ----------
    def _on_press(self, e):
        if e.widget in self._controls:
            self._drag_start = None
            return
        self._drag_start = (e.x_root, e.y_root)
        self._drag_moved = False

    def _on_drag(self, e):
        if self._drag_start is None:
            return
        dx = e.x_root - self._drag_start[0]
        dy = e.y_root - self._drag_start[1]
        if abs(dx) + abs(dy) > 4:
            self._drag_moved = True
            gx = self.root.winfo_x() + dx
            gy = self.root.winfo_y() + dy
            self.root.geometry(f"+{gx}+{gy}")
            self._drag_start = (e.x_root, e.y_root)

    def _on_release(self, e):
        if e.widget in self._controls:
            self._drag_start = None
            return
        if not self._drag_moved:
            self.next()
        self._drag_start = None


def main():
    root = tk.Tk()
    root.title("VocabPlayer")
    VocabPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()