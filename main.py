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

def pixel_to_geo(transform, x, y):
    geo_x = transform[0] + x * transform[1] + y * transform[2]
    geo_y = transform[3] + x * transform[4] + y * transform[5]
    return geo_x, geo_y

def save_match_image(img1, kp1, img2, kp2, matches, save_path):
    img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR) if len(img1.shape) == 2 else img1
    img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR) if len(img2.shape) == 2 else img2

    max_height = max(img1.shape[0], img2.shape[0])
    if img1.shape[0] < max_height:
        img1 = cv2.copyMakeBorder(img1, 0, max_height - img1.shape[0], 0, 0, cv2.BORDER_CONSTANT)
    if img2.shape[0] < max_height:
        img2 = cv2.copyMakeBorder(img2, 0, max_height - img2.shape[0], 0, 0, cv2.BORDER_CONSTANT)

    concat_img = np.hstack((img1, img2))
    for m in matches[:50]:
        pt1 = tuple(np.round(kp1[m.queryIdx].pt).astype(int))
        pt2 = tuple(np.round(kp2[m.trainIdx].pt).astype(int))
        pt2 = (pt2[0] + img1.shape[1], pt2[1])
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.line(concat_img, pt1, pt2, color, 2)
        cv2.circle(concat_img, pt1, 4, color, -1)
        cv2.circle(concat_img, pt2, 4, color, -1)
    cv2.imwrite(save_path, concat_img)

def try_load_full_image(path):
    try:
        ds = gdal.Open(path)
        arr = ds.ReadAsArray()
        if arr is None:
            return None, None, None
        img = (cv2.cvtColor(np.moveaxis(arr, 0, -1), cv2.COLOR_RGB2BGR)
               if len(arr.shape) == 3 else
               cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_GRAY2BGR))
        return img, ds.GetGeoTransform(), ds
    except Exception as e:
        logging.error(f"[ERROR] GDAL full image load failed: {e}")
        return None, None, None

def tile_image_and_extract_features(ds, tile_size=5000):
    width = ds.RasterXSize
    height = ds.RasterYSize
    transform = ds.GetGeoTransform()
    detector = cv2.SIFT_create()
    tiles = []

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            w = min(tile_size, width - x)
            h = min(tile_size, height - y)
            tile = ds.ReadAsArray(x, y, w, h)
            if tile is None:
                continue
            tile_rgb = (cv2.cvtColor(np.moveaxis(tile, 0, -1), cv2.COLOR_RGB2BGR)
                        if len(tile.shape) == 3 else
                        cv2.cvtColor(tile.astype(np.uint8), cv2.COLOR_GRAY2BGR))
            kp, desc = detector.detectAndCompute(tile_rgb, None)
            if kp is not None and desc is not None:
                tiles.append({
                    "x": x, "y": y, "w": w, "h": h,
                    "kp": kp, "desc": desc, "img": tile_rgb
                })
    return tiles, transform

def clean_up_output(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--base_path", required=True, help="Base path to folders")
    args = parser.parse_args()

    base_path = args.base_path
    tiff_dir = os.path.join(base_path, "Tiff")
    drone_dir = os.path.join(base_path, "Drone_images")

    ortho_path = next(
        (os.path.join(tiff_dir, f) for f in os.listdir(tiff_dir)
         if f.lower().startswith("drone") and f.lower().endswith((".tif", ".tiff"))),
        None
    )
    if ortho_path is None or not os.path.exists(ortho_path):
        print(f"[ERROR] {tiff_dir}/drone.tif or drone.tiff not found.")
        return

    drone_images = [os.path.join(drone_dir, f) for f in os.listdir(drone_dir)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    # Create output structure
    main_output = os.path.join(base_path, "Output")
    os.makedirs(main_output, exist_ok=True)
    output_base = os.path.join(main_output, f"output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(output_base, exist_ok=True)

    detector = cv2.SIFT_create()
    ortho_img, transform, ds = try_load_full_image(ortho_path)
    tile_mode = False

    if ortho_img is not None:
        try:
            ortho_kp, ortho_desc = detector.detectAndCompute(ortho_img, None)
        except Exception as e:
            logging.warning(f"[WARNING] Full image feature extraction failed: {e}")
            ortho_img = None

    if ortho_img is None:
        logging.info("[INFO] Falling back to tile-based matching...")
        tile_mode = True
        ds = gdal.Open(ortho_path)
        tiles, transform = tile_image_and_extract_features(ds)

    csv_path = os.path.join(output_base, "geolocation_report.csv")
    try:
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "Image Name", "Latitude", "Longitude",
                "Processing Time (HH:MM:SS)", "Processing Time (Seconds)",
                "Process-Status", "Status"
            ])

            for drone_path in drone_images:
                name = os.path.splitext(os.path.basename(drone_path))[0]
                out_dir = os.path.join(output_base, name)
                os.makedirs(out_dir, exist_ok=True)

                img = cv2.imread(drone_path)
                if img is None:
                    logging.error(f"[ERROR] Cannot read {drone_path}")
                    writer.writerow([name, "", "", "", "", "failure", "failure: file read error"])
                    continue

                h, w = img.shape[:2]
                start = time.time()

                try:
                    kp2, desc2 = detector.detectAndCompute(img, None)
                    if desc2 is None:
                        raise ValueError("No descriptors in drone image")

                    best_geo = (0.0, 0.0)
                    best_matches = []
                    best_score = 0
                    best_kp = None
                    best_img = None

                    if not tile_mode:
                        matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
                        matches = matcher.knnMatch(ortho_desc, desc2, k=2)
                        good = [m for m, n in matches if m.distance < 0.75 * n.distance]
                        if len(good) >= 4:
                            src_pts = np.float32([ortho_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                            H, _ = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
                            mapped = cv2.perspectiveTransform(np.array([[[w/2, h/2]]], dtype=np.float32), H)[0][0]
                            geo_lon, geo_lat = pixel_to_geo(transform, mapped[0], mapped[1])
                            save_match_image(ortho_img, ortho_kp, img, kp2, good,
                                             os.path.join(out_dir, f"{name}_match.jpg"))
                            best_geo = (geo_lat, geo_lon)
                        else:
                            raise ValueError("Not enough good matches in full image")
                    else:
                        for tile in tiles:
                            matches = cv2.BFMatcher().knnMatch(tile["desc"], desc2, k=2)
                            good = [m for m, n in matches if m.distance < 0.75 * n.distance]
                            if len(good) > best_score:
                                best_score = len(good)
                                best_kp = tile["kp"]
                                best_img = tile["img"]
                                best_matches = good
                                best_geo = pixel_to_geo(transform, tile["x"] + tile["w"] // 2, tile["y"] + tile["h"] // 2)

                        if best_matches:
                            save_match_image(best_img, best_kp, img, kp2, best_matches,
                                             os.path.join(out_dir, f"{name}_match.jpg"))
                        else:
                            raise ValueError("Not enough good matches in tiles")

                    end = time.time()
                    elapsed = end - start

                    if elapsed < 1:
                        process_status = "success"
                    elif elapsed < 5:
                        process_status = "can be optimized"
                    elif elapsed < 10:
                        process_status = "almost done"
                    else:
                        process_status = "failure"

                    writer.writerow([
                        name, f"{best_geo[0]:.6f}", f"{best_geo[1]:.6f}",
                        str(datetime.timedelta(seconds=int(elapsed))),
                        f"{elapsed:.2f}", process_status, "success"
                    ])
                    logging.info(f"[{name}] Processed in {elapsed:.2f} seconds")

                except Exception as e:
                    elapsed = time.time() - start
                    writer.writerow([
                        name, "", "", str(datetime.timedelta(seconds=int(elapsed))),
                        f"{elapsed:.2f}", "failure", f"failure: {str(e)}"
                    ])
                    logging.error(f"[{name}] Failed: {e}")

    except Exception as e:
        logging.error(f"[ERROR] {e}. Cleaning up output...")
        clean_up_output(output_base)
        return

    logging.info(f"[INFO] Completed successfully. Output saved to: {output_base}")

if __name__ == "__main__":
    main()
