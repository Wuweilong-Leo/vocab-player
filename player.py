# -*- coding: utf-8 -*-
"""VocabPlayer 主类:轮播、UI、鼠标交互"""
import random
import tkinter as tk
from tkinter import ttk

from config import INTERVAL_MS, TICK_MS, MIN_SEC, MAX_SEC, WIN_W, WIN_H, BG, FG_DIM, FG_ACCENT
from doc_loader import load_entries, clean_for_speech
from speech import speak as _speak
from hotkey import start_hotkey
from search import SearchBar


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
        self.interval = INTERVAL_MS
        self._controls = set()

        self._setup_window()
        self._build_ui()
        self.reload()
        start_hotkey(self.speak)
        self.tick()

    # ---------- 语音 ----------
    def speak(self):
        if not self.cur_en:
            return
        _speak(clean_for_speech(self.cur_en))

    # ---------- 窗口 ----------
    def _setup_window(self):
        r = self.root
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.96)
        r.configure(bg=BG)
        sw = r.winfo_screenwidth()
        r.geometry(f"{WIN_W}x{WIN_H}+{sw - WIN_W - 24}+24")
        r.minsize(WIN_W, WIN_H)

        self._drag_start = None
        self._drag_moved = False
        r.bind("<ButtonPress-1>", self._on_press)
        r.bind("<B1-Motion>", self._on_drag)
        r.bind("<ButtonRelease-1>", self._on_release)
        r.bind("<Button-3>", lambda e: self.prev())
        r.bind("<space>", lambda e: self.toggle_pause() if not self.search.active else None)
        r.bind("<Escape>", lambda e: self.search.clear() if self.search.active else self.quit())
        r.bind("<Button-2>", lambda e: self.toggle_pause())
        r.bind("<p>", lambda e: self.speak())
        r.bind("<P>", lambda e: self.speak())
        r.bind("<Control-f>", lambda e: self.search.entry.focus_set())
        r.bind("<Control-F>", lambda e: self.search.entry.focus_set())

    def _build_ui(self):
        r = self.root
        # ---- 顶栏 ----
        bar = tk.Frame(r, bg=BG)
        bar.pack(side="top", fill="x", padx=8, pady=(6, 0))
        self._controls.add(bar)

        self.lbl_pos = tk.Label(bar, text="", fg=FG_DIM, bg=BG,
                                font=("Segoe UI", 9))
        self.lbl_pos.pack(side="left")
        self._controls.add(self.lbl_pos)

        spk = tk.Label(bar, text="🔊", fg=FG_ACCENT, bg=BG,
                       font=("Segoe UI", 11), cursor="hand2", padx=6)
        spk.pack(side="right")
        spk.bind("<Button-1>", lambda e: self.speak())
        self._controls.add(spk)

        for txt, cmd in (("✕", self.quit), ("⏸", self.toggle_pause),
                         ("◀", self.prev), ("⇻", self.next)):
            b = tk.Label(bar, text=txt, fg=FG_DIM, bg=BG,
                         font=("Segoe UI", 11), cursor="hand2", padx=6)
            b.pack(side="right")
            b.bind("<Button-1>", lambda e, c=cmd: c())
            self._controls.add(b)

        # ---- 第二行:搜索 + 速度 ----
        spd = tk.Frame(r, bg=BG)
        spd.pack(fill="x", padx=16, pady=(0, 0))
        self._controls.add(spd)

        self.search = SearchBar(spd, self.entries,
                                on_select=self._on_search_select,
                                on_active_change=self._on_search_active)

        tk.Label(spd, text="⏱", fg="#666", bg=BG,
                 font=("Segoe UI", 9)).pack(side="left")
        self.speed_var = tk.IntVar(value=INTERVAL_MS // 1000)
        self.speed_scale = tk.Scale(spd, from_=MIN_SEC, to=MAX_SEC,
                                    orient="horizontal", variable=self.speed_var,
                                    command=self._on_speed, showvalue=True,
                                    length=200, sliderlength=18,
                                    bg=BG, fg=FG_DIM, troughcolor="#333",
                                    highlightthickness=0, bd=0,
                                    font=("Segoe UI", 8))
        self.speed_scale.pack(side="left", padx=(2, 4))
        tk.Label(spd, text="秒/词", fg="#666", bg=BG,
                 font=("Segoe UI", 9)).pack(side="left")
        self._controls.add(self.speed_scale)

        # ---- 词条内容 ----
        self.lbl_en = tk.Label(r, text="", fg="#ffffff", bg=BG,
                               font=("Segoe UI", 18, "bold"), anchor="w",
                               justify="left", wraplength=WIN_W - 32)
        self.lbl_en.pack(fill="x", padx=16, pady=(4, 0))

        self.lbl_zh = tk.Label(r, text="", fg=FG_ACCENT, bg=BG,
                               font=("Microsoft YaHei", 13), anchor="w",
                               justify="left", wraplength=WIN_W - 32)
        self.lbl_zh.pack(fill="x", padx=16)

        self.lbl_usage = tk.Label(r, text="", fg="#9aa0a6", bg=BG,
                                  font=("Microsoft YaHei", 10), anchor="w",
                                  justify="left", wraplength=WIN_W - 32)
        self.lbl_usage.pack(fill="x", padx=16)

        # ---- 底部进度条 ----
        self.bar = ttk.Progressbar(r, mode="determinate", maximum=100)
        self.bar.pack(side="bottom", fill="x")
        self.bar["value"] = 0

    # ---------- 数据 ----------
    def reload(self):
        self.entries = load_entries()
        self.search.update_entries(self.entries)
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
        if self.search.active and self.search._hits:
            return
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

    # ---------- 搜索回调 ----------
    def _on_search_select(self, entry_idx):
        """搜索选中/预览词条:更新主显示区,选中时跳转位置"""
        en, zh, usage = self.entries[entry_idx]
        self.cur_en = en
        self.lbl_en.config(text=en)
        self.lbl_zh.config(text=zh)
        self.lbl_usage.config(text=usage)
        # 选中(非预览)时跳转:搜索框 clear 后会调用,此时 _hits 已清空
        if not self.search._hits:
            if entry_idx in self.order:
                self.pos = self.order.index(entry_idx)
            self.progress = 0
            self.bar["value"] = 0
        else:
            # 预览模式:更新序号
            sel_in_hits = self.search._hits.index(entry_idx) if entry_idx in self.search._hits else 0
            self.lbl_pos.config(text=f"搜索 {sel_in_hits + 1}/{len(self.search._hits)}")

    def _on_search_active(self, active, _was_paused):
        """搜索激活状态变化:暂停/恢复轮播,返回之前的暂停状态"""
        if active:
            prev_paused = self.paused
            self.paused = True
            return prev_paused
        else:
            self.paused = _was_paused
            self.show()
            return None

    # ---------- 计时 ----------
    def _on_speed(self, val):
        self.interval = int(val) * 1000

    def tick(self):
        if not self.paused:
            self.progress += TICK_MS
            self.bar["value"] = min(100, self.progress / self.interval * 100)
            if self.progress >= self.interval:
                self.next()
        self.after_id = self.root.after(TICK_MS, self.tick)

    def quit(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

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
