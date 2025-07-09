import os
import cv2
import argparse

# Define target resolutions
resolutions = {
    "720p_converted": (1280, 720),
    "1080p_converted": (1920, 1080)
}

# Supported image formats
image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]

def resize_and_save(image_path, output_path, size):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Skipping unreadable image: {image_path}")
        return
    resized = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    cv2.imwrite(output_path, resized)

def process_images(input_dir):
    input_dir = os.path.abspath(input_dir)

    # Create resolution folders inside input directory
    for folder_name in resolutions:
        os.makedirs(os.path.join(input_dir, folder_name), exist_ok=True)

    for filename in os.listdir(input_dir):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            full_image_path = os.path.join(input_dir, filename)

            for folder_name, size in resolutions.items():
                output_folder = os.path.join(input_dir, folder_name)
                output_path = os.path.join(output_folder, filename)
                resize_and_save(full_image_path, output_path, size)

    print("Resizing complete. Images saved in '720p_converted' and '1080p_converted' folders.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resize images and store in subfolders.")
    parser.add_argument("-p", "--path", required=True, help="Path to the folder containing images")
    args = parser.parse_args()

    process_images(args.path)
