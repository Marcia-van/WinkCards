import sys
import os
import csv
import random
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

COLORS = {
    "primary": "#C9B59C",      # 燕麦卡其
    "bg": "#F8F5F2",           # 更柔和的背景白
    "card_bg": "#FFFFFF",      # 纯白卡片
    "card_shadow": "#E2DDD8",  # 阴影色
    "text_main": "#2D2926",    # 深炭灰
    "text_sub": "#706962",     # 次要文字
    "accent_green": "#A1B39F", # 雅致绿
    "accent_red": "#CF9F9D",   # 雅致红
    "highlight": "#A66242"     # 答案高亮色
}

I18N = {
    "zh": {
        "title": "眨眼闪卡 - 在眨眼之间记住所有",
        "progress": "掌握进度: {} / {} ({}%)",
        "hint": "快捷键: [空格]翻面 | [→]记住了 | [←]忘记了 | [Ctrl+滚轮]缩放",
        "btn_show": "显示答案 (空格)",
        "btn_wrong": " 忘记了 (再练练)",
        "btn_right": " 记得住 (已掌握)",
        "btn_reset": "🔄 重置进度",
        "btn_import": "📥 导入词库",
        "btn_lang": "EN / 英文",
        "welcome": "欢迎使用！\n请点击右下角导入词库。",
        "finished": "🎉 太棒了！\n已全部掌握！",
        "reset_confirm": "确定要清空背诵记录吗？",
        "reset_success": "进度已重置！",
    },
    "en": {
        "title": "BlinkCards - Minimalist Flashcards",
        "progress": "Progress: {} / {} ({}%)",
        "hint": "Keys: [Space] Flip | [→] Got it | [←] Forgot | [Ctrl+Scroll] Zoom",
        "btn_show": "Show Answer (Space)",
        "btn_wrong": " Forgot (Again)",
        "btn_right": " Learned (Mastered)",
        "btn_reset": "🔄 Reset",
        "btn_import": "📥 Import",
        "btn_lang": "中文 / CN",
        "welcome": "Welcome!\nPlease click Import to start.",
        "finished": "🎉 Brilliant!\nYou've mastered everything!",
        "reset_confirm": "Clear all progress?",
        "reset_success": "Progress Reset!",
    }
}

PROGRESS_FILE = "progress.txt"

class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.lang = "zh"
        
        # 核心数据
        self.cards = []
        self.learned_count = 0
        self.total_count = 0
        self.current_card = None
        self.is_showing_answer = False
        
        # 初始字体大小（会根据窗口动态调整）
        self.base_font_size = 48 
        self.autofiled_path = "flashcards.csv"

        self.setup_ui()
        self.bind_events()
        
        # 窗口最大化
        try:
            self.root.state('zoomed')
        except:
            self.root.geometry("1200x800")

        if os.path.exists(self.autofiled_path):
            self.load_csv(self.autofiled_path)
        else:
            self.refresh_ui_text()

    def setup_ui(self):
        """构建更大气、全屏适配的UI结构"""
        self.root.configure(bg=COLORS["bg"])
        
        # 顶部栏
        self.header = tk.Frame(self.root, bg=COLORS["bg"])
        self.header.pack(fill=tk.X, padx=60, pady=(30, 10))
        
        self.progress_var = tk.StringVar()
        # 调大进度文字：16 -> 22
        self.progress_label = tk.Label(self.header, textvariable=self.progress_var, font=("Microsoft YaHei", 22), bg=COLORS["bg"], fg=COLORS["text_main"])
        self.progress_label.pack(side=tk.LEFT)
        
        # 调大语言切换按钮文字：12 -> 16
        self.lang_btn = tk.Button(self.header, command=self.toggle_language, font=("Microsoft YaHei", 16), 
                                  bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=20, pady=8)
        self.lang_btn.pack(side=tk.RIGHT)

        # 进度条 (根据窗口宽度自适应)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        # 增加进度条厚度：12 -> 18
        self.style.configure("Custom.Horizontal.TProgressbar", thickness=18, troughcolor=COLORS["card_shadow"], background=COLORS["primary"])
        self.pb = ttk.Progressbar(self.root, style="Custom.Horizontal.TProgressbar", mode='determinate')
        self.pb.pack(fill=tk.X, padx=60, pady=(0, 30))

        # 核心卡片容器
        self.card_outer = tk.Frame(self.root, bg=COLORS["card_shadow"], padx=2, pady=2)
        self.card_outer.pack(expand=True, fill=tk.BOTH, padx=80, pady=20)
        
        self.card_inner = tk.Frame(self.card_outer, bg=COLORS["card_bg"], cursor="hand2")
        self.card_inner.pack(expand=True, fill=tk.BOTH)
        self.card_inner.bind("<Button-1>", lambda e: self.toggle_card())

        # 主显示标签：使用大字号，支持动态缩放
        self.display_label = tk.Label(
            self.card_inner, 
            text="", 
            font=("Microsoft YaHei", self.base_font_size, "bold"),
            bg=COLORS["card_bg"],
            fg=COLORS["text_main"],
            justify=tk.CENTER
        )
        self.display_label.pack(expand=True, padx=60, pady=60)

        # 控制区域
        self.ctrl_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.ctrl_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=50)

        # 调大主翻页按钮文字：18 -> 24
        self.btn_flip = tk.Button(self.ctrl_frame, command=self.toggle_card, font=("Microsoft YaHei", 24),
                                bg=COLORS["primary"], fg=COLORS["text_main"], relief=tk.FLAT, width=35, height=2)
        self.btn_flip.pack(pady=5)

        self.feedback_box = tk.Frame(self.ctrl_frame, bg=COLORS["bg"])
        # 调大反馈按钮文字：16 -> 22
        self.btn_forget = tk.Button(self.feedback_box, command=self.click_wrong, bg=COLORS["accent_red"], 
                                   fg=COLORS["text_main"], relief=tk.FLAT, width=20, height=2, font=("Microsoft YaHei", 22))
        self.btn_forget.pack(side=tk.LEFT, padx=30)
        
        self.btn_gotit = tk.Button(self.feedback_box, command=self.click_right, bg=COLORS["accent_green"], 
                                  fg=COLORS["text_main"], relief=tk.FLAT, width=20, height=2, font=("Microsoft YaHei", 22))
        self.btn_gotit.pack(side=tk.LEFT, padx=30)

# === 底部小工具栏 ===
        self.tool_bar = tk.Frame(self.root, bg=COLORS["bg"])
        self.tool_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=60, pady=(0, 20))
        
        # 1. 调大“重置进度”按钮字号：从 16 调大到 20
        self.reset_btn = tk.Button(self.tool_bar, command=self.reset_progress, font=("Microsoft YaHei", 20), bg=COLORS["bg"], 
                                  fg=COLORS["text_sub"], relief=tk.FLAT)
        self.reset_btn.pack(side=tk.LEFT)
        
        # 2. 调大“导入词库”按钮字号：从 16 调大到 20
        self.import_btn = tk.Button(self.tool_bar, command=self.manual_import, font=("Microsoft YaHei", 20, "bold"), 
                                   bg=COLORS["bg"], fg=COLORS["text_main"], relief=tk.FLAT)
        self.import_btn.pack(side=tk.RIGHT)

        # 3. 调大中间的“快捷键提示”字号：从 15 调大到 18
        self.hint_label = tk.Label(self.root, text="", font=("Microsoft YaHei", 18), bg=COLORS["bg"], fg=COLORS["text_sub"])
        self.hint_label.pack(side=tk.BOTTOM, pady=5)

    def on_window_resize(self, event):
        """当窗口大小改变时，动态调整字体和换行宽度"""
        if event.widget == self.root:
            win_w = event.width
            win_h = event.height
            
            new_size = max(24, int(win_w / 35))
            self.base_font_size = new_size
            
            self.display_label.config(wraplength=int(win_w * 0.7))
            
            if self.current_card:
                if self.is_showing_answer:
                    self.show_answer_ui()
                else:
                    self.display_label.config(font=("Microsoft YaHei", self.base_font_size, "bold"))
            elif not self.cards:
                self.display_label.config(font=("Microsoft YaHei", self.base_font_size, "bold"))

    def refresh_ui_text(self):
        """切换语言并刷新文案"""
        t = I18N[self.lang]
        self.root.title(t["title"])
        self.lang_btn.config(text=t["btn_lang"])
        self.btn_flip.config(text=t["btn_show"])
        self.btn_forget.config(text=t["btn_wrong"])
        self.btn_gotit.config(text=t["btn_right"])
        self.reset_btn.config(text=t["btn_reset"])
        self.import_btn.config(text=t["btn_import"])
        self.hint_label.config(text=t["hint"])
        self.update_progress_display()
        
        if not self.current_card:
            self.display_label.config(text=t["welcome"])

    def toggle_language(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        self.refresh_ui_text()
        if self.is_showing_answer and self.current_card:
            self.show_answer_ui()

    def update_progress_display(self):
        t = I18N[self.lang]
        perc = int((self.learned_count / self.total_count * 100)) if self.total_count > 0 else 0
        self.progress_var.set(t["progress"].format(self.learned_count, self.total_count, perc))
        self.pb['value'] = perc

    def load_csv(self, filepath):
        try:
            learned_qs = set()
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    learned_qs = {line.strip() for line in f if line.strip()}

            self.cards = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                all_data = [row for row in reader if len(row) >= 2]
                self.total_count = len(all_data)
                for row in all_data:
                    q, a = row[0].strip(), row[1].strip()
                    if q not in learned_qs:
                        self.cards.append({"q": q, "a": a})
            
            self.learned_count = self.total_count - len(self.cards)
            self.autofiled_path = filepath
            
            if self.cards:
                self.next_card()
            else:
                self.show_finished()
            self.refresh_ui_text()
        except Exception:
            messagebox.showerror("Error", "CSV Error!")

    def next_card(self):
        if not self.cards:
            self.show_finished()
            return
        self.current_card = random.choice(self.cards)
        self.is_showing_answer = False
        self.display_label.config(text=self.current_card["q"], fg=COLORS["text_main"], font=("Microsoft YaHei", self.base_font_size, "bold"))
        self.feedback_box.pack_forget()
        self.btn_flip.pack(pady=5)
        self.update_progress_display()

    def toggle_card(self):
        if not self.current_card or self.is_showing_answer: return
        self.show_answer_ui()

    def show_answer_ui(self):
        self.is_showing_answer = True
        q = self.current_card["q"]
        a = self.current_card["a"]
        ans_size = int(self.base_font_size * 0.85)
        display = f"{q}\n\n━━━━━━━━\n\n{a}"
        self.display_label.config(text=display, fg=COLORS["highlight"], font=("Microsoft YaHei", ans_size, "bold"))
        self.btn_flip.pack_forget()
        self.feedback_box.pack(pady=5)

    def click_right(self):
        if self.current_card:
            with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
                f.write(self.current_card["q"] + "\n")
            if self.current_card in self.cards:
                self.cards.remove(self.current_card)
            self.learned_count += 1
            self.next_card()

    def click_wrong(self):
        self.next_card()

    def show_finished(self):
        self.current_card = None
        self.display_label.config(text=I18N[self.lang]["finished"], fg=COLORS["accent_green"])
        self.btn_flip.pack_forget()
        self.feedback_box.pack_forget()
        self.update_progress_display()

    def reset_progress(self):
        if messagebox.askyesno("Reset", I18N[self.lang]["reset_confirm"]):
            if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
            self.load_csv(self.autofiled_path)

    def manual_import(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path: self.load_csv(path)

    def bind_events(self):
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.bind("<space>", lambda e: self.toggle_card())
        self.root.bind("<Right>", lambda e: self.click_right() if self.is_showing_answer else self.toggle_card())
        self.root.bind("<Left>", lambda e: self.click_wrong() if self.is_showing_answer else self.toggle_card())
        self.root.bind("<Control-MouseWheel>", self.zoom_font)

    def zoom_font(self, event):
        delta = 4 if event.delta > 0 else -4
        self.base_font_size = max(16, min(120, self.base_font_size + delta))
        current_font = ("Microsoft YaHei", self.base_font_size if not self.is_showing_answer else int(self.base_font_size*0.85), "bold")
        self.display_label.config(font=current_font)

if __name__ == "__main__":
    root = tk.Tk()
    
    # === 新增这行：设置软件窗口和任务栏的图标 ===
    if os.path.exists("app_logo.ico"):
        root.iconbitmap("app_logo.ico")
        
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) 
    except:
        pass
    app = FlashcardApp(root)
    root.mainloop()