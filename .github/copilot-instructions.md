# Copilot 指令 — SC_DB_Searcher

以下为面向 AI 编码代理的简明指南，旨在帮助你快速在本仓库中高效工作。请只陈述可从代码中直接发现的事实与示例。

## 一句话总结
- 这是一个基于 `customtkinter` 的桌面搜索工具，使用 `data.txt` 作为内置数据库，通过拼音/首字母匹配实现快速模糊搜索，支持打包为单文件 EXE（PyInstaller）。

## 关键文件与位置
- 主程序：`sc_searcher.py`（项目入口，若 README 提到 `app.py`，当前仓库以 `sc_searcher.py` 为主）
- 数据：`data.txt`（行格式 `key=value`，展示字符串包含中文与英文方括号英文简称）
- 文档：`README.md`（运行与打包示例）
- 打包与构建相关：`build.py`, `app.spec`, `SC_DB_Searcher.spec`

## 架构要点（跨文件/跨组件）
- UI 层：`SearchApp`（继承自 `customtkinter.CTk`），负责窗口、输入框、防抖、结果渲染与复制逻辑。
- 搜索层：`SearchEngine`，在后台线程加载 `data.txt`，预计算 `first_letters` 與 `full_pinyin`（通过 `pypinyin.lazy_pinyin`），再用轻量字符串匹配评分排序返回结果。
- 平台/部署差异：打包后通过 `sys._MEIPASS` 找数据文件；单实例通过在系统临时目录创建锁文件并用 `msvcrt.locking` 锁定检测。

## 项目风格与约定（针对 AI）
- 性能权衡：项目刻意避免复杂模糊库，倾向用简单、可解释的字符串规则（可见 `SearchEngine.search` 中的得分逻辑）。
- UI 交互规则：左键复制整行，右键复制方括号内的英文（参考 `copy_logic` 中的正则 `\[(.*?)\]`）。
- 线程与异步：文件加载与热键监听都在守护线程中启动，编辑 UI 时要使用安全清理（`clear_buttons_safe`）以避免异步销毁冲突。

## 运行、调试与打包要点
- 运行（开发）：在带有显示的环境中运行 `python sc_searcher.py`。
- 依赖安装示例：`pip install customtkinter rapidfuzz pypinyin pyperclip keyboard pyautogui`（README 中列出）。
- 打包示例（README）：
  ```bash
  py -m PyInstaller --noconsole --onefile --uac-admin --collect-all customtkinter --add-data "data.txt;." --name "SC_DB_Searcher" --clean sc_searcher.py
  ```
- 注意：热键监听 (`keyboard`) 在 Windows 上通常需要管理员权限或 UAC 提升；README 也建议以管理员身份运行以确保快捷键生效。

## 常见陷阱（AI 代理应注意）
- 单实例锁：不要移除 `is_already_running()`，它依赖 `msvcrt` 与 TEMP 目录。打包后路径与锁行为保持一致。
- 数据文件路径：在调试时使用相对路径，打包时通过 `sys._MEIPASS` 获取资源。请在改动前验证两种路径分支。
- 鼠标控制：`pyautogui.moveTo` + `click` 在无显示或远程桌面环境下可能失败或被阻止（`pyautogui.FAILSAFE = False` 已设置）。

## 可直接引用的代码片段与示例（用于快速修补或生成补丁）
- 拼音预处理（来自 `SearchEngine._load_data`）:
  ```py
  pinyin_list = lazy_pinyin(chinese_part)
  first_letters = "".join([w[0] for w in pinyin_list if w]).lower()
  full_pinyin = "".join(pinyin_list).lower()
  ```
- 复制逻辑（英文在方括号时只复制方括号内容）:
  ```py
  match = re.search(r'\[(.*?)\]', text)
  to_copy = match.group(1) if match else text
  pyperclip.copy(to_copy)
  ```

## 编辑与贡献指引（AI 代理应遵循）
- 保持現有的輕量匹配策略；若需要引入更复杂的模糊匹配，请同时保留并可切换回当前实现以便性能对比。
- 修改与 UI 相关代码时注意线程安全：任何对 Tkinter 控件的修改应发生在主线程或通过安全回调。
- 在改动初始化或热键代码前，确认影响范围（打包、管理员权限、单实例行为）。

---
如需我将这些内容合并为仓库内的 `.github/copilot-instructions.md`（我已创建），或者将某些段落扩展为英文/更详细示例，请告诉我需要补充的部分。反馈后我会按需迭代。
