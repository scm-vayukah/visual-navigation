import os
import cv2
import csv
import time
import datetime
import shutil
import logging
import numpy as np
from PIL import Image
from osgeo import gdal
from transformers import AutoImageProcessor, SuperPointForKeypointDetection
from tqdm import tqdm

def pixel_to_geo(transform, x, y):
    geo_x = transform[0] + x * transform[1] + y * transform[2]
    geo_y = transform[3] + x * transform[4] + y * transform[5]
    return geo_x, geo_y

def extract_features_from_image(model, processor, image_input):
    logging.debug(f"Loading image: {image_input}")

    if isinstance(image_input, str):
        image = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        image = image_input.convert("RGB")
    else:
        raise TypeError("image_input must be a file path or PIL.Image")

    inputs = processor(image, return_tensors="pt")
    outputs = model(**inputs)
    size = (image.height, image.width)
    processed = processor.post_process_keypoint_detection(outputs, [size])[0]
    keypoints = processed['keypoints'].detach().numpy()
    descriptors = processed['descriptors'].detach().numpy()
    logging.debug(f"Extracted {len(keypoints)} keypoints")
    return keypoints, descriptors

def match_features(drone_descriptors, ortho_descriptors):
    if drone_descriptors.shape[1] != 256 or ortho_descriptors.shape[1] != 256:
        raise ValueError("Descriptor size must be 256 for SuperPoint")

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    logging.debug("Running FLANN matcher")
    matches = flann.knnMatch(drone_descriptors.astype(np.float32), ortho_descriptors.astype(np.float32), k=2)
    good_matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < 0.85 * m[1].distance]

    if len(good_matches) == 0:
        logging.warning("No good matches with FLANN. Trying BFMatcher fallback...")
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        matches = bf.match(drone_descriptors.astype(np.float32), ortho_descriptors.astype(np.float32))
        good_matches = sorted(matches, key=lambda x: x.distance)[:5]

    logging.debug(f"Found {len(good_matches)} good matches")
    return good_matches

def try_load_full_tiff(ortho_path):
    try:
        dataset = gdal.Open(ortho_path)
        if not dataset:
            raise RuntimeError("GDAL failed to open image")
        ortho_array = dataset.ReadAsArray()
        if ortho_array.ndim == 3:
            ortho_array = np.transpose(ortho_array, (1, 2, 0))
        elif ortho_array.ndim == 2:
            ortho_array = np.expand_dims(ortho_array, axis=-1)
        logging.info("Loaded full orthophoto image successfully")
        return ortho_array, dataset
    except Exception as e:
        logging.warning(f"Could not load full orthophoto: {e}")
        return None, None

def tile_orthophoto(ortho_path, tile_size):
    logging.info("Tiling orthophoto image...")
    dataset = gdal.Open(ortho_path)
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    ortho_tiles = []
    geo_transform = dataset.GetGeoTransform()

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            w = min(tile_size, width - x)
            h = min(tile_size, height - y)
            tile = dataset.ReadAsArray(x, y, w, h)
            if tile.ndim == 3:
                tile = np.transpose(tile, (1, 2, 0))
            elif tile.ndim == 2:
                tile = np.expand_dims(tile, axis=-1)
            ortho_tiles.append(((x, y), tile))

    logging.info(f"Generated {len(ortho_tiles)} tiles")
    return ortho_tiles, geo_transform

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base', required=True, help='Base directory')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    base_path = args.base
    ortho_folder = os.path.join(base_path, 'Tiff')
    drone_folder = os.path.join(base_path, 'Drone_images')
    output_folder = os.path.join(base_path, "Output")

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    try:
        ortho_path = next((os.path.join(ortho_folder, f) for f in os.listdir(ortho_folder)
                           if f.lower().endswith(('.tif', '.tiff'))), None)
        if not ortho_path:
            raise FileNotFoundError("No orthophoto TIFF image found in Tiff folder")

        processor = AutoImageProcessor.from_pretrained("magic-leap-community/superpoint")
        model = SuperPointForKeypointDetection.from_pretrained("magic-leap-community/superpoint")

        ortho_image, dataset = try_load_full_tiff(ortho_path)
        if ortho_image is not None:
            ortho_pil = Image.fromarray(ortho_image[:, :, :3])
            ortho_keypoints, ortho_descriptors = extract_features_from_image(model, processor, ortho_pil)
            geo_transform = dataset.GetGeoTransform()
        else:
            tiles, geo_transform = tile_orthophoto(ortho_path, tile_size=1024)
            all_keypoints = []
            all_descriptors = []
            for (x_offset, y_offset), tile_img in tiles:
                tile_pil = Image.fromarray(tile_img[:, :, :3])
                kps, descs = extract_features_from_image(model, processor, tile_pil)
                kps[:, 0] += x_offset
                kps[:, 1] += y_offset
                all_keypoints.append(kps)
                all_descriptors.append(descs)
            ortho_keypoints = np.vstack(all_keypoints)
            ortho_descriptors = np.vstack(all_descriptors)

        output_csv_path = os.path.join(output_folder, "matched_coordinates.csv")
        drone_image_files = [f for f in os.listdir(drone_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        with open(output_csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Image", "Latitude", "Longitude", "Time(hh:mm:ss)", "Time(s)", "Status", "Process_Status"])

            for drone_filename in tqdm(drone_image_files):
                drone_image_path = os.path.join(drone_folder, drone_filename)

                try:
                    start_time = time.time()
                    logging.debug(f"Processing drone image: {drone_filename}")
                    drone_keypoints, drone_descriptors = extract_features_from_image(model, processor, drone_image_path)
                    matches = match_features(drone_descriptors, ortho_descriptors)

                    if not matches:
                        raise ValueError("No good matches found")

                    best_match_kp = ortho_keypoints[matches[0].trainIdx]
                    longitude, latitude = pixel_to_geo(geo_transform, best_match_kp[0], best_match_kp[1])

                    end_time = time.time()
                    elapsed = end_time - start_time
                    hhmmss = time.strftime("%H:%M:%S", time.gmtime(elapsed))

                    if elapsed < 1:
                        process_status = "<1 second success"
                    elif elapsed < 5:
                        process_status = "<5 seconds can be optimised"
                    elif elapsed < 10:
                        process_status = "<10 seconds almost done"
                    else:
                        process_status = "else failure"

                    writer.writerow([drone_filename, latitude, longitude, hhmmss, f"{elapsed:.2f}", "success", process_status])

                except Exception as e:
                    elapsed = time.time() - start_time
                    hhmmss = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                    process_status = "else failure"
                    writer.writerow([drone_filename, "", "", hhmmss, f"{elapsed:.2f}", f"failure: {str(e)}", process_status])

    except Exception as e:
        logging.error(f"Process failed: {e}")
        shutil.rmtree(output_folder, ignore_errors=True)
    else:
        logging.info(f"Process completed. Results saved to {output_csv_path}")

if __name__ == '__main__':
    main()
