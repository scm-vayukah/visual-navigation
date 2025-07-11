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
    kpts = processed['keypoints'].detach().numpy()
    descs = processed['descriptors'].detach().numpy()
    logging.debug(f"Extracted {len(kpts)} keypoints")
    return kpts, descs

def match_features(descriptors1, descriptors2):
    if descriptors1.shape[1] != 256 or descriptors2.shape[1] != 256:
        raise ValueError("Descriptor size must be 256 for SuperPoint")

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    logging.debug("Running FLANN matcher")
    matches = flann.knnMatch(descriptors1.astype(np.float32), descriptors2.astype(np.float32), k=2)
    good_matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < 0.85 * m[1].distance]

    if len(good_matches) == 0:
        logging.warning("No good matches with FLANN. Trying BFMatcher fallback...")
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        matches = bf.match(descriptors1.astype(np.float32), descriptors2.astype(np.float32))
        good_matches = sorted(matches, key=lambda x: x.distance)[:5]

    logging.debug(f"Found {len(good_matches)} good matches")
    return good_matches

def try_load_full_tiff(tiff_path):
    try:
        dataset = gdal.Open(tiff_path)
        if not dataset:
            raise RuntimeError("GDAL failed to open image")
        image = dataset.ReadAsArray()
        if image.ndim == 3:
            image = np.transpose(image, (1, 2, 0))
        elif image.ndim == 2:
            image = np.expand_dims(image, axis=-1)
        logging.info("Loaded full TIFF image successfully")
        return image, dataset
    except Exception as e:
        logging.warning(f"Could not load full TIFF: {e}")
        return None, None

def tile_image(tiff_path, tile_size):
    logging.info("Tiling TIFF image...")
    dataset = gdal.Open(tiff_path)
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    image_tiles = []
    transform = dataset.GetGeoTransform()

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            w = min(tile_size, width - x)
            h = min(tile_size, height - y)
            tile = dataset.ReadAsArray(x, y, w, h)
            if tile.ndim == 3:
                tile = np.transpose(tile, (1, 2, 0))
            elif tile.ndim == 2:
                tile = np.expand_dims(tile, axis=-1)
            image_tiles.append(((x, y), tile))

    logging.info(f"Generated {len(image_tiles)} tiles")
    return image_tiles, transform

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
    tiff_folder = os.path.join(base_path, 'Tiff')
    drone_folder = os.path.join(base_path, 'Drone_images')
    output_folder = os.path.join(base_path, "Output")

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    try:
        tiff_image_path = next((os.path.join(tiff_folder, f) for f in os.listdir(tiff_folder)
                                if f.lower().endswith(('.tif', '.tiff'))), None)
        if not tiff_image_path:
            raise FileNotFoundError("No TIFF image found in Tiff folder")

        processor = AutoImageProcessor.from_pretrained("magic-leap-community/superpoint")
        model = SuperPointForKeypointDetection.from_pretrained("magic-leap-community/superpoint")

        tiff_image, dataset = try_load_full_tiff(tiff_image_path)
        if tiff_image is not None:
            pil_image = Image.fromarray(tiff_image[:, :, :3])
            tiff_kpts, tiff_descs = extract_features_from_image(model, processor, pil_image)
            transform = dataset.GetGeoTransform()
        else:
            tiles, transform = tile_image(tiff_image_path, tile_size=1024)
            tiff_kpts = []
            tiff_descs = []
            for (x_off, y_off), tile_img in tiles:
                pil_tile = Image.fromarray(tile_img[:, :, :3])
                kp, desc = extract_features_from_image(model, processor, pil_tile)
                kp[:, 0] += x_off
                kp[:, 1] += y_off
                tiff_kpts.append(kp)
                tiff_descs.append(desc)
            tiff_kpts = np.vstack(tiff_kpts)
            tiff_descs = np.vstack(tiff_descs)

        output_csv_path = os.path.join(output_folder, "matched_coordinates.csv")
        drone_images = [f for f in os.listdir(drone_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        with open(output_csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Image", "Latitude", "Longitude", "Time(hh:mm:ss)", "Time(s)", "Status", "Process_Status"])

            for drone_img_name in tqdm(drone_images):
                drone_img_path = os.path.join(drone_folder, drone_img_name)

                try:
                    start_time = time.time()
                    logging.debug(f"Processing image: {drone_img_name}")
                    drone_kpts, drone_descs = extract_features_from_image(model, processor, drone_img_path)
                    matches = match_features(drone_descs, tiff_descs)

                    if not matches:
                        raise ValueError("No good matches found")

                    matched_kp = tiff_kpts[matches[0].trainIdx]
                    lon, lat = pixel_to_geo(transform, matched_kp[0], matched_kp[1])

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

                    writer.writerow([drone_img_name, lat, lon, hhmmss, f"{elapsed:.2f}", "success", process_status])

                except Exception as e:
                    elapsed = time.time() - start_time
                    hhmmss = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                    process_status = "else failure"
                    writer.writerow([drone_img_name, "", "", hhmmss, f"{elapsed:.2f}", f"failure: {str(e)}", process_status])

    except Exception as e:
        logging.error(f"Process failed: {e}")
        shutil.rmtree(output_folder, ignore_errors=True)
    else:
        logging.info(f"Process completed. Results saved to {output_csv_path}")

if __name__ == '__main__':
    main()
