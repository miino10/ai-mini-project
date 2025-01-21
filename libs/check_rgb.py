import os
from PIL import Image

def check_non_rgb_images(folder_path):

    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist")
        return []
    
    image_extensions = ('.jpg', '.jpeg', '.png')
    non_rgb_images = []
    
    image_files = [f for f in os.listdir(folder_path) 
                  if os.path.isfile(os.path.join(folder_path, f)) 
                  and f.lower().endswith(image_extensions)]
    
    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    non_rgb_images.append(image_file)
                    print(f"Non-RGB image found: {image_file} (Mode: {img.mode})")
        except Exception as e:
            print(f"Error processing {image_file}: {str(e)}")
    
    return non_rgb_images

if __name__ == "__main__":
    print("Available classes: Holstein, Angus")
    folder_class = input("Enter the folder class name: ")
    
    folder_path = f"./dataset/raw/{folder_class}"
    
    non_rgb_images = check_non_rgb_images(folder_path)
    
    if non_rgb_images:
        print(f"\nFound {len(non_rgb_images)} non-RGB images in {folder_path}")
    else:
        print(f"\nAll images in {folder_path} are in RGB format") 