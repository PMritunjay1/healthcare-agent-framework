# download_medqa.py (Final version with corrected size calculation)

from datasets import load_dataset
import os

def download_and_verify_medqa():
    """
    Downloads the medalpaca/medical_meadow_medqa dataset, verifies
    its size and content, and saves it locally.
    """
    dataset_name = "medalpaca/medical_meadow_medqa"
    
    print(f"Loading the '{dataset_name}' dataset from Hugging Face...")
    print("(This will download if not already in the cache)...")
    
    dataset = load_dataset(dataset_name)
    
    print("\nLoad complete!")

    # --- VERIFICATION STEP ---
    print("\n" + "="*50)
    print("              DATASET VERIFICATION REPORT")
    print("="*50)

    total_rows = 0
    total_size_mb = 0

    # Iterate through all the splits in the dataset (e.g., 'train')
    for split_name, split_dataset in dataset.items():
        num_rows = len(split_dataset)
        total_rows += num_rows
        print(f"\n[INFO] The '{split_name}' split was found.")
        print(f"       It contains {num_rows:,} rows (question-answer pairs).")

        # --- CORRECTED SIZE CALCULATION ---
        # Get the size of each individual split and add it to the total
        if split_dataset.size_in_bytes:
            split_size_mb = split_dataset.size_in_bytes / (1024 * 1024)
            total_size_mb += split_size_mb
            print(f"       Size of this split in memory: {split_size_mb:.2f} MB")

    print("\n---------------------------------")
    print(f"[SUCCESS] Total verified rows in the dataset: {total_rows:,}")
    print(f"[SUCCESS] Total estimated size in memory: {total_size_mb:.2f} MB")
    print("---------------------------------")
    print("="*50)
    # --- END VERIFICATION ---
    
    
    # --- Saving the dataset locally for future offline use ---
    if not os.path.exists('datasets'):
        os.makedirs('datasets')
        
    save_path = f'./datasets/medalpaca_medqa'
    
    print(f"\nSaving pointers and metadata to '{save_path}'...")
    dataset.save_to_disk(save_path)
    print("Dataset saved successfully!")


if __name__ == "__main__":
    download_and_verify_medqa()