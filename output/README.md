# 📁 Output Folder

This folder stores the results generated after each run of the geolocation pipeline.

---

## 📂 Structure

```

Output/
└── output_YYYYMMDD_HHMMSS/
├── \<image1_name>/
│   └── \<image1_name>_match.jpg
├── \<image2_name>/
│   └── \<image2_name>_match.jpg
└── geolocation_report.csv

```

Each run generates a new folder with a timestamp (`output_YYYYMMDD_HHMMSS`) inside the `Output/` directory.

---

## 📄 Contents

### 🔹 Match Images

- Visual representation of feature matches between:
  - Drone image
  - Reference map (TIFF or tile)
- Useful for visual verification of geolocation quality

### 🔹 `geolocation_report.csv`

This CSV file includes:

| Column Name             | Description                                      |
|-------------------------|--------------------------------------------------|
| `Image Name`            | Name of the input drone image                    |
| `Latitude`, `Longitude` | Estimated coordinates from the matched location |
| `Processing Time (HH:MM:SS)` | Time in hours:minutes:seconds               |
| `Processing Time (Seconds)`  | Time in float seconds                      |
| `Process-Status`        | Based on speed (`success`, `can be optimized`, `failure`, etc.) |
| `Status`                | `success` or `failure: <reason>`                |

---


