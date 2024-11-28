import os
import time
import boto3
import random
import torchaudio
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

s3 = boto3.client('s3')
model = load_silero_vad()
SAMPLING_RATE = 16000

def vad_process(audio_file: str):
    """Perform VAD processing on an audio file and return chunks."""
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
            "chunk": wav[:, ts["start"]:ts["end"]],
            "start_time": ts["start"] / SAMPLING_RATE,  # Convert to seconds
            "end_time": ts["end"] / SAMPLING_RATE,      # Convert to seconds
            "sample_rate": SAMPLING_RATE,
        }  
        for i, ts in enumerate(speech_timestamps)
    ]

def upload_chunk_to_s3(bucket_name, key, audio_chunk):
    """Save and upload an audio chunk as MP3 to S3."""
    local_path = f"/tmp/{key.split('/')[-1]}"
    
    # Save the chunk as MP3
    torchaudio.save(
        local_path,
        audio_chunk["chunk"],
        audio_chunk["sample_rate"],
        format='mp3',
    )
    
    # Upload to S3
    try:
        s3.upload_file(local_path, bucket_name, key)
        print(f"Uploaded {key} to {bucket_name}")
    except ClientError as e:
        print(f"Error uploading {key}: {e}")
    finally:
        os.remove(local_path)  # Cleanup local file

def get_all_files(bucket_name):
    """List all files in an S3 bucket."""
    response = s3.list_objects_v2(Bucket=bucket_name)
    files = response.get('Contents', [])
    print(f"Found {len(files)} files in bucket {bucket_name}.")
    return [file['Key'] for file in files]

def tag_file(bucket_name, key, status):
    """Tag a file with a processing status."""
    try:
        s3.put_object_tagging(
            Bucket=bucket_name,
            Key=key,
            Tagging={
                'TagSet': [
                    {'Key': 'Status', 'Value': status}
                ]
            }
        )
        print(f"Tagged {key} as {status}.")
    except ClientError as e:
        print(f"Error tagging {key}: {e}")

def download_file(bucket_name, key, local_path):
    """Download a file from S3."""
    try:
        s3.download_file(bucket_name, key, local_path)
        print(f"Downloaded {key} to {local_path}.")
    except ClientError as e:
        print(f"Error downloading {key}: {e}")

def delete_file(bucket_name, key):
    """Delete a file from S3."""
    try:
        s3.delete_object(Bucket=bucket_name, Key=key)
        print(f"Deleted {key} from {bucket_name}.")
    except ClientError as e:
        print(f"Error deleting {key}: {e}")

def process_file(bucket_name, local_path, output_bucket):
    """Process the file with VAD and upload chunks to S3 asynchronously."""
    chunks = vad_process(local_path)

    with ThreadPoolExecutor() as executor:
        futures = []
        for chunk in chunks:
            # Generate filename with start and end times
            chunk_key = f"chunks/{chunk['audio_id']}|{int(chunk['start_time'])}|{int(chunk['end_time'])}.mp3"
            futures.append(executor.submit(upload_chunk_to_s3, output_bucket, chunk_key, chunk))
        
        # Wait for all uploads to complete
        for future in futures:
            future.result()

def main():
    input_bucket = 'yt-dl-mp3'
    output_bucket = 'yt-chunk-mp3'
    local_dir = '/tmp/'

    while True:
        all_files = get_all_files(input_bucket)
        if len(all_files) > 0:
            key = random.choice(all_files) # Pick a random file to process

            # Check if the file is already in progress or completed
            try:
                tags = s3.get_object_tagging(Bucket=input_bucket, Key=key)['TagSet']
                if tags and any(tag['Key'] == 'Status' and tag['Value'] in ['in-progress', 'completed'] for tag in tags):
                    continue
            except ClientError as e:
                print(f"Error fetching tags for {key}: {e}")
                continue

            # Tag the file as in-progress and download it
            tag_file(input_bucket, key, 'in-progress')
            
            local_path = f"{local_dir}{key.split('/')[-1]}"
            download_file(input_bucket, key, local_path)
            
            process_file(input_bucket, local_path, output_bucket)
            
            tag_file(input_bucket, key, 'completed')
            delete_file(input_bucket, key)
        else:
            print("No unprocessed files found. Sleeping...")
            time.sleep(10)

if __name__ == "__main__":
    main()