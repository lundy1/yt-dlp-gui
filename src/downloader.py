import yt_dlp
import os

class YouTubeDownloader:
    def __init__(self):
        self.download_path = os.path.expanduser("~/Downloads/YouTube")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            
        self.formats = {
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
            "Audio Only": "bestaudio[ext=m4a]/best[ext=m4a]"
        }

    def get_options(self, quality, progress_hook, audio_only=False):
        opts = {
            'format': self.formats.get(quality, self.formats['720p']),
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4' if not audio_only else 'm4a',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True
        }

        if audio_only:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]

        return opts

    def download(self, url, quality, progress_hook):
        if not url.strip():
            raise ValueError("URL cannot be empty")
            
        audio_only = quality == "Audio Only"
        opts = self.get_options(quality, progress_hook, audio_only)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])