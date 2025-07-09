
<<<<<<< HEAD
# 🗺️ Tiff Folder

This folder contains the georeferenced base map image (usually an orthomosaic or satellite image) used for localizing the drone images.

---

## 🖼️ File Requirements

- Supported formats: `.tif`, `.tiff`
- File name must start with `drone` (e.g., `drone.tif`, `drone_map.tiff`)
- Must be:
  - **Orthorectified**: top-down, no distortion
  - **Georeferenced**: contains valid spatial reference info (e.g., UTM, WGS84)
  - Grayscale or RGB supported

---

## 📂 Example Structure

```

Tiff/
└── drone.tif

=======
# Tiff Folder

This folder contains a **georeferenced, stitched TIFF image**, typically generated from orthomosaics or satellite imagery. It serves as the **base map** for feature extraction and matching with drone images.

---

## Purpose

The TIFF image in this folder is used as the **reference layer**. It is:

* Divided into tiles for efficient processing.
* Used to extract and store image features.
* Compared against drone imagery for alignment or localization.

---

## Requirements

* **Only one TIFF file** should be present (e.g., `drone.tif`).
* The image must be:

  * **Georeferenced**
  * **Preferably orthorectified**
  * Either **single-band (grayscale)** or **three-band (RGB)**

---

## Processing Workflow

1. **Tiling**
   The TIFF is divided into smaller tiles (default size: **5000 × 5000 pixels**) to enable scalable matching.

2. **Export**

   * Each tile is saved as a JPEG (`.jpg`)
   * Feature descriptors are extracted from each tile and saved in a compressed `.npz` format

---

## Example Directory Structure

```
Tiff/
└── drone.tif
>>>>>>> 2c35db42cdaea25826a19cb2113b21e63b39db35
```

---

<<<<<<< HEAD
=======





>>>>>>> 2c35db42cdaea25826a19cb2113b21e63b39db35
