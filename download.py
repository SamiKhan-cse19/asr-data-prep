import os
import zmq
from yt_dlp import YoutubeDL
from datetime import datetime

ydl_opts = {
        'ignoreerrors': True,
        'abort_on_unavailable_fragments': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',  # You can set the quality as needed
            'nopostoverwrites': False,  # Ensure postprocessing overwrites files if needed
        }],
        'postprocessor_args': [
            '-ar', '16000',  # 16 KHz sampling rate
            '-ac', '1'       # Mono Audio
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False,
    }

# Calculate the date one year ago in the format required by yt-dlp (YYYYMMDD)
one_year_ago = datetime.now().strftime("%Y%m%d")

def _duration_filter(info_dict, *, incomplete):
    """Filter videos longer than 20 minutes."""
    if incomplete:
        # Allow download if metadata is incomplete (e.g., during playlist processing)
        return None
    duration = info_dict.get('duration', 0)  # Duration in seconds
    if duration > 20 * 60:  # 20 minutes
        return None  # None means the video passes the filter
    return f"Video is shorter than 20 minutes ({duration} seconds)."

def download_urls(urls, location="data", apply_time_filter=True, apply_duration_filter=True):
    # os.makedirs(location, exist_ok=True)  # yt-dlp will create the directory if it doesn't exist
    ydl_opts['outtmpl'] = os.path.join(location, '%(id)s.%(ext)s')

    if apply_time_filter:
        ydl_opts['dateafter'] = one_year_ago

    if apply_duration_filter:
        ydl_opts['match_filter'] = _duration_filter
    
    for url in urls:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    return [os.path.join(location, f"{url.split('=')[-1]}.mp3") for url in urls]