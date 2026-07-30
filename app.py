import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import queue
from main import main as download_main


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("抖音视频批量下载工具")
        self.root.geometry("880x620")
        self.root.minsize(700, 500)

        self.stop_event = threading.Event()
        self.worker_thread = None
        self.log_queue = queue.Queue()
        self.running = False

        self.setup_ui()
        self.poll_log_queue()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # ── 左侧：配置面板 ──
        left = ttk.Frame(paned, padding=(0, 0, 10, 0))
        paned.add(left, weight=1)

        ttk.Label(left, text="⚙️ 配置", font=("", 13, "bold")).pack(anchor=tk.W, pady=(0, 10))

        cfg_frame = ttk.Frame(left)
        cfg_frame.pack(fill=tk.X)

        def add_row(parent, label, row, default, btn_text=None, btn_cmd=None):
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(parent, textvariable=var)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=(5, 5), pady=4)
            if btn_text:
                btn = ttk.Button(parent, text=btn_text, command=btn_cmd(var))
                btn.grid(row=row, column=2, padx=(0, 0), pady=4)
            setattr(self, f"var_{label[:4]}", var)
            return entry

        cfg_frame.columnconfigure(1, weight=1)

        self.var_excel = tk.StringVar(value="工作簿1.xlsx")
        ttk.Label(cfg_frame, text="Excel 文件").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(cfg_frame, textvariable=self.var_excel).grid(row=0, column=1, sticky=tk.EW, padx=(5, 5), pady=4)
        ttk.Button(cfg_frame, text="浏览", command=self.browse_excel).grid(row=0, column=2, pady=4)

        self.var_output = tk.StringVar(value="./downloads")
        ttk.Label(cfg_frame, text="输出目录").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(cfg_frame, textvariable=self.var_output).grid(row=1, column=1, sticky=tk.EW, padx=(5, 5), pady=4)
        ttk.Button(cfg_frame, text="浏览", command=self.browse_output).grid(row=1, column=2, pady=4)

        self.var_api = tk.StringVar(value="http://192.168.0.100:8080/api/hybrid/video_data")
        ttk.Label(cfg_frame, text="API 地址").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(cfg_frame, textvariable=self.var_api).grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=(5, 0), pady=4)

        self.var_interval = tk.StringVar(value="3")
        ttk.Label(cfg_frame, text="间隔(秒)").grid(row=3, column=0, sticky=tk.W, pady=4)
        ttk.Entry(cfg_frame, textvariable=self.var_interval, width=6).grid(row=3, column=1, sticky=tk.W, padx=(5, 5), pady=4)

        self.var_retries = tk.StringVar(value="3")
        ttk.Label(cfg_frame, text="重试次数").grid(row=4, column=0, sticky=tk.W, pady=4)
        ttk.Entry(cfg_frame, textvariable=self.var_retries, width=6).grid(row=4, column=1, sticky=tk.W, padx=(5, 5), pady=4)

        self.var_start = tk.StringVar(value="1")
        ttk.Label(cfg_frame, text="起始序号").grid(row=5, column=0, sticky=tk.W, pady=4)
        ttk.Entry(cfg_frame, textvariable=self.var_start, width=6).grid(row=5, column=1, sticky=tk.W, padx=(5, 5), pady=4)

        # ── 按钮 ──
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=(15, 10))

        self.btn_start = ttk.Button(btn_frame, text="▶ 开始下载", command=self.start)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = ttk.Button(btn_frame, text="■ 停止", command=self.stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT)

        # ── 进度 ──
        prog_frame = ttk.LabelFrame(left, text="进度", padding=8)
        prog_frame.pack(fill=tk.X, pady=(5, 0))

        self.progress_bar = ttk.Progressbar(prog_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(prog_frame, text="就绪")
        self.progress_label.pack(anchor=tk.W, pady=(4, 0))

        self.current_file_label = ttk.Label(prog_frame, text="", foreground="gray")
        self.current_file_label.pack(anchor=tk.W)

        # ── 右侧：日志 ──
        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        ttk.Label(right, text="📋 运行日志", font=("", 13, "bold")).pack(anchor=tk.W, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(right, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # ── 状态栏 ──
        self.status_bar = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

    # ══════════════════════════

    def browse_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")])
        if path:
            self.var_excel.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.var_output.set(path)

    # ══════════════════════════

    def start(self):
        try:
            start_num = int(self.var_start.get())
            interval = int(self.var_interval.get())
            retries = int(self.var_retries.get())
        except ValueError:
            self.log("❌ 序号、间隔、重试次数必须为整数")
            return

        config = {
            "excel_path": self.var_excel.get(),
            "output_dir": self.var_output.get(),
            "api_base": self.var_api.get(),
            "sleep_interval": interval,
            "max_retries": retries,
            "start_num": start_num,
        }

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.progress_bar["value"] = 0
        self.progress_label["text"] = "0 / ?"
        self.current_file_label["text"] = ""

        self.stop_event.clear()
        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.status_bar["text"] = "下载中..."

        self.worker_thread = threading.Thread(target=self.worker, args=(config,), daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        self.status_bar["text"] = "正在停止..."

    def worker(self, config):
        def log_callback(msg):
            self.log_queue.put(("log", msg))

        def progress_callback(current, total, filename=""):
            self.log_queue.put(("progress", current, total, filename))

        download_main(config, log_callback=log_callback, progress_callback=progress_callback, stop_event=self.stop_event)

        self.log_queue.put(("done",))

    # ══════════════════════════

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def poll_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                tag = item[0]

                if tag == "log":
                    self.log(item[1])
                elif tag == "progress":
                    _, current, total, filename = item
                    self.progress_bar["maximum"] = total
                    self.progress_bar["value"] = current
                    self.progress_label["text"] = f"{current} / {total}"
                    self.current_file_label["text"] = filename if filename else ""
                elif tag == "done":
                    self.on_finish()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_log_queue)

    def on_finish(self):
        self.running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_bar["text"] = "完成 ✅"


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
