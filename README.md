# 🛰️ Drone Image Geolocation with SuperPoint

This project implements a visual geolocation system using SuperPoint-based feature matching between drone images and a georeferenced TIFF map. It estimates GPS coordinates for each drone image using keypoint matching and falls back to tile-based processing if the TIFF image is too large to load entirely.

---

## 📁 Folder Structure

```
visual-navigation/
├── main.py                 # SuperPoint geolocation pipeline
├── requirements.txt        # Python dependencies
├── Drone_images/           # Input drone images
├── Tiff/                   # Georeferenced TIFF map
└── Output/                 # Auto-generated geolocation results
```

---

## ⚙️ How It Works

1. Loads the georeferenced TIFF using GDAL.
2. If the full TIFF can't be loaded into memory, tiles it (default size: 5000x5000).
3. Uses Hugging Face `magic-leap-community/superpoint` model to extract keypoints & descriptors.
4. Matches drone image features with TIFF features using FLANN (or BF fallback).
5. Converts matched pixel location to GPS coordinates using the TIFF’s geotransform.
6. Results are saved to `Output/matched_coordinates.csv`.

---

## ✅ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/scm-vayukah/visual-navigation.git
cd visual-navigation
```

### 2. Set Up Python Environment

#### Option A: Conda (Recommended)

```bash
conda create -n locest python=3.11
conda activate locest
conda install -c conda-forge gdal=3.6.0
pip install -r requirements.txt
```

#### Option B: pip + GDAL Wheel (for Windows)

1. Download [GDAL .whl for Python 3.11](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)

2. Install:

```bash
pip install GDAL-3.10.1-cp311-cp311-win_amd64.whl
pip install -r requirements.txt
```

---

## 📦 `requirements.txt`

```
opencv-python
opencv-contrib-python
numpy
Pillow
transformers
tqdm
```

> ⚠️ Do NOT include `gdal` in `requirements.txt` if you install it via wheel or conda separately.

---

## ▶️ Usage

Run the geolocation pipeline:

```bash
python main.py --base .
```

| Argument | Description                                           |
| -------- | ----------------------------------------------------- |
| `--base` | Base directory containing `Tiff/` and `Drone_images/` |

---

## 📂 Input

### `Drone_images/`

* Contains `.jpg`, `.jpeg`, or `.png` drone images.

### `Tiff/`

* Contains a single `.tif` or `.tiff` file.
* Must be georeferenced (orthorectified) with valid geotransform metadata.

---

## 📤 Output

After each run:

```
Output/
└── matched_coordinates.csv
```

### CSV Columns

| Column           | Description                                         |
| ---------------- | --------------------------------------------------- |
| `Image`          | Drone image filename                                |
| `Latitude`       | Estimated latitude from match                       |
| `Longitude`      | Estimated longitude from match                      |
| `Time(hh:mm:ss)` | Processing time in human-readable format            |
| `Time(s)`        | Processing time in seconds                          |
| `Status`         | `success` or `failure: <reason>`                    |
| `Process_Status` | Performance classification based on processing time |

#### Process Status Categories

| Time Taken | Process Status                |
| ---------- | ----------------------------- |
| < 1 sec    | `<1 second success`           |
| < 5 sec    | `<5 seconds can be optimised` |
| < 10 sec   | `<10 seconds almost done`     |
| >= 10 sec  | `else failure`                |

---

## 🧠 Feature Matching Details

* **Keypoints & Descriptors**: Extracted using Hugging Face’s `SuperPoint` model.
* **Matcher**: FLANN-based KNN matcher (fallback to brute-force if needed).
* **Fallback Tiling**: Automatically tiles TIFF if full load fails.

---


