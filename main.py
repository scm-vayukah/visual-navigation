import os
import cv2
import csv
import time
import datetime
import shutil
import logging
import numpy as np
from osgeo import gdal

logging.basicConfig(level=logging.INFO, format="%(message)s")

def pixel_to_geo(geo_transform, px, py):
    geo_x = geo_transform[0] + px * geo_transform[1] + py * geo_transform[2]
    geo_y = geo_transform[3] + px * geo_transform[4] + py * geo_transform[5]
    return geo_x, geo_y

def save_match_visualization(img1, kp1, img2, kp2, matches, output_path):
    img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR) if len(img1.shape) == 2 else img1
    img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR) if len(img2.shape) == 2 else img2

    max_height = max(img1.shape[0], img2.shape[0])
    img1 = cv2.copyMakeBorder(img1, 0, max_height - img1.shape[0], 0, 0, cv2.BORDER_CONSTANT)
    img2 = cv2.copyMakeBorder(img2, 0, max_height - img2.shape[0], 0, 0, cv2.BORDER_CONSTANT)

    combined_img = np.hstack((img1, img2))
    for match in matches[:50]:
        pt1 = tuple(np.round(kp1[match.queryIdx].pt).astype(int))
        pt2 = tuple(np.round(kp2[match.trainIdx].pt).astype(int))
        pt2 = (pt2[0] + img1.shape[1], pt2[1])
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.line(combined_img, pt1, pt2, color, 2)
        cv2.circle(combined_img, pt1, 4, color, -1)
        cv2.circle(combined_img, pt2, 4, color, -1)
    cv2.imwrite(output_path, combined_img)

def try_load_full_tiff_image(path):
    try:
        dataset = gdal.Open(path)
        array = dataset.ReadAsArray()
        if array is None:
            return None, None, None
        image = (cv2.cvtColor(np.moveaxis(array, 0, -1), cv2.COLOR_RGB2BGR)
                 if len(array.shape) == 3 else
                 cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_GRAY2BGR))
        return image, dataset.GetGeoTransform(), dataset
    except Exception as e:
        logging.error(f"[ERROR] GDAL failed to load full image: {e}")
        return None, None, None

def tile_image_and_extract_sift(dataset, tile_size=5000):
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    geo_transform = dataset.GetGeoTransform()
    sift_detector = cv2.SIFT_create()
    tiles_features = []

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            tile_width = min(tile_size, width - x)
            tile_height = min(tile_size, height - y)
            tile_data = dataset.ReadAsArray(x, y, tile_width, tile_height)
            if tile_data is None:
                continue
            tile_image = (cv2.cvtColor(np.moveaxis(tile_data, 0, -1), cv2.COLOR_RGB2BGR)
                          if len(tile_data.shape) == 3 else
                          cv2.cvtColor(tile_data.astype(np.uint8), cv2.COLOR_GRAY2BGR))
            keypoints, descriptors = sift_detector.detectAndCompute(tile_image, None)
            if keypoints is not None and descriptors is not None:
                tiles_features.append({
                    "x": x, "y": y, "w": tile_width, "h": tile_height,
                    "kp": keypoints, "desc": descriptors, "img": tile_image
                })
    return tiles_features, geo_transform

def clean_up(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--base_path", required=True, help="Path to the dataset base directory")
    args = parser.parse_args()

    base_path = args.base_path
    tiff_dir = os.path.join(base_path, "Tiff")
    drone_dir = os.path.join(base_path, "Drone_images")

    ortho_path = next((os.path.join(tiff_dir, f) for f in os.listdir(tiff_dir)
                      if f.lower().startswith("drone") and f.lower().endswith((".tif", ".tiff"))), None)
    if not ortho_path:
        logging.error("[ERROR] No TIFF image starting with 'drone' found.")
        return

    drone_image_paths = [os.path.join(drone_dir, f) for f in os.listdir(drone_dir)
                         if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    # Prepare output structure
    main_output_dir = os.path.join(base_path, "Output")
    os.makedirs(main_output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    session_output_dir = os.path.join(main_output_dir, f"output_{timestamp}")
    os.makedirs(session_output_dir, exist_ok=True)

    sift_detector = cv2.SIFT_create()
    ortho_image, geo_transform, gdal_dataset = try_load_full_tiff_image(ortho_path)
    tile_mode = False

    if ortho_image is not None:
        try:
            ortho_keypoints, ortho_descriptors = sift_detector.detectAndCompute(ortho_image, None)
        except Exception as e:
            logging.warning(f"[WARNING] Full image feature extraction failed: {e}")
            ortho_image = None

    if ortho_image is None:
        logging.info("[INFO] Falling back to tile-based matching...")
        tile_mode = True
        gdal_dataset = gdal.Open(ortho_path)
        tile_features, geo_transform = tile_image_and_extract_sift(gdal_dataset)

    csv_output_path = os.path.join(session_output_dir, "geolocation_report.csv")

    try:
        with open(csv_output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "Image Name", "Latitude", "Longitude",
                "Processing Time (HH:MM:SS)", "Seconds", "Status", "Message"
            ])

            for drone_path in drone_image_paths:
                drone_name = os.path.splitext(os.path.basename(drone_path))[0]
                drone_output_dir = os.path.join(session_output_dir, drone_name)
                os.makedirs(drone_output_dir, exist_ok=True)

                drone_image = cv2.imread(drone_path)
                if drone_image is None:
                    logging.error(f"[ERROR] Could not read {drone_path}")
                    writer.writerow([drone_name, "", "", "", "", "Failure", "Read error"])
                    continue

                start_time = time.time()

                try:
                    drone_keypoints, drone_descriptors = sift_detector.detectAndCompute(drone_image, None)
                    if drone_descriptors is None:
                        raise ValueError("No descriptors in drone image")

                    best_coordinates = (0.0, 0.0)
                    best_matches = []
                    best_score = 0
                    matched_kp = None
                    matched_image = None

                    if not tile_mode:
                        matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
                        matches = matcher.knnMatch(ortho_descriptors, drone_descriptors, k=2)
                        good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]

                        if len(good_matches) >= 4:
                            src_pts = np.float32([ortho_keypoints[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                            dst_pts = np.float32([drone_keypoints[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                            homography, _ = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
                            center_point = np.array([[[drone_image.shape[1] / 2, drone_image.shape[0] / 2]]], dtype=np.float32)
                            mapped_point = cv2.perspectiveTransform(center_point, homography)[0][0]
                            longitude, latitude = pixel_to_geo(geo_transform, mapped_point[0], mapped_point[1])
                            save_match_visualization(ortho_image, ortho_keypoints, drone_image, drone_keypoints,
                                                     good_matches, os.path.join(drone_output_dir, f"{drone_name}_match.jpg"))
                            best_coordinates = (latitude, longitude)
                        else:
                            raise ValueError("Not enough good matches in full image")

                    else:
                        for tile in tile_features:
                            matches = cv2.BFMatcher().knnMatch(tile["desc"], drone_descriptors, k=2)
                            good = [m for m, n in matches if m.distance < 0.75 * n.distance]
                            if len(good) > best_score:
                                best_score = len(good)
                                matched_kp = tile["kp"]
                                matched_image = tile["img"]
                                best_matches = good
                                best_coordinates = pixel_to_geo(geo_transform, tile["x"] + tile["w"] // 2,
                                                                tile["y"] + tile["h"] // 2)

                        if best_matches:
                            save_match_visualization(matched_image, matched_kp, drone_image, drone_keypoints,
                                                     best_matches, os.path.join(drone_output_dir, f"{drone_name}_match.jpg"))
                        else:
                            raise ValueError("Not enough good matches in tiles")

                    elapsed = time.time() - start_time
                    writer.writerow([
                        drone_name, f"{best_coordinates[0]:.6f}", f"{best_coordinates[1]:.6f}",
                        str(datetime.timedelta(seconds=int(elapsed))),
                        f"{elapsed:.2f}", "Success", "Processed successfully"
                    ])
                    logging.info(f"[{drone_name}] Done in {elapsed:.2f} seconds")

                except Exception as e:
                    elapsed = time.time() - start_time
                    writer.writerow([
                        drone_name, "", "",
                        str(datetime.timedelta(seconds=int(elapsed))),
                        f"{elapsed:.2f}", "Failure", str(e)
                    ])
                    logging.error(f"[{drone_name}] Error: {e}")

    except Exception as e:
        logging.error(f"[FATAL] {e}. Cleaning up...")
        clean_up(session_output_dir)
        return

    logging.info(f"[INFO] All done. Output stored at: {session_output_dir}")

if __name__ == "__main__":
    main()
