

# Drone Image Geolocation using Orthoimage (SIFT + EXIF)

This project estimates the GPS coordinates of drone images by matching them against a georeferenced orthoimage using SIFT feature matching. The resulting geolocation is embedded directly into the image's EXIF metadata, and the output is saved in both `.JPG` and `.TIFF` formats.

---

## Folder Structure

```
location_estimator/
├── 720p/                   # Resized drone images at 1280x720 (input)
├── 1080p/                  # Resized drone images at 1920x1080 (input)
├── output/                 # Final geotagged outputs per version
├── ortho_image.tif         # Georeferenced input orthoimage
├── estimation.py           # Script for high-resource CPU systems
├── est.py                  # Optimized version for Raspberry Pi (low memory)
├── est1.py                 # Processes images in both 720p and 1080p folders
├── resize.py               # Script to create 720p and 1080p versions of images
├── requirements.txt        # Python package requirements
└── README.md               # Project documentation
```

---

## Input/Output Dataset

**Link to Input & Output Data**  :  [Click here](https://drive.google.com/drive/folders/16USVXG7BJE_eZ0p2p4KOHHLDbqOfbR-Z?usp=drive_link)

This folder contains:
- **Missing input data** (original drone images to be processed)
- **Output data** including `.JPG` and `.TIFF` images with GPS coordinates embedded in the EXIF metadata and overlaid on the image

---

## Script Overview

| Script          | Purpose                                                               | Platform          |
| --------------- | --------------------------------------------------------------------- | ----------------- |
| `estimation.py` | Uses full-resolution orthoimage                                       | CPU-based systems |
| `est.py`        | Uses a downsampled orthoimage to save memory                          | Raspberry Pi      |
| `est1.py`       | Automatically processes images from both `720p/` and `1080p/` folders | Raspberry Pi     |
| `resize.py`     | Converts original drone images into 720p and 1080p                    | All platforms     |

**Note**: File paths and image names are currently hardcoded. Update them in the scripts if your data or filenames change.

---

## Image Resolutions

| Name  | Size (pixels) |
| ----- | ------------- |
| 720p  | 1280 × 720    |
| 1080p | 1920 × 1080   |

---

## How to Use

### Step 1: Resize the Drone Images

To generate the resized versions of your input drone images:

```bash
python3 resize.py
```

This creates:

* `720p/drone1.JPG`, `drone2.JPG`, etc.
* `1080p/drone1.JPG`, `drone2.JPG`, etc.

---

### Step 2: Run the Location Estimation

Choose the script that matches your system:

* **For CPU systems (full ortho image):**

  ```bash
  python3 estimation.py
  ```

* **For Raspberry Pi (downsampled ortho image):**

  ```bash
  python3 est.py
  ```

* **To process all images from `720p/` and `1080p/` folders:**

  ```bash
  python3 est1.py
  ```

---

## Output Folder Structure

After processing, the `output/` folder will contain:

```
output/
├── sift_v1/
│   ├── drone1/
│   │   ├── drone1.JPG   # Image with GPS overlay + EXIF metadata
│   │   └── drone1.TIFF  # Original image with EXIF GPS
├── 720p_sift_v1/
│   └── ...
├── 1080p_sift_v1/
│   └── ...
```

Each subfolder contains:

* `.JPG`: Image with visual overlay of GPS text and embedded EXIF coordinates
* `.TIFF`: Original image format with embedded GPS metadata

---

## Features

* Uses OpenCV’s SIFT for keypoint detection and feature matching
* Matches drone image to orthoimage using FLANN-based matcher
* Calculates geolocation of the image center using homography and GDAL geotransform
* Embeds GPS coordinates into EXIF
* Displays resolution and time taken for processing

---

## Requirements

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

Make sure your system also has:

* Python 3.10+
* GDAL with development headers and Python bindings
* OpenCV (with SIFT support)
* Pillow
* NumPy
* piexif

---

