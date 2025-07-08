# Drone_images Folder

This folder contains individual drone-captured images used as **query images** for localization through feature matching.

---

## Purpose

These images represent real-time or pre-recorded captures from a drone camera. Each image is matched against the tiled reference map stored in the `Tiff/` folder to determine its location or alignment within the georeferenced base.

---

## Image Requirements

- **Supported formats**: `.jpg`, `.jpeg`, `.png`
- **Recommended resolution**: Medium to high (sufficient for reliable feature extraction)
- **Content**: Images should overlap with regions covered in the base TIFF map

---

## Directory Structure Example

```
Drone_images/
├── drone_001.jpg
├── drone_002.jpg
├── drone_003.jpg
└── ...
```

---

## Best Practices

- Avoid images that are:

  - Blurry
  - Overexposed or underexposed
  - Captured at extreme angles or altitudes not consistent with the base map

- Ensure the area in each image **falls within the georeferenced region** of the base TIFF map

---
