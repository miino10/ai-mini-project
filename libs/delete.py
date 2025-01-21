import os
import random

def delete_random_images(folder_path, num_images_to_delete):
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist")
        return
    
    image_extensions = ('.jpg', '.jpeg', '.png',)
    image_files = [f for f in os.listdir(folder_path) 
                  if os.path.isfile(os.path.join(folder_path, f)) 
                  and f.lower().endswith(image_extensions)]
    
    if len(image_files) < num_images_to_delete:
        print(f"Error: Folder only contains {len(image_files)} images, cannot delete {num_images_to_delete}")
        return
    
    images_to_delete = random.sample(image_files, num_images_to_delete)
    
    for image in images_to_delete:
        image_path = os.path.join(folder_path, image)
        try:
            os.remove(image_path)
            print(f"Deleted: {image}")
        except Exception as e:
            print(f"Error deleting {image}: {str(e)}")
    
    print(f"\nSuccessfully deleted {num_images_to_delete} images from {folder_path}")


if __name__ == "__main__":
    print("Available classes: holstein, Angus")
    folder_class = input("Enter the folder class name: ")
    
    num_images = int(input("Enter the number of images to delete: "))
    
    
    folder_path = f"./dataset/{folder_class}"
    
    delete_random_images(folder_path, num_images)