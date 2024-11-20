import os
import torchaudio

def save_chunks(chunks, audio_id, sample_rate):
    for i, chunk in enumerate(chunks):
        torchaudio.save(
            os.path.join("chunks", f"{audio_id}_{i}.mp3"),
            chunk,
            sample_rate=sample_rate,
            format="mp3",
        )