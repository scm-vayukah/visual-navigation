import os
from PIL import Image

# Images to resize
input_images = ["drone1.JPG", "drone2.JPG", "drone3.JPG"]

# Target resolutions
resolutions = {
    "720p": (1280, 720),
    "1080p": (1920, 1080)
}

# Create output folders if not exist
for folder in resolutions:
    os.makedirs(folder, exist_ok=True)

# Resize each image
for image_name in input_images:
    with Image.open(image_name) as img:
        for folder, size in resolutions.items():
            resized = img.resize(size, Image.Resampling.LANCZOS)
            output_path = os.path.join(folder, image_name)
            resized.save(output_path)
            print(f"Saved {output_path} ({size[0]}x{size[1]})")
