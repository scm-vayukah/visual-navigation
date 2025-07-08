# Drone Image Geolocation

This project implements a visual localization system for drones. It estimates the drone's position by matching live or recorded drone images against a georeferenced base map image (TIFF). The system supports multiple feature detectors such as SIFT, ORB, and CUDA ORB.

---

## Folder Structure

```
visual-navigation/
├── main.py
├── requirements.txt
├── Drone_images/
│ └── README.md
├── Tiff/
│ └── README.md
└── src/
 ├── feature_extractor.py
 ├── image_matcher.py
 ├── tiff_tiler.py
 └── utils.py

```

---

## How It Works

1. A large georeferenced TIFF image (orthomosaic or satellite image) is loaded and tiled into smaller square images.
2. Features are extracted from each tile using the selected algorithm.
3. For each drone image in the `Drone_images/` folder, the system attempts to find the best match among all the tiles.
4. Match scores and metadata (including processing time and success/failure) are written to a CSV report.
5. The process stops automatically if the total runtime exceeds 4 minutes.

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/scm-vayukah/visual-navigation.git
cd visual-navigation
```

---

### Step 2: Set Up the Python Environment

#### Option A: Using Conda (Recommended for Windows)

```bash
conda create -n locest python=3.11
conda activate locest
conda install -c conda-forge gdal=3.6.0
pip install -r requirements.txt
```

#### Option B: Using pip with Prebuilt GDAL Wheel (Windows + Python 3.11)

1. Download the appropriate GDAL `.whl` file from the link below:

   [Click here to open GDAL wheels for Windows (py311)](https://wheelhouse.openquake.org/v3/windows/py311/)

   Example file:
   `GDAL-3.10.1-cp311-cp311-win_amd64.whl`

2. Install the GDAL wheel:

```bash
pip install GDAL-3.10.1-cp311-cp311-win_amd64.whl
```

3. Then install the remaining dependencies:

```bash
pip install -r requirements.txt
```

---

### Step 3: Verify Installation

Run the following to confirm GDAL and OpenCV are installed:

```bash
python -c "from osgeo import gdal; import cv2; print('GDAL and OpenCV installed successfully.')"
```

---

### requirements.txt

> If using the pip + wheel method, do **not** include `gdal` in `requirements.txt`.

```
opencv-python
opencv-contrib-python
numpy
Pillow
```

---

## Running the Project

```bash
python main.py -b . -m sift -t 5000
```

### Command-Line Arguments

| Argument              | Description                                                    |
| --------------------- | -------------------------------------------------------------- |
| `-b` or `--base_path` | Path to the base folder containing `Tiff/` and `Drone_images/` |
| `-m` or `--model`     | Feature model to use: `sift`, `orb`, or `orb-cuda`             |
| `-t` or `--tile_size` | Tile size in pixels (default: 5000)                            |

---

## Input Folders

### Drone_images/

Contains the input drone-captured images to be localized.

**Example:**

```
Drone_images/
├── img_1.jpg
├── img_2.jpg
└── img_3.jpg
```

- Supported formats: `.jpg`, `.jpeg`, `.png`
- Avoid blurry, overexposed, or misaligned images

See `Drone_images/README.md` for more information.

---

### Tiff/

Contains a single georeferenced TIFF file used as the reference map.

**Example:**

```
Tiff/
└── drone.tif
```

- Must be orthorectified and georeferenced
- Can be grayscale or RGB

See `Tiff/README.md` for more information.

---

## Output

Each run generates a timestamped output directory:

```
output_YYYYMMDD_HHMMSS/
├── tiles/
│   ├── tile_0_0.jpg
│   ├── tile_0_0.jpg.npz
│   └── ...
└── report/
    └── estimated_geolocation_match.csv
```

### CSV Report Columns

- `image_name`: Name of the drone image
- `lat`, `lon`: Placeholder values (can be updated with real geolocation)
- `processing_time_hms`: Time in hours, minutes, seconds
- `processing_time_sec`: Time in seconds
- `status`: Whether matching succeeded or failed
- `process_status`: One of `success`, `can be optimized`, `almost done`, `failure`

---

## Feature Matching Models

- `sift`: Scale-Invariant Feature Transform (high accuracy)
- `orb`: Oriented FAST and Rotated BRIEF (lightweight)
- `orb-cuda`: GPU-accelerated ORB (requires CUDA-capable GPU)

---
