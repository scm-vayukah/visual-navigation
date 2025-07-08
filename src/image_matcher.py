import os
import cv2
import csv
import numpy as np
import time
from src.feature_extractor import extract_features

def keypoints_from_array(kparr):
    return [cv2.KeyPoint(x=float(k[0]), y=float(k[1]), _size=float(k[2]), _angle=float(k[3]),
                         _response=float(k[4]), _octave=int(k[5]), _class_id=int(k[6])) for k in kparr]

def match_drone_images(drone_folder, tiles_folder, report_path, model_name, start_time):
    bf = cv2.BFMatcher()
    drone_images = [f for f in os.listdir(drone_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    with open(report_path, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["image_name", "lat", "lon", "processing_time_hms", "processing_time_sec", "status", "process_status"])

        for img_file in drone_images:
            now = time.time()
            if now - start_time > 240:
                print("Process exceeded 4 minutes. Exiting and deleting output folder.")
                return

            image_path = os.path.join(drone_folder, img_file)
            img = cv2.imread(image_path)
            kp1, des1 = extract_features(img, model_name)
            if des1 is None or len(kp1) == 0:
                writer.writerow([img_file, "", "", "0:00:00", "0", "failure - no features", "failure"])
                continue

            best_score = 0
            best_tile = None

            for tile_file in os.listdir(tiles_folder):
                if tile_file.endswith(".npz"):
                    tile_data = np.load(os.path.join(tiles_folder, tile_file))
                    kp2 = keypoints_from_array(tile_data['kp'])
                    des2 = tile_data['desc']

                    matches = bf.knnMatch(des1, des2, k=2)
                    good = [m for m, n in matches if m.distance < 0.75 * n.distance]
                    if len(good) > best_score:
                        best_score = len(good)
                        best_tile = tile_file

            end = time.time()
            elapsed = end - now
            hms = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            status = "success" if best_score > 10 else "failure - low matches"
            proc_status = "success" if elapsed < 1 else "can be optimized 5 sec" if elapsed < 5 else "almost done" if elapsed < 10 else "failure"

            writer.writerow([img_file, "0.0000", "0.0000", hms, round(elapsed, 2), status, proc_status])
