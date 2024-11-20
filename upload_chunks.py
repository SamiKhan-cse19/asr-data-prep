from datasets import load_dataset

def upload_dataset(location="data", repo_name=None):
    dataset = load_dataset("audio_folder", data_files=location, split="train")
    if repo_name is not None:
        dataset.push_to_hub(repo_name, private=True, commit_message="initial upload")
    else:
        print("No repo_name provided. Dataset not uploaded.")