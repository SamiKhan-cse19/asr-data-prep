import os
import time
from download import download_urls
from concurrent.futures import ProcessPoolExecutor, as_completed
from vad import init_model, vad_process
from save import save_chunks


def download_and_vad(url):
    audio_file = download_urls([url])[0]
    init_model()
    result = vad_process(audio_file)
    save_chunks(result["chunks"], result["audio_id"], result["sample_rate"])

NUM_PROCESS = 4
urls = [
    "https://www.youtube.com/watch?v=sWhIX5A-9pY",
    "https://www.youtube.com/watch?v=uGqvXQRK9iw",
    "https://www.youtube.com/watch?v=iWVEg1TxItI",
    "https://www.youtube.com/watch?v=5d3tzO3057o"
    ]
futures = []

start_time = time.time()
os.makedirs("chunks", exist_ok=True)

with ProcessPoolExecutor(max_workers=NUM_PROCESS, initializer=init_model) as ex:
    for url in urls:
        futures.append(ex.submit(download_and_vad, url))

for finished in as_completed(futures):
    print(finished.result())

print(f"Time taken: {time.time() - start_time:.2f} seconds")