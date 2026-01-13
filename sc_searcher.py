import customtkinter as ctk
from pypinyin import lazy_pinyin
from rapidfuzz import process, fuzz
import pyperclip  # 用于复制到剪贴板
import sys
import os

class SearchEngine:
    def __init__(self, file_name="data.txt"):
        self.data = []
        
        # --- 获取内置文件路径的核心逻辑 ---
        if hasattr(sys, '_MEIPASS'):
            # 如果是打包后的 EXE 运行，文件会被解压到 sys._MEIPASS 目录下
            file_path = os.path.join(sys._MEIPASS, file_name)
        else:
            # 如果是平时的 .py 脚本运行，就在当前文件夹找
            file_path = os.path.join(os.path.abspath("."), file_name)
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        _, value = line.strip().split("=", 1)
                        if len(value) > 80: continue
                        
                        # 核心修改点：
                        pinyin_list = lazy_pinyin(value)
                        # 1. 提取首字母 (xbbq)
                        first_letters = "".join([w[0] for w in pinyin_list if w]).lower()
                        # 2. 提取全拼 (xinbabeiqi)
                        full_pinyin = "".join(pinyin_list).lower()
                        
                        self.data.append({
                            "display": value,
                            "first_letters": first_letters,
                            "full_pinyin": full_pinyin
                        })
        else:
            print(f"未找到数据文件: {file_path}")
        
    def search(self, query, limit=15):
        if not query: return []
        query = query.lower().replace(" ", "")
        results = []
        
        for item in self.data:
            display_lower = item["display"].lower()
            
            # 1. 计算基础分数
            # 使用 ratio 而不是 partial_ratio，对整体相似度更敏感
            base_score = fuzz.ratio(query, display_lower) 
            # 依然保留部分匹配，防止输入“新巴”搜不到长词
            partial_score = fuzz.partial_ratio(query, display_lower)
            
            # 2. 拼音匹配得分
            pinyin_score = 0
            if query.isalpha():
                if query == item["first_letters"]: # 首字母完全一样，给最高分
                    pinyin_score = 100
                elif query in item["first_letters"]:
                    pinyin_score = 95
                elif query == item["full_pinyin"]: # 全拼完全一样，给极高分
                    pinyin_score = 98
                elif query in item["full_pinyin"]:
                    pinyin_score = 90
                else:
                    pinyin_score = fuzz.partial_ratio(query, item["full_pinyin"]) * 0.8

            # 3. 综合得分
            final_score = max(base_score, partial_score, pinyin_score)

            # --- 关键：权重修正逻辑 ---
            # 如果 display 中包含 query，且 display 很短，给额外奖励
            # 这样 "新巴贝奇" 会比 "新巴贝奇星际空港" 多出几分奖励
            if query in display_lower or query in item["first_letters"] or query in item["full_pinyin"]:
                # 长度惩罚：目标字符串越长，减分越多 (每多一个字减 0.1 分)
                penalty = len(item["display"]) * 0.1
                final_score -= penalty
                
                # 精确匹配奖励：如果去掉括号后的中文部分和输入完全对应，大幅加分
                clean_chinese = item["display"].split('[')[0].strip()
                if query == clean_chinese:
                    final_score += 10

            if final_score > 50:
                results.append((item["display"], final_score))
        
        # 排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [res[0] for res in results[:limit]]

class SearchApp(ctk.CTk):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        
        self.title("SC 数据库搜索 (点击即可复制)")
        self.geometry("600x550")
        ctk.set_appearance_mode("dark")
        
        # 搜索框
        self.entry = ctk.CTkEntry(self, placeholder_text="输入关键词或拼音首字母...", 
                                 width=500, height=45, font=("Microsoft YaHei", 14))
        self.entry.pack(pady=20)
        self.entry.bind("<KeyRelease>", self.on_search)
        
        # 提示标签
        self.info_label = ctk.CTkLabel(self, text="搜索结果：", font=("Microsoft YaHei", 12))
        self.info_label.pack(anchor="w", padx=25)

        # 结果滚动区域
        self.result_frame = ctk.CTkScrollableFrame(self, width=550, height=400)
        self.result_frame.pack(padx=10, pady=5)
        
        self.buttons = []

    def copy_to_clipboard(self, text, btn):
        # 复制核心功能
        pyperclip.copy(text)
        
        # 视觉反馈：改变按钮颜色并显示“已复制”
        original_text = text
        btn.configure(fg_color="#2D5A27", text=f"✅ 已复制: {text}")
        
        # 1秒后恢复原样
        self.after(1000, lambda: btn.configure(fg_color="transparent", text=original_text))

    def on_search(self, event):
        query = self.entry.get().strip()
        results = self.engine.search(query)
        
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()
        
        for text in results:
            # 使用按钮替代 Label，增加点击感
            btn = ctk.CTkButton(
                self.result_frame, 
                text=text, 
                font=("Microsoft YaHei", 13),
                anchor="w",
                fg_color="transparent",
                hover_color="#3B3B3B",
                height=35,
                # 关键：使用 lambda 传递当前行的文本
                command=lambda t=text: self.copy_to_clipboard(t, btn)
            )
            # 这里需要把按钮实例存下来，否则 lambda 里的 btn 会指向最后一个
            btn.configure(command=lambda t=text, b=btn: self.copy_to_clipboard(t, b))
            
            btn.pack(fill="x", padx=5, pady=2)
            self.buttons.append(btn)

if __name__ == "__main__":
    # 确保 data.txt 在同一目录下
    engine = SearchEngine("data.txt")
    app = SearchApp(engine)
    app.mainloop()