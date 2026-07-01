# -*- coding: utf-8 -*-
"""单词轮播小工具 — 入口"""
import tkinter as tk
from player import VocabPlayer


def main():
    root = tk.Tk()
    root.title("VocabPlayer")
    VocabPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
