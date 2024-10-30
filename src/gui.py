import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import os
import json
from datetime import timedelta
from .downloader import YouTubeDownloader

class ModernDownloaderGUI:
    def __init__(self):
        self.settings = {}
        self.downloader = YouTubeDownloader()
        self.load_settings()
        self.setup_gui()
        self.current_download = None

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except:
            self.settings = {
                'download_path': self.downloader.download_path,
                'last_quality': '1080p'
            }
            self.save_settings()

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f)
        except:
            pass

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("YouTube Downloader")
        self.root.geometry("500x400")
        self.root.minsize(500, 400)
        
        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Download Location", command=self.change_location)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # URL
        url_frame = ttk.LabelFrame(main, text="Video URL", padding=10)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(url_frame, text="Paste", command=self.paste_url).pack(side=tk.RIGHT)

        # Options
        opt_frame = ttk.LabelFrame(main, text="Options", padding=10)
        opt_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(opt_frame, text="Quality:").pack(side=tk.LEFT)

        self.quality = tk.StringVar(value=self.settings.get('last_quality', '1080p'))
        self.quality_combo = ttk.Combobox(opt_frame, 
                                        textvariable=self.quality,
                                        values=["1080p", "720p", "480p", "Audio Only"],
                                        state='readonly',
                                        width=15)
        self.quality_combo.pack(side=tk.LEFT, padx=5)

        self.download_btn = ttk.Button(opt_frame, 
                                     text="Download",
                                     command=self.start_download)
        self.download_btn.pack(side=tk.RIGHT)

        # Progress
        prog_frame = ttk.LabelFrame(main, text="Progress", padding=10)
        prog_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(prog_frame,
                                          variable=self.progress,
                                          maximum=100,
                                          mode='determinate')
        self.progress_bar.pack(fill=tk.X)

        # Status
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X)

        self.status = ttk.Label(status_frame, 
                              text="Ready",
                              wraplength=350)
        self.status.pack(side=tk.LEFT)

        self.cancel_btn = ttk.Button(status_frame, 
                                   text="Cancel",
                                   command=self.cancel_download,
                                   state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT)

    def paste_url(self):
        try:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.root.clipboard_get())
        except:
            pass

    def change_location(self):
        path = filedialog.askdirectory(
            initialdir=self.downloader.download_path,
            title="Select Download Location"
        )
        if path:
            self.downloader.download_path = path
            self.settings['download_path'] = path
            self.save_settings()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)

                if total:
                    progress = (downloaded / total) * 100
                    self.progress.set(progress)

                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    speed_mb = speed / 1024 / 1024 if speed else 0
                    eta_str = str(timedelta(seconds=eta)) if eta else 'Unknown'

                    status = f"{downloaded_mb:.1f}MB of {total_mb:.1f}MB "
                    status += f"({progress:.1f}%) at {speed_mb:.1f}MB/s "
                    status += f"- ETA: {eta_str}"
                    
                    self.status.config(text=status)
                    self.root.update_idletasks()

            except Exception as e:
                self.status.config(text=f"Error: {str(e)}")

        elif d['status'] == 'finished':
            self.progress.set(100)
            self.status.config(text="Processing...")
            self.root.update_idletasks()

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Error", "Enter a URL")
            return

        self.download_btn.config(state='disabled')
        self.url_entry.config(state='disabled')
        self.quality_combo.config(state='disabled')
        self.cancel_btn.config(state='normal')
        
        self.settings['last_quality'] = self.quality.get()
        self.save_settings()

        def run_download():
            try:
                self.downloader.download(
                    url=url,
                    quality=self.quality.get(),
                    progress_hook=self.progress_hook
                )
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Download complete!\nLocation: {self.downloader.download_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self.reset_ui)

        self.current_download = threading.Thread(target=run_download, daemon=True)
        self.current_download.start()

    def cancel_download(self):
        self.reset_ui()
        self.status.config(text="Cancelled")

    def reset_ui(self):
        self.url_entry.config(state='normal')
        self.download_btn.config(state='normal')
        self.quality_combo.config(state='readonly')
        self.cancel_btn.config(state='disabled')
        self.progress.set(0)
        self.current_download = None

    def run(self):
        self.root.mainloop()