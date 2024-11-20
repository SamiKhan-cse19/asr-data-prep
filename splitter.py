import os
import zmq
import torchaudio

CHUNKS_DIR = "chunks"

# Ensure the chunks directory exists
os.makedirs(CHUNKS_DIR, exist_ok=True)


def save_chunks(chunks, audio_id, sample_rate):
    """Save audio chunks to files."""
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(CHUNKS_DIR, f"{audio_id}_{i}.mp3")
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
        audio_id = data["audio_id"]
        chunks = data["chunks"]
        sample_rate = data["sample_rate"]

        print(f"Received data for audio_id: {audio_id}, saving {len(chunks)} chunks...")
        save_chunks(chunks, audio_id, sample_rate)


if __name__ == "__main__":
    splitter()
