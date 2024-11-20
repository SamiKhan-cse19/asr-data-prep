import os
import torchaudio
from yt_download import download_urls
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

urls = [
    "https://www.youtube.com/watch?v=sWhIX5A-9pY",
    ]
sample_rate = 16000  

audio_files = download_urls(urls)
model = load_silero_vad()
wav = read_audio(audio_files[0], sampling_rate=sample_rate)

speech_timestamps = get_speech_timestamps(
    wav,
    model,
    threshold=0.5,
    speech_pad_ms=50,
    min_speech_duration_ms=3000,
    max_speech_duration_s=30,
    min_silence_duration_ms=600,
)

# adjust mono
if wav.dim() == 1:
    wav = wav.unsqueeze(0)

# save timestamps in mp3 files
os.makedirs("chunks", exist_ok=True)
for i, timestamp in enumerate(speech_timestamps):
    start = timestamp["start"]
    end = timestamp["end"]

    chunk = wav[:, start:end]
    torchaudio.save(
        os.path.join("chunks", f"chunk_{i}.mp3"),
        chunk,
        sample_rate=sample_rate,
        format="mp3",
    )