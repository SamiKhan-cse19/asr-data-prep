import os
import zmq
import torchaudio

CHUNKS_DIR = "chunks"

# Ensure the chunks directory exists
os.makedirs(CHUNKS_DIR, exist_ok=True)


def save_chunk(chunk, audio_id, chunk_id, sample_rate):
    """Save audio chunks to files."""
    chunk_filename = os.path.join(CHUNKS_DIR, f"{audio_id}#{chunk_id}.mp3")
    torchaudio.save(
        chunk_filename,
        chunk,
        sample_rate=sample_rate,
        format="mp3",
    )
    print(f"Saved chunk: {chunk_filename}")


def splitter():
    """Split audio files based on VAD processing results."""
    context = zmq.Context()

    # Pull processed data from VAD processor
    chunk_receiver = context.socket(zmq.PULL)
    chunk_receiver.connect("tcp://localhost:5556")  # Connect to VAD Processor's PUSH

    print("Splitter is ready and waiting for VAD data...")

    while True:
        data = chunk_receiver.recv_pyobj()  # Receive data as a Python object
        try:
            audio_id = data["audio_id"]
            chunk_id = data["chunk_id"]
            chunk = data["chunk"]
            sample_rate = data["sample_rate"]

            print(f"Received chunk {chunk_id} for: {audio_id}")
            save_chunk(chunk, audio_id, chunk_id, sample_rate)
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    splitter()
