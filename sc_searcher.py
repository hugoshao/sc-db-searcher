import customtkinter as ctk
from pypinyin import lazy_pinyin
from rapidfuzz import fuzz
import pyperclip
import sys
import os

class SearchEngine:
    def __init__(self, file_name="data.txt"):
        self.data = []
        if hasattr(sys, '_MEIPASS'):
            file_path = os.path.join(sys._MEIPASS, file_name)
        else:
            file_path = os.path.join(os.path.abspath("."), file_name)
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        _, value = line.strip().split("=", 1)
                        if len(value) > 80: continue
                        pinyin_list = lazy_pinyin(value)
                        first_letters = "".join([w[0] for w in pinyin_list if w]).lower()
                        full_pinyin = "".join(pinyin_list).lower()
                        self.data.append({
                            "display": value,
                            "first_letters": first_letters,
                            "full_pinyin": full_pinyin
                        })

    def search(self, query, limit=15):
        if not query: return []
        query = query.lower().replace(" ", "")
        results = []
        for item in self.data:
            display_lower = item["display"].lower()
            base_score = fuzz.ratio(query, display_lower) 
            partial_score = fuzz.partial_ratio(query, display_lower)
            pinyin_score = 0
            if query.isalpha():
                if query == item["first_letters"]: pinyin_score = 100
                elif query in item["first_letters"]: pinyin_score = 95
                elif query == item["full_pinyin"]: pinyin_score = 98
                elif query in item["full_pinyin"]: pinyin_score = 90
                else: pinyin_score = fuzz.partial_ratio(query, item["full_pinyin"]) * 0.8
            final_score = max(base_score, partial_score, pinyin_score)
            if query in display_lower or query in item["first_letters"] or query in item["full_pinyin"]:
                penalty = len(item["display"]) * 0.1
                final_score -= penalty
                clean_chinese = item["display"].split('[')[0].strip()
                if query == clean_chinese: final_score += 10
            if final_score > 50:
                results.append((item["display"], final_score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [res[0] for res in results[:limit]]

class SearchApp(ctk.CTk):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        
        # --- 核心状态开关 ---
        self.just_copied = False 
        
        self.title("SC 数据库搜索")
        self.geometry("600x550")
        ctk.set_appearance_mode("dark")
        
        self.entry = ctk.CTkEntry(self, placeholder_text="输入关键词...", 
                                 width=500, height=45, font=("Microsoft YaHei", 14))
        self.entry.pack(pady=20)
        
        # 绑定事件
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<KeyRelease>", self.on_search)
        
        self.info_label = ctk.CTkLabel(self, text="搜索结果：", font=("Microsoft YaHei", 12))
        self.info_label.pack(anchor="w", padx=25)

        self.result_frame = ctk.CTkScrollableFrame(self, width=550, height=400)
        self.result_frame.pack(padx=10, pady=5)
        self.buttons = []

    def on_key_press(self, event):
        # 只有在刚刚点击过复制，且按下的是退格键时
        if self.just_copied and event.keysym == "BackSpace":
            self.entry.delete(0, 'end')    # 一键清空
            self.just_copied = False       # 重置状态，下次按退格就是正常删字
            return "break"                 # 拦截事件，不触发 normal 搜索逻辑，保留列表

    def copy_to_clipboard(self, text, btn):
        pyperclip.copy(text)
        
        # --- 激活清空状态 ---
        self.just_copied = True 
        
        original_text = text
        btn.configure(fg_color="#2D5A27", text=f"✅ 已复制: {text}")
        self.after(1000, lambda: btn.configure(fg_color="transparent", text=original_text))

    def on_search(self, event):
        # 如果是用户在正常输入字符（非退格键导致的清空），我们需要重置状态
        # 这样能保证如果用户复制完又手动输入了一个字，退格键也会变回正常模式
        if event.keysym != "BackSpace":
            self.just_copied = False

        query = self.entry.get().strip()
        
        # 如果搜索框为空（比如被我们一键清空了），不刷新列表
        if not query:
            return

        results = self.engine.search(query)
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()
        
        for text in results:
            btn = ctk.CTkButton(
                self.result_frame, 
                text=text, 
                font=("Microsoft YaHei", 13),
                anchor="w",
                fg_color="transparent",
                hover_color="#3B3B3B",
                height=35
            )
            btn.configure(command=lambda t=text, b=btn: self.copy_to_clipboard(t, b))
            btn.pack(fill="x", padx=5, pady=2)
            self.buttons.append(btn)

if __name__ == "__main__":
    engine = SearchEngine("data.txt")
    app = SearchApp(engine)
    app.mainloop()