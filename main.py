import zmq

def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:5550")  # Bind to send URLs to the downloader

    print("Enter YouTube URLs or playlists. Type 'exit' to quit.")
    while True:
        url = input("Enter URL: ")
        if url.lower() == 'exit':
            break
        socket.send_string(url)
        print(f"Sent URL: {url}")

if __name__ == "__main__":
    main()
