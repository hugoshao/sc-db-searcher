import customtkinter as ctk
from pypinyin import lazy_pinyin
from rapidfuzz import fuzz
import pyperclip
import sys
import os
import re
import keyboard
import threading
import pyautogui

# 禁用安全保护
pyautogui.FAILSAFE = False

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
                        parts = line.strip().split("=", 1)
                        if len(parts) < 2: continue
                        value = parts[1]
                        chinese_part = value.split('[')[0].strip()
                        pinyin_list = lazy_pinyin(chinese_part)
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
            score = 0
            if query == item["first_letters"]: score = 150
            elif item["first_letters"].startswith(query): score = 120
            elif query == item["full_pinyin"]: score = 140
            elif query in item["full_pinyin"]: score = 100
            elif query in item["display"].lower(): score = 110
            
            if score > 0:
                final_score = score - (len(item["display"]) * 0.1)
                results.append((item["display"], final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [res[0] for res in results[:limit]]

class SearchApp(ctk.CTk):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.just_copied = False 
        
        # --- 窗口属性 ---
        self.title("SC Search Assistant")
        self.width = 620
        self.height = 600
        self.attributes("-toolwindow", False)
        self.center_window()
        self.attributes("-topmost", True)
        ctk.set_appearance_mode("dark")
        self.is_visible = True 

        # --- UI 布局 ---
        # 搜索框区域
        self.entry = ctk.CTkEntry(self, placeholder_text="Alt + Q 唤起，直接输入关键词...", 
                                 width=500, height=45, font=("Microsoft YaHei", 14))
        self.entry.pack(pady=(30, 5))
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<KeyRelease>", self.on_search)
        
        self.info_label = ctk.CTkLabel(self, text="左键全文 / 右键英文 | 唤起后鼠标自动定位", 
                                     font=("Microsoft YaHei", 11), text_color="gray")
        self.info_label.pack(anchor="w", padx=60)

        # 结果列表区域
        self.result_frame = ctk.CTkScrollableFrame(self, width=570, height=380)
        self.result_frame.pack(padx=10, pady=5)
        self.buttons = []

        # --- 底部控制栏 ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=10)

        self.hide_var = ctk.BooleanVar(value=False) # 默认不勾选
        self.hide_checkbox = ctk.CTkCheckBox(self.bottom_frame, text="复制后自动隐藏 (开启后按 Alt+Q 重新呼出)", 
                                            variable=self.hide_var,
                                            font=("Microsoft YaHei", 11),
                                            checkbox_width=18, checkbox_height=18)
        self.hide_checkbox.pack(side="right")

        # 启动热键监听
        threading.Thread(target=self.init_hotkeys, daemon=True).start()

    def center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.win_x = int((screen_width / 2) - (self.width / 2))
        self.win_y = int((screen_height / 2) - (self.height / 2))
        self.geometry(f"{self.width}x{self.height}+{self.win_x}+{self.win_y}")

    def init_hotkeys(self):
        keyboard.add_hotkey('alt+q', self.toggle_window)

    def toggle_window(self):
        if self.is_visible:
            self.withdraw()
            self.is_visible = False
        else:
            # 1. 唤起时自动清空输入框
            self.entry.delete(0, 'end')
            
            # 2. 安全清理旧按钮 (关键修改)
            # 先停止所有结果框的绘制，再销毁
            for btn in self.buttons:
                try:
                    if btn.winfo_exists():
                        # 重点：先解绑父容器关系，让它从绘制序列中脱离
                        btn.pack_forget() 
                        # 延迟销毁，避开当前的绘制循环
                        btn.after(10, btn.destroy)
                except:
                    pass
            self.buttons.clear()
            
            # 3. 刷新位置显示
            self.center_window()
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.focus_force() 
            
            # 4. 鼠标定位逻辑
            target_x = self.win_x + (self.width / 2)
            target_y = self.win_y + 53
            pyautogui.moveTo(target_x, target_y)
            pyautogui.click() 
            
            self.after(50, lambda: self.entry.focus_set())
            self.is_visible = True

    def on_key_press(self, event):
        if self.just_copied and event.keysym == "BackSpace":
            self.entry.delete(0, 'end')
            self.just_copied = False
            return "break"
        
    def reset_button_color(self, btn, original_text):
        try:
            if btn.winfo_exists():
                btn.configure(fg_color="transparent", text=original_text)
        except:
            pass

    def copy_logic(self, text, btn, mode="full"):
        if mode == "en":
            match = re.search(r'\[(.*?)\]', text)
            to_copy = match.group(1) if match else text
        else:
            to_copy = text
        pyperclip.copy(to_copy)
        self.just_copied = True 
        
        # 立即反馈颜色
        try:
            if btn.winfo_exists():
                btn.configure(fg_color="#2D5A27", text="✅ 已复制")
        except:
            pass
        
        if self.hide_var.get():
            # 延迟隐藏。这里直接调 toggle_window，它内部已经处理了安全清理
            self.after(300, self.toggle_window)
        else:
            # 安全复原颜色
            self.after(1000, lambda: self.reset_button_color(btn, text))

    def on_search(self, event):
        if event.keysym != "BackSpace": self.just_copied = False
        query = self.entry.get().strip()
        if not query:
            for btn in self.buttons: btn.destroy()
            self.buttons.clear()
            return

        results = self.engine.search(query)
        for btn in self.buttons: btn.destroy()
        self.buttons.clear()
        
        for text in results:
            btn = ctk.CTkButton(self.result_frame, text=text, font=("Microsoft YaHei", 13),
                                anchor="w", fg_color="transparent", hover_color="#3B3B3B", height=35)
            btn.configure(command=lambda t=text, b=btn: self.copy_logic(t, b, "full"))
            btn.bind("<Button-3>", lambda e, t=text, b=btn: self.copy_logic(t, b, "en"))
            btn.pack(fill="x", padx=5, pady=2)
            self.buttons.append(btn)

if __name__ == "__main__":
    engine = SearchEngine("data.txt")
    app = SearchApp(engine)
    app.mainloop()