import zmq
from yt_dlp import YoutubeDL

def downloader():
    context = zmq.Context()
    url_receiver = context.socket(zmq.PULL)
    url_receiver.connect("tcp://localhost:5550")
    filename_sender = context.socket(zmq.PUSH)
    filename_sender.bind("tcp://*:5555")

    def on_complete(d):
        """Callback when a file download is complete."""
        if d['status'] == 'finished' and d['info_dict']['filepath'] is not None:
            filename = d['info_dict']['filepath']
            if filename.endswith(".mp3"):
                print(f"Saved: {filename}")
                filename_sender.send_string(filename)
        elif d['status'] == 'error':
            print("Download failed")
            print(d['error'])


    ydl_opts = {
        'abort_on_unavailable_fragments': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',  # You can set the quality as needed
        }],
        'postprocessor_args': [
            '-ar', '16000',  # 16 KHz sampling rate
            '-ac', '1'       # Mono Audio
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False,
        'outtmpl': 'downloads/%(channel_id)s/%(id)s.%(ext)s',
        'postprocessor_hooks': [on_complete]
    }

    with YoutubeDL(ydl_opts) as ydl:
        print("Downloader is ready and waiting for URLs...")
        while True:
            url = url_receiver.recv_string()
            print(f"Received URL: {url}")
            ydl.download([url])

if __name__ == "__main__":
    downloader()

