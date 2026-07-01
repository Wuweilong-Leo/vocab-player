# -*- coding: utf-8 -*-
"""模糊搜索逻辑与下拉浮层 UI"""
import tkinter as tk
from thefuzz import fuzz, process
from config import BG, FG_DIM, FG_ACCENT, SEARCH_SCORE_MIN, SEARCH_RESULT_LIMIT
from doc_loader import clean_for_speech


# 忽略导航键的 KeyRelease,避免松开↑↓时重建列表
_NAV_KEYS = frozenset(("Up", "Down", "Left", "Right", "Shift_L", "Shift_R",
                       "Control_L", "Control_r"))


class SearchBar:
    """搜索栏组件:🔍+输入框+下拉结果列表"""

    def __init__(self, parent, entries, on_select, on_active_change):
        """
        Args:
            parent: 放搜索框的 tkinter 容器
            entries: [(en, zh, usage), ...] 全部词条
            on_select: 选中词条回调 fn(entry_idx) — 选中后跳转用
            on_active_change: 搜索激活状态变化回调 fn(active: bool)
        """
        self._entries = entries
        self._on_select = on_select
        self._on_active_change = on_active_change

        self.active = False
        self._was_paused = False
        self._hits = []           # 匹配的 entry index 列表
        self._popup = None
        self._listbox = None

        # 🔍 按钮
        self.btn = tk.Label(parent, text="🔍", fg=FG_DIM, bg=BG,
                            font=("Segoe UI", 10), cursor="hand2", padx=2)
        self.btn.pack(side="left")
        # 输入框
        self.var = tk.StringVar()
        self.entry = tk.Entry(parent, textvariable=self.var,
                              bg="#333", fg="#eee", insertbackground="#eee",
                              font=("Segoe UI", 10), width=14,
                              relief="flat", bd=2)
        self.entry.pack(side="left", padx=(0, 6))
        self.entry.bind("<KeyRelease>", self._on_input)
        self.entry.bind("<Escape>", lambda e: self.clear())
        # 🔍 点击聚焦搜索框
        self.btn.bind("<Button-1>", lambda e: self.entry.focus_set())

    # ---- 公开接口 ----
    def clear(self):
        """清空搜索框,关闭下拉,恢复轮播"""
        self.var.set("")
        self.active = False
        self._hits = []
        self._destroy_popup()
        self._on_active_change(False, self._was_paused)

    def update_entries(self, entries):
        """词条刷新后更新引用"""
        self._entries = entries

    # ---- 内部逻辑 ----
    def _set_active(self):
        if not self.active:
            self.active = True
            self._was_paused = self._on_active_change(True, None)

    def _on_input(self, event=None):
        if event and event.keysym in _NAV_KEYS:
            return
        q = self.var.get().strip()
        if not q:
            if self.active:
                self.active = False
                self._hits = []
                self._destroy_popup()
                self._on_active_change(False, self._was_paused)
            return
        self._set_active()
        choices = {i: clean_for_speech(en) for i, (en, zh, usage) in enumerate(self._entries)}
        if not choices:
            return
        results = process.extract(q, choices, limit=SEARCH_RESULT_LIMIT,
                                  scorer=fuzz.partial_ratio)
        self._hits = [key for _val, score, key in results if score >= SEARCH_SCORE_MIN]
        if self._hits:
            self._show_popup()
        else:
            self._destroy_popup()

    def _destroy_popup(self):
        if self._popup:
            self._popup.destroy()
            self._popup = None
            self._listbox = None

    def _show_popup(self):
        self._destroy_popup()
        self.entry.update_idletasks()
        ex = self.entry.winfo_rootx()
        ey = self.entry.winfo_rooty() + self.entry.winfo_height() + 2

        pop = tk.Toplevel(self.entry)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg="#2a2a32")
        pop.geometry(f"+{ex}+{ey}")
        self._popup = pop

        lb = tk.Listbox(pop, bg="#2a2a32", fg="#eee", selectbackground="#505068",
                        selectforeground=FG_ACCENT, font=("Segoe UI", 10),
                        relief="flat", bd=0, highlightthickness=1,
                        highlightcolor="#555", highlightbackground="#555",
                        exportselection=False, width=40,
                        height=min(len(self._hits), 10))
        for idx in self._hits:
            en, zh, usage = self._entries[idx]
            lb.insert("end", f"{en}  {zh}" if zh else en)
        lb.pack(fill="both", padx=2, pady=2)
        lb.selection_set(0)
        lb.activate(0)
        self._listbox = lb

        def _select_entry(sel_idx):
            entry_idx = self._hits[sel_idx]
            self._on_select(entry_idx)
            self.clear()

        lb.bind("<ButtonRelease-1>", lambda e: _select_entry(lb.curselection()[0])
                if lb.curselection() else None)
        lb.bind("<Return>", lambda e: _select_entry(lb.curselection()[0])
                if lb.curselection() else None)

        # 搜索框 Enter → 选中高亮项
        self.entry.unbind("<Return>")
        self.entry.bind("<Return>", lambda e: _select_entry(lb.curselection()[0])
                        if lb.curselection() else None)

        # 搜索框 ↑↓ → 列表导航 + 实时预览(通过 on_select 回调)
        def _nav(delta):
            sel = lb.curselection()
            cur = sel[0] if sel else 0
            nxt = (cur + delta) % lb.size()
            lb.selection_clear(0, "end")
            lb.selection_set(nxt)
            lb.activate(nxt)
            lb.see(nxt)
            self._on_select(self._hits[nxt])  # 预览

        self.entry.bind("<Down>", lambda e: (_nav(1), "break")[1])
        self.entry.bind("<Up>", lambda e: (_nav(-1), "break")[1])

        # 初始预览第一项
        self._on_select(self._hits[0])
