import customtkinter as ctk
from pypinyin import lazy_pinyin
import pyperclip
import sys
import os
import re
import threading
import pyautogui
import msvcrt
import ctypes
import ctypes.wintypes
from tkinter import messagebox

# 禁用安全保护
pyautogui.FAILSAFE = False

# --- 单实例检测逻辑 ---
def is_already_running():
    lock_file = os.path.join(os.getenv('TEMP'), 'sc_searcher.lock')
    global f_lock
    f_lock = open(lock_file, 'w')
    try:
        msvcrt.locking(f_lock.fileno(), msvcrt.LK_NBLCK, 1)
        return False
    except IOError:
        return True

class SearchEngine:
    def __init__(self, file_name="data.txt"):
        self.data = []
        self.is_ready = False
        if hasattr(sys, '_MEIPASS'):
            self.file_path = os.path.join(sys._MEIPASS, file_name)
        else:
            self.file_path = os.path.join(os.path.abspath("."), file_name)
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
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
        self.is_ready = True

    def search(self, query, limit=12):
        if not query or not self.is_ready: return []
        query = query.lower().replace(" ", "")
        results = []
        for item in self.data:
            score = 0
            if query == item["first_letters"]: score = 200
            elif item["first_letters"].startswith(query): score = 150
            elif query in item["full_pinyin"]: score = 100
            elif query in item["display"].lower(): score = 80
            
            if score > 0:
                final_score = score - (len(item["display"]) * 0.5)
                results.append((item["display"], final_score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [res[0] for res in results[:limit]]

class SearchApp(ctk.CTk):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.just_copied = False 
        self.search_timer = None
        
        # --- 窗口基础属性 ---
        self.configure(fg_color="#242424")
        self.config(background="#242424")
        ctk.set_appearance_mode("dark")
        
        self.title("SC Search Assistant")
        self.width = 620
        self.height = 600
        self.attributes("-toolwindow", False)
        
        # --- UI 布局 ---
        self.entry = ctk.CTkEntry(self, placeholder_text="Alt + Q 唤起，直接输入关键词...", 
                                 width=500, height=45, font=("Microsoft YaHei", 14))
        self.entry.pack(pady=(30, 5))
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<KeyRelease>", self.on_search_handle)
        
        # 绑定 Alt + C (窗口内有效)
        self.bind("<Alt-c>", self.on_alt_c_pressed)
        self.bind("<Alt-C>", self.on_alt_c_pressed)
        
        self.info_label = ctk.CTkLabel(self, text="左键全文 / 右键英文 / Alt+C 第一行英文", 
                                     font=("Microsoft YaHei", 11), text_color="gray")
        self.info_label.pack(anchor="w", padx=60)

        self.result_frame = ctk.CTkScrollableFrame(self, width=570, height=380)
        self.result_frame.pack(padx=10, pady=5)
        self.buttons = []

        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=10)

        self.hide_var = ctk.BooleanVar(value=True)
        self.hide_checkbox = ctk.CTkCheckBox(self.bottom_frame, text="复制后自动隐藏 (Alt+Q 呼出)", 
                                            variable=self.hide_var, font=("Microsoft YaHei", 11),
                                            checkbox_width=18, checkbox_height=18)
        self.hide_checkbox.pack(side="right")

        # 启动原生 Win32 热键监听
        threading.Thread(target=self.init_native_hotkeys, daemon=True).start()

        # --- 启动即显示逻辑 ---
        self.is_visible = False 
        self.attributes("-alpha", 0.0) 
        self.center_window()
        self.deiconify()
        self.after(200, self.toggle_window)

    def center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.win_x = int((screen_width / 2) - (self.width / 2))
        self.win_y = int((screen_height / 2) - (self.height / 2))
        self.geometry(f"{self.width}x{self.height}+{self.win_x}+{self.win_y}")

    def init_native_hotkeys(self):
        user32 = ctypes.windll.user32
        MOD_ALT = 0x0001
        VK_Q = 0x51
        HOTKEY_ID = 99

        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT, VK_Q):
            return

        try:
            msg = ctypes.wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    if msg.wParam == HOTKEY_ID:
                        self.after(0, self.toggle_window)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def toggle_window(self):
        if self.is_visible:
            # 隐藏前预清理，防止下次打开看到清空过程
            self.attributes("-alpha", 0.0)
            self.withdraw()
            self.entry.delete(0, 'end')
            self.clear_buttons_safe()
            self.update_idletasks()
            self.is_visible = False
        else:
            self.attributes("-alpha", 0.0)
            self.center_window()
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            
            # 尝试切换为英文输入法
            try:
                hwnd = self.winfo_id()
                ctypes.windll.user32.PostMessageW(hwnd, 0x0050, 0, 0x04090409)
            except:
                pass
            
            self.update_idletasks()
            self.attributes("-alpha", 1.0)
            self.focus_force() 
            
            # 鼠标激活焦点
            target_x = self.win_x + (self.width / 2)
            target_y = self.win_y + 53
            pyautogui.moveTo(target_x, target_y)
            pyautogui.click() 
            
            self.after(100, lambda: self.entry.focus_set())
            self.is_visible = True

    def on_alt_c_pressed(self, event):
        """窗口内快捷键：复制第一行英文结果"""
        if self.buttons:
            first_btn = self.buttons[0]
            text = first_btn.cget("text")
            self.copy_logic(text, first_btn, mode="en")
        return "break"

    def clear_buttons_safe(self):
        for btn in self.buttons:
            try:
                if btn.winfo_exists():
                    btn.pack_forget()
                    btn.after(10, btn.destroy)
            except: pass
        self.buttons.clear()

    def on_key_press(self, event):
        if self.just_copied and event.keysym == "BackSpace":
            self.entry.delete(0, 'end')
            self.just_copied = False
            return "break"

    def on_search_handle(self, event):
        if event.keysym == "BackSpace": self.just_copied = False
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(150, self.execute_search)

    def execute_search(self):
        query = self.entry.get().strip()
        if not query:
            self.clear_buttons_safe()
            return
        results = self.engine.search(query)
        self.render_results(results)

    def render_results(self, results):
        self.clear_buttons_safe()
        for text in results:
            btn = ctk.CTkButton(self.result_frame, text=text, font=("Microsoft YaHei", 13),
                                anchor="w", fg_color="transparent", hover_color="#3B3B3B", height=35)
            btn.configure(command=lambda t=text, b=btn: self.copy_logic(t, b, "full"))
            btn.bind("<Button-3>", lambda e, t=text, b=btn: self.copy_logic(t, b, "en"))
            btn.pack(fill="x", padx=5, pady=2)
            self.buttons.append(btn)

    def copy_logic(self, text, btn, mode="full"):
        if mode == "en":
            match = re.search(r'\[(.*?)\]', text)
            to_copy = match.group(1) if match else text
        else:
            to_copy = text
        pyperclip.copy(to_copy)
        self.just_copied = True 
        try:
            if btn.winfo_exists():
                btn.configure(fg_color="#2D5A27", text="✅ 已复制")
        except: pass
        
        if self.hide_var.get():
            self.after(300, self.toggle_window)
        else:
            self.after(1000, lambda: self.reset_button_color(btn, text))

    def reset_button_color(self, btn, original_text):
        try:
            if btn.winfo_exists():
                btn.configure(fg_color="transparent", text=original_text)
        except: pass

if __name__ == "__main__":
    if is_already_running():
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("程序已在运行", "SC Search Assistant 已经在后台运行。\n请使用 Alt + Q 唤起。")
        root.destroy()
        sys.exit(0)
        
    engine = SearchEngine("data.txt")
    app = SearchApp(engine)
    app.mainloop()