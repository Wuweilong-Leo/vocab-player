# Vocab Player 📖

Windows 英语单词轮播小工具，开机自动运行，定时轮播学习文档中的单词/短语，加深印象。

![Python](https://img.shields.io/badge/Python-3.14-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能

- 🔄 **自动轮播** — 随机顺序播放词条，一轮播完自动重新读取文档并打乱
- 🔊 **按键发音** — SAPI 语音朗读，支持按钮/快捷键/全局热键
- ⏱ **可调速度** — 滑块调节每个词的展示时间（3~30 秒）
- 📌 **置顶悬浮** — 无边框半透明窗口，不遮挡工作
- ▶◀ **手动切词** — 上一个/下一个按钮，左键/右键点击
- 🔢 **序号显示** — 当前第几个 / 共多少个词条
- 🔍 **模糊搜索** — 输入关键词即时模糊匹配，拼写容错
- 🚀 **开机自启** — 桌面快捷方式 + Startup 文件夹

## 操作

| 操作 | 方式 |
|------|------|
| 下一个 | 左键单击窗口 / ⇻ 按钮 |
| 上一个 | 右键单击窗口 / ◀ 按钮 |
| 移动窗口 | 左键拖动 |
| 朗读当前词 | 🔊 按钮 / P 键 / Ctrl+Alt+P |
| 暂停/继续 | 空格 / ⏸ 按钮 / 鼠标中键 |
| 搜索 | 🔍 按钮 / Ctrl+F |
| 下一个匹配 | Enter（搜索模式下） |
| 关闭搜索 | Esc / 再点 🔍 |
| 退出 | Esc / ✕ 按钮 |

## 文档格式

读取 `.docx` 文件中的词汇表，识别规则：

- 表头第一列为 `英文` 的表格会被读取
- 每行三列：`英文 /音标/ 词性` | `中文释义` | `用法；例：EN ZH`
- 支持多个分类表格（习惯用语、动词、名词、形容词副词等）

## 安装与运行

### 前置依赖

- Python 3.x + `python-docx` + `thefuzz`

```bash
pip install python-docx thefuzz
```

### 运行

```bash
# 默认：读取同目录下的 英语学习文档_整理版.docx
pythonw vocab_player.pyw

# 指定文档路径
pythonw vocab_player.pyw --doc "D:/my_vocab.docx"

# 通过环境变量
set VOCAB_DOC=D:/my_vocab.docx
pythonw vocab_player.pyw
```

### 开机自启

将快捷方式放入 `shell:startup` 文件夹：

- 目标：`C:\Python314\pythonw.exe`
- 参数：`"D:\wwl\vocab_player.pyw"`
- 起始位置：`D:\wwl`

## 配置

文档路径按以下优先级解析：

1. `--doc` 命令行参数
2. `VOCAB_DOC` 环境变量
3. 脚本同目录下的 `英语学习文档_整理版.docx`

## 搭配技能

本项目搭配两个 Claude Code 技能使用：

- **vocab-logger** — 提出新词自动查义/音标/词性/用法/例句并追加到学习文档
- **vocab-quiz** — 随机出选择题+填空题，脚本判题+AI二次判断，带错题加权

技能位于 `~/.claude/skills/`，全局可用。

## 技术细节

- **发音**：`wscript.exe` + VBScript 调用 `SAPI.SpVoice` COM，无需安装额外依赖
- **搜索**：`thefuzz` 库实现 Levenshtein 距离模糊匹配，拼写容错
- **全局热键**：`ctypes.user32.RegisterHotKey` 注册 Ctrl+Alt+P
- **UI**：tkinter 无边框置顶窗口（`overrideredirect` + `-topmost`）

## License

MIT