import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import yt_dlp
import threading
import os
from typing import Dict, Optional
from datetime import timedelta
import sys
import ctypes
import json

class ThemeManager:
    DARK_MODE = {
        'bg': '#2E2E2E',
        'fg': '#FFFFFF',
        'entry_bg': '#3E3E3E',
        'button_bg': '#4A90E2',
        'progress_bg': '#404040',
        'progress_fg': '#4A90E2'
    }
    
    LIGHT_MODE = {
        'bg': '#F0F0F0',
        'fg': '#000000',
        'entry_bg': '#FFFFFF',
        'button_bg': '#4A90E2',
        'progress_bg': '#E0E0E0',
        'progress_fg': '#4A90E2'
    }

    @staticmethod
    def is_dark_mode():
        if sys.platform == 'win32':
            try:
                value = ctypes.windll.user32.GetWindowsThemeSystemProperty(
                    0x1C  # WinThemeSystemProperty.AppsUseLightTheme
                )
                return value == 0
            except Exception:
                return False
        return False

    @staticmethod
    def get_theme():
        return ThemeManager.DARK_MODE if ThemeManager.is_dark_mode() else ThemeManager.LIGHT_MODE

class YouTubeDownloader:
    def __init__(self):
        self.download_path = os.path.expanduser("~/Downloads/YouTube")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            
        self.format_specs = {
            "4K": "bestvideo[height<=2160][ext!=webm]+bestaudio[ext!=webm]/best[height<=2160][ext!=webm]",
            "1080p": "bestvideo[height<=1080][ext!=webm]+bestaudio[ext!=webm]/best[height<=1080][ext!=webm]",
            "720p": "bestvideo[height<=720][ext!=webm]+bestaudio[ext!=webm]/best[height<=720][ext!=webm]",
            "480p": "bestvideo[height<=480][ext!=webm]+bestaudio[ext!=webm]/best[height<=480][ext!=webm]",
            "Audio Only": "bestaudio[ext!=webm]/best[ext!=webm]"
        }

    def get_ydl_opts(self, quality: str, progress_hook, audio_only: bool = False) -> Dict:
        opts = {
            'format': self.format_specs.get(quality, self.format_specs['1080p']),
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4' if not audio_only else 'mp3',
            'noplaylist': True,
            'extract_flat': False,
            'quiet': False,
            'no_warnings': True,
            'restrictfilenames': True
        }

        if audio_only:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            opts['postprocessors'] = [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }]

        return opts

    def download(self, url: str, quality: str, progress_hook) -> None:
        if not url.strip():
            raise ValueError("URL cannot be empty")
            
        audio_only = quality == "Audio Only"
        ydl_opts = self.get_ydl_opts(quality, progress_hook, audio_only)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

class ModernDownloaderGUI:
    def __init__(self):
        self.downloader = YouTubeDownloader()
        self.current_download = None
        self.load_settings()  # Load settings before setting up GUI
        self.setup_gui()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except:
            self.settings = {
                'download_path': self.downloader.download_path,
                'last_quality': '1080p',
                'theme': 'system'
            }

    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Modern YouTube Downloader")
        self.root.geometry("600x500")
        self.root.minsize(600, 500)

        self.theme = ThemeManager.get_theme()
        self.setup_styles()
        self.create_menu()
        self.setup_main_frame()
        self.setup_url_frame()
        self.setup_options_frame()
        self.setup_progress_frame()
        self.setup_status_frame()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('Main.TFrame', background=self.theme['bg'])
        self.style.configure('Custom.TEntry', 
                           fieldbackground=self.theme['entry_bg'],
                           foreground=self.theme['fg'])
        self.style.configure('Custom.TButton',
                           background=self.theme['button_bg'],
                           foreground=self.theme['fg'])
        self.style.configure('Custom.Horizontal.TProgressbar',
                           background=self.theme['progress_fg'],
                           troughcolor=self.theme['progress_bg'])

    def create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Download Location", 
                            command=self.change_download_location)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_main_frame(self):
        self.main_frame = ttk.Frame(self.root, style='Main.TFrame', padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def setup_url_frame(self):
        url_frame = ttk.LabelFrame(self.main_frame, text="Video URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 20))

        self.url_entry = ttk.Entry(url_frame, width=50, style='Custom.TEntry')
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        paste_button = ttk.Button(url_frame, text="Paste", 
                                command=self.paste_url,
                                style='Custom.TButton')
        paste_button.pack(side=tk.RIGHT)

    def setup_options_frame(self):
        options_frame = ttk.LabelFrame(self.main_frame, text="Download Options", 
                                     padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 20))

        # Quality Selection
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.quality_var = tk.StringVar(value=self.settings.get('last_quality', '1080p'))
        qualities = ["4K", "1080p", "720p", "480p", "Audio Only"]
        
        self.quality_combo = ttk.Combobox(quality_frame, 
                                        textvariable=self.quality_var,
                                        values=qualities,
                                        state='readonly',
                                        width=15)
        self.quality_combo.pack(side=tk.LEFT)

        # Download Button
        self.download_button = ttk.Button(options_frame, 
                                        text="Download",
                                        command=self.start_download,
                                        style='Custom.TButton')
        self.download_button.pack(fill=tk.X, pady=(10, 0))

    def setup_progress_frame(self):
        progress_frame = ttk.LabelFrame(self.main_frame, text="Download Progress", 
                                      padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 20))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate',
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill=tk.X)

    def setup_status_frame(self):
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(self.status_frame, 
                                    text="Ready to download",
                                    wraplength=550)
        self.status_label.pack(side=tk.LEFT)

        self.cancel_button = ttk.Button(self.status_frame, 
                                      text="Cancel",
                                      command=self.cancel_download,
                                      state='disabled',
                                      style='Custom.TButton')
        self.cancel_button.pack(side=tk.RIGHT)

    def paste_url(self):
        try:
            url = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        except:
            pass

    def change_download_location(self):
        new_path = filedialog.askdirectory(
            initialdir=self.downloader.download_path,
            title="Select Download Location"
        )
        if new_path:
            self.downloader.download_path = new_path
            self.settings['download_path'] = new_path
            self.save_settings()

    def show_about(self):
        about_text = """YouTube Downloader
Version 1.0.0

A modern YouTube video downloader with support for various qualities and formats.
Built with Python, yt-dlp, and tkinter.

© 2023 Your Name"""
        messagebox.showinfo("About", about_text)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)

                if total:
                    progress = (downloaded / total) * 100
                    self.progress_var.set(progress)

                    # Format status message
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    speed_mb = speed / 1024 / 1024 if speed else 0
                    eta_str = str(timedelta(seconds=eta)) if eta else 'Unknown'

                    status = f"Downloaded: {downloaded_mb:.1f}MB of {total_mb:.1f}MB "
                    status += f"({progress:.1f}%) at {speed_mb:.1f}MB/s "
                    status += f"- ETA: {eta_str}"
                    
                    self.status_label.config(text=status)
                    self.root.update_idletasks()

            except Exception as e:
                self.status_label.config(text=f"Error updating progress: {str(e)}")

        elif d['status'] == 'finished':
            self.progress_var.set(100)
            self.status_label.config(text="Download completed! Processing file...")
            self.root.update_idletasks()

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a video URL")
            return

        self.download_button.config(state='disabled')
        self.url_entry.config(state='disabled')
        self.quality_combo.config(state='disabled')
        self.cancel_button.config(state='normal')
        
        # Save last used quality
        self.settings['last_quality'] = self.quality_var.get()
        self.save_settings()

        def run_download():
            try:
                self.downloader.download(
                    url=url,
                    quality=self.quality_var.get(),
                    progress_hook=self.progress_hook
                )
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Download completed!\nSaved to: {self.downloader.download_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Download failed: {str(e)}"))
            finally:
                self.root.after(0, self.reset_ui)

        self.current_download = threading.Thread(target=run_download, daemon=True)
        self.current_download.start()

    def cancel_download(self):
        # Implement download cancellation logic here
        self.reset_ui()
        self.status_label.config(text="Download cancelled")

    def reset_ui(self):
        self.url_entry.config(state='normal')
        self.download_button.config(state='normal')
        self.quality_combo.config(state='readonly')
        self.cancel_button.config(state='disabled')
        self.progress_var.set(0)
        self.current_download = None

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        # If running as compiled executable
        os.environ["PATH"] = os.path.join(sys._MEIPASS, "ffmpeg") + os.pathsep + os.environ["PATH"]
    
    app = ModernDownloaderGUI()
    app.run()