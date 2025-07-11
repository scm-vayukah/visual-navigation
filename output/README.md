
# 📁 Output Folder

This folder stores the results generated after each run of the SuperPoint-based geolocation pipeline.

---

## 📂 Structure

```
Output/
└── matched_coordinates.csv
```

The `matched_coordinates.csv` file is regenerated for **each run** and stores the geolocation output for all drone images processed in that run.

> 🗑️ If the process fails or is interrupted, the entire `Output/` folder is automatically deleted to ensure cleanup.

---

## 📄 Contents

### 🔹 `matched_coordinates.csv`

This CSV file contains the result of the geolocation pipeline for each drone image.

| Column Name             | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| `Image`                 | Name of the input drone image                        |
| `Latitude`, `Longitude` | Estimated coordinates from the best matched keypoint |
| `Time(hh:mm:ss)`        | Processing time in `HH:MM:SS` format                 |
| `Time(s)`               | Processing time in seconds (float)                   |
| `Status`                | Either `success` or `failure: <reason>`              |
| `Process_Status`        | Performance indicator based on processing time       |

---

### 🔹 `Process_Status` Values

| Time Taken  | Process Status                | Description                            |
| ----------- | ----------------------------- | -------------------------------------- |
| `< 1 sec`   | `<1 second success`           | Extremely fast and accurate            |
| `< 5 sec`   | `<5 seconds can be optimised` | Acceptable but may benefit from tuning |
| `< 10 sec`  | `<10 seconds almost done`     | Near timeout; check performance        |
| `>= 10 sec` | `else failure`                | Slow or failed due to matching issues  |

---

