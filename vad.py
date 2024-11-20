SAMPLING_RATE = 16000
import torch
from save import save_chunks
torch.set_num_threads(1)

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model='silero_vad',
                                force_reload=True,
                                onnx=False)

(get_speech_timestamps,
save_audio,
read_audio,
VADIterator,
collect_chunks) = utils


import multiprocessing

vad_models = dict()

def init_model():
    pid = multiprocessing.current_process().pid
    model, _ = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model='silero_vad',
                                force_reload=False,
                                onnx=False)
    vad_models[pid] = model

def vad_process(audio_file: str):
    
    pid = multiprocessing.current_process().pid
    
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
    if wav.dim() == 1: # adjust mono to torchaudio compatible format
        wav = wav.unsqueeze(0)
    chunks = [
        wav[:, ts["start"]:ts["end"]] 
        for ts in speech_timestamps
    ]
    return {
        "audio_id": audio_id,
        "chunks": chunks,
        "sample_rate": SAMPLING_RATE
    }
