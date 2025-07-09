# Drone Image Geolocation

This project implements a drone visual localization system by matching input drone images against a georeferenced TIFF map image. It estimates GPS coordinates using SIFT-based feature matching. The system falls back to tile-based matching if the TIFF is too large to load entirely into memory.

---

## 📁 Folder Structure

```
visual-navigation/
├── main.py                 # Main geolocation pipeline 
├── requirements.txt        # Python dependencies
├── Drone_images/           # Input drone images
│   └── README.md
├── Tiff/                   # Georeferenced TIFF map
│   └── README.md
└── Output/                 # Output results per run
    └── README.md
```

---

## ⚙️ How It Works

1. The TIFF image is loaded using GDAL.
2. If full-image loading fails, it's automatically divided into tiles.
3. SIFT features are extracted from the full image or each tile.
4. For every image in `Drone_images/`, the system attempts to find the best match in the TIFF.
5. GPS coordinates are calculated from the matched location using the image transform.
6. Results (matches, images, and CSV) are saved in `Output/output_YYYYMMDD_HHMMSS/`.

---

## ✅ Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/scm-vayukah/visual-navigation.git
cd visual-navigation
```

### Step 2: Set Up Python Environment

#### Option A: Conda (Recommended)

```bash
conda create -n locest python=3.11
conda activate locest
conda install -c conda-forge gdal=3.6.0
pip install -r requirements.txt
```

#### Option B: pip + GDAL Wheel (Windows)

1. Download GDAL wheel: [OpenQuake GDAL Wheels (py311)](https://wheelhouse.openquake.org/v3/windows/py311/)


2. Install:

```bash
pip install GDAL-3.10.1-cp311-cp311-win_amd64.whl
pip install -r requirements.txt
```

### Step 3: Verify

```bash
python -c "from osgeo import gdal; import cv2; print('GDAL and OpenCV OK')"
```

---

## 📦 `requirements.txt`

```
opencv-python
opencv-contrib-python
numpy
Pillow
```

> ⚠️ Do not include `gdal` here if installed via `.whl`

---

## ▶️ Usage

```bash
python main.py -b .
```

### Arguments

| Argument            | Description                           |
| ------------------- | ------------------------------------- |
| `-b`, `--base_path` | Path with `Tiff/` and `Drone_images/` |

---

## 📂 Input Structure

### `Drone_images/`

* Contains `.jpg`, `.jpeg`, `.png`
* Avoid blurry or distorted images

### `Tiff/`

* Must contain one `drone.tif` or `drone.tiff`
* Must be georeferenced (orthorectified)

---

## 📤 Output

Each run creates:

```
Output/
└── output_YYYYMMDD_HHMMSS/
    ├── <image1>/
    │   └── img1_match.jpg
    ├── <image2>/
    │   └── img2_match.jpg
    └── geolocation_report.csv
```

### CSV Columns

* `Image Name`
* `Latitude`, `Longitude`
* `Processing Time (HH:MM:SS)`
* `Processing Time (Seconds)`
* `Process-Status`:

  * `< 1 sec` → `success`
  * `< 5 sec` → `can be optimized`
  * `< 10 sec` → `almost done`
  * `>= 10 sec` → `failure`
* `Status`:

  * `success`
  * `failure: <reason>` (e.g. file read error, no descriptors)

---

## 🔍 Feature Matching

* Uses **SIFT** (Scale-Invariant Feature Transform)
* Tile-based fallback used only if full image fails to load

---




