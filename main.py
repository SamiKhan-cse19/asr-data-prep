import zmq
from pprint import pprint
from yt_dlp import YoutubeDL

def list_videos(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # Extract only video metadata, no download
        'force_generic_extractor': False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:5550")  # Bind to send URLs to the downloader

    print("Enter YouTube URLs or playlists. Type 'exit' to quit.")
    while True:
        url = input("Enter URL: ")
        if url.lower() == 'exit':
            break
        try:
            videos = list_videos(url)
            print("Video metadata downloaded")
            if videos.get('entries') is not None:
                print(f"Found {len(videos['entries'])} videos in the URL.")
                for video in videos['entries']:
                    video_url = video['url']
                    socket.send_string(video_url)
                    print(f"Sent URL: {video_url}")
            else:
                socket.send_string(url)
                print(f"Sent URL: {url}")
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()
