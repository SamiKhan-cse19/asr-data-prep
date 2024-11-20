import zmq
import torch
from save import save_chunks
from multiprocessing import current_process

torch.set_num_threads(1)

# Load VAD model and utilities
model, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=True,
    onnx=False
)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

SAMPLING_RATE = 16000
vad_models = {}  # Store model instances per process


def init_model():
    """Initialize and store a separate VAD model for each process."""
    pid = current_process().pid
    model, _ = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False,
        onnx=False
    )
    vad_models[pid] = model


def vad_process(audio_file: str):
    """Perform VAD processing on an audio file."""
    pid = current_process().pid
    audio_id = audio_file.split("/")[-1].split(".")[0]

    with torch.no_grad():
        wav = read_audio(audio_file, sampling_rate=SAMPLING_RATE)
        speech_timestamps = get_speech_timestamps(
            wav,
            vad_models[pid],
            threshold=0.5,
            speech_pad_ms=50,
            min_speech_duration_ms=3000,
            max_speech_duration_s=30,
            min_silence_duration_ms=600,
        )
    if wav.dim() == 1:  # Adjust mono to torchaudio-compatible format
        wav = wav.unsqueeze(0)

    chunks = [wav[:, ts["start"]:ts["end"]] for ts in speech_timestamps]
    return {
        "audio_id": audio_id,
        "chunks": chunks,
        "sample_rate": SAMPLING_RATE
    }


def vad_processor():
    """Process incoming audio files and send processed data to the next stage."""
    context = zmq.Context()

    # Pull data from the downloader
    url_receiver = context.socket(zmq.PULL)
    url_receiver.connect("tcp://localhost:5555")  # Connect to Downloader's PUSH

    # Push processed data to the splitter
    chunk_sender = context.socket(zmq.PUSH)
    chunk_sender.bind("tcp://*:5556")  # Bind for Splitter to connect

    # Initialize the VAD model for the process
    init_model()

    while True:
        audio_file = url_receiver.recv_string()  # Receive audio file path
        print(f"Processing VAD for: {audio_file}")
        result = vad_process(audio_file)  # Process VAD
        chunk_sender.send_pyobj(result)  # Send result as a Python object to the splitter


if __name__ == "__main__":
    vad_processor()
