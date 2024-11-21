import os
import zmq
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

model = load_silero_vad()

SAMPLING_RATE = 16000

def vad_process(audio_file: str):
    """Perform VAD processing on an audio file."""
    audio_id = audio_file.split("/")[-1].split(".")[0]

    wav = read_audio(audio_file)
    os.remove(audio_file)  # Remove the downloaded audio file

    speech_timestamps = get_speech_timestamps(
        wav,
        model,
        threshold=0.5,
        speech_pad_ms=50,
        min_speech_duration_ms=3000,
        max_speech_duration_s=30,
        min_silence_duration_ms=600,
    )

    if wav.dim() == 1:  # Adjust mono to torchaudio-compatible format
        wav = wav.unsqueeze(0)

    return [
        {
            "audio_id": audio_id,
            "chunk_id": i,
            "chunk": wav[:, ts["start"]:ts["end"]] ,
            "sample_rate": SAMPLING_RATE,
        }  
        for i, ts in enumerate(speech_timestamps)
    ]

def vad_processor():
    """Process incoming audio files and send processed data to the next stage."""
    context = zmq.Context()

    # Pull data from the downloader
    url_receiver = context.socket(zmq.PULL)
    url_receiver.connect("tcp://localhost:5555")  # Connect to Downloader's PUSH

    # Push processed data to the splitter
    chunk_sender = context.socket(zmq.PUSH)
    chunk_sender.bind("tcp://*:5556")  # Bind for Splitter to connect

    print("VAD Processor is ready and waiting for audio files...")

    while True:
        audio_file = url_receiver.recv_string()  # Receive audio file path
        print(f"Processing VAD for: {audio_file}")
        try:
            results = vad_process(audio_file)  # Process VAD
            print("Sending chunks to splitter...")
            for result in results:
                chunk_sender.send_pyobj(result)  # Send result as a Python object to the splitter
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    vad_processor()
