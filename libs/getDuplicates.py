import os
import hashlib

def find_duplicates(file_class):
    
    full_path = os.path.join('./dataset/raw', file_class)
    
    hashes = {}
    duplicates = []

    for root, _, files in os.walk(full_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
                print(file_path)
                print(file_hash)
                if file_hash in hashes:
                    duplicates.append(file_path)
                else:
                    hashes[file_hash] = file_path

    
    print(f"Total duplicates found in {file_class}: {len(duplicates)}")

    
    for duplicate in duplicates:
        print(f"Duplicate found: {duplicate}")

    print(f"Number of duplicates: {len(duplicates)}")


file_class = input("Enter the file class (e.g., 'Holstein'): ")
find_duplicates(file_class)