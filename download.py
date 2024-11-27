import zmq
import boto3
from yt_dlp import YoutubeDL
import os

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = 'yt-dl-mp3'


def uploader_to_s3(file_path):
    """Uploads a file to the specified S3 bucket."""
    try:
        s3_key = os.path.relpath(file_path, start='downloads')  # Remove 'downloads/' prefix for S3 key
        s3.upload_file(file_path, BUCKET_NAME, s3_key)
        print(f"Uploaded to S3: s3://{BUCKET_NAME}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload {file_path} to S3: {e}")

def downloader():
    context = zmq.Context()
    url_receiver = context.socket(zmq.PULL)
    url_receiver.connect("tcp://localhost:5550")
    # filename_sender = context.socket(zmq.PUSH)
    # filename_sender.bind("tcp://*:5555")

    def on_complete(d):
        """Callback when a file download is complete."""
        if d['status'] == 'finished' and d['info_dict'].get('filepath') is not None:
            filename = d['info_dict']['filepath']
            if filename.endswith(".mp3"):
                print(f"Saved: {filename}")
                uploader_to_s3(filename)  # Upload the file to S3
                os.remove(filename)
                # filename_sender.send_string(filename)
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
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessor_hooks': [on_complete]
    }

    with YoutubeDL(ydl_opts) as ydl:
        print("Downloader is ready and waiting for URLs...")
        while True:
            url = url_receiver.recv_string()
            print(f"Received URL: {url}")
            try:
                ydl.download([url])
            except Exception as e:
                print(f"Error: {e}")
                continue

if __name__ == "__main__":
    downloader()
