
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

```

---

