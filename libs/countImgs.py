import os

def count_images_in_folder(base_folder, class_name, image_extensions=None):
    if image_extensions is None:
       
        image_extensions = ['.jpg', '.jpeg', '.png']

   
    folder_path = os.path.join(base_folder, class_name)
    
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return 0

    count = 0

    
    for file_name in os.listdir(folder_path):
        
        if any(file_name.lower().endswith(ext) for ext in image_extensions):
            count += 1

    return count


base_folder = './dataset/raw'
class_name = input("Enter the class folder name (e.g., holstein, Angus): ")
num_images = count_images_in_folder(base_folder, class_name)
print(f'There are {num_images} images in the {class_name} folder.')
