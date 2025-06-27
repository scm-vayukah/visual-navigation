import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from osgeo import gdal
import piexif
import time
import datetime
import logging
from glob import glob

# Enable GDAL exceptions and setup logging
gdal.UseExceptions()
logging.basicConfig(level=logging.INFO, format='%(message)s')

def pixel_to_geo(transform, x, y):
    geo_x = transform[0] + x * transform[1] + y * transform[2]
    geo_y = transform[3] + x * transform[4] + y * transform[5]
    return geo_x, geo_y

def deg_to_dms_rational(deg_float):
    deg = int(deg_float)
    min_float = (deg_float - deg) * 60
    minute = int(min_float)
    sec_float = (min_float - minute) * 60
    return [
        (deg, 1),
        (minute, 1),
        (int(round(sec_float * 10000)), 10000)
    ]

def write_gps_to_exif(image_path, lat, lon):
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
        piexif.GPSIFD.GPSLatitude: deg_to_dms_rational(abs(lat)),
        piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
        piexif.GPSIFD.GPSLongitude: deg_to_dms_rational(abs(lon))
    }
    user_comment = f"Latitude: {lat:.6f}, Longitude: {lon:.6f}".encode('utf-8')
    exif_dict = {"GPS": gps_ifd, "Exif": {piexif.ExifIFD.UserComment: user_comment}}
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, image_path)

def process_images(ortho_path, drone_paths, output_version):
    # Load orthoimage downsampled
    ortho_ds = gdal.Open(ortho_path)
    if ortho_ds is None:
        raise ValueError("Failed to load orthoimage")

    transform = ortho_ds.GetGeoTransform()

    buf_xsize = 1024
    buf_ysize = int(ortho_ds.RasterYSize * buf_xsize / ortho_ds.RasterXSize)
    ortho_array = ortho_ds.ReadAsArray(buf_xsize=buf_xsize, buf_ysize=buf_ysize)

    if len(ortho_array.shape) == 3:
        ortho_img = cv2.cvtColor(np.moveaxis(ortho_array, 0, -1), cv2.COLOR_RGB2GRAY)
    else:
        ortho_img = ortho_array.astype(np.uint8)

    detector = cv2.SIFT_create()

    for drone_path in drone_paths:
        image_name = os.path.splitext(os.path.basename(drone_path))[0]
        out_dir = os.path.join(output_version, image_name)
        os.makedirs(out_dir, exist_ok=True)

        drone_img_gray = cv2.imread(drone_path, cv2.IMREAD_GRAYSCALE)
        drone_img_color = Image.open(drone_path).convert("RGB")
        width, height = drone_img_color.size

        start_time = time.time()
        try:
            kp1, des1 = detector.detectAndCompute(ortho_img, None)
            kp2, des2 = detector.detectAndCompute(drone_img_gray, None)
            if des1 is None or des2 is None:
                raise ValueError("No descriptors found.")

            matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
            matches = matcher.knnMatch(des1, des2, k=2)
            good = [m for m, n in matches if m.distance < 0.75 * n.distance]

            if len(good) < 4:
                raise ValueError("Not enough good matches")

            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            H, _ = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

            h, w = drone_img_gray.shape
            center = np.array([[[w / 2, h / 2]]], dtype=np.float32)
            mapped_center = cv2.perspectiveTransform(center, H)[0][0]
            geo_lon, geo_lat = pixel_to_geo(transform, mapped_center[0], mapped_center[1])

            # Overlay text
            jpg_overlay = drone_img_color.copy()
            draw = ImageDraw.Draw(jpg_overlay)
            text = f"{geo_lat:.6f}, {geo_lon:.6f}"
            font = ImageFont.load_default()
            draw.text((10, 10), text, fill=(255, 0, 0), font=font)

            # Save outputs
            jpg_path = os.path.join(out_dir, image_name + ".JPG")
            tif_path = os.path.join(out_dir, image_name + ".TIFF")

            jpg_overlay.save(jpg_path, "JPEG")
            drone_img_color.save(tif_path, "TIFF")
            write_gps_to_exif(jpg_path, geo_lat, geo_lon)

            elapsed = time.time() - start_time
            readable = str(datetime.timedelta(seconds=int(elapsed)))

            if elapsed <= 1.0:
                logging.info(f"Hurray! You did it in less than a second [{width}x{height}]")
            elif elapsed <= 10.0:
                logging.info(f"Almost there! Took {readable} [{width}x{height}]")
            else:
                logging.info(f"Failed! Took too long: {readable} [{width}x{height}]")

        except Exception as e:
            elapsed = time.time() - start_time
            readable = str(datetime.timedelta(seconds=int(elapsed)))
            logging.error(f"Failed! Error processing {drone_path}: {e} [{width}x{height}] - Time: {readable}")

if __name__ == "__main__":
    ortho_image_path = "ortho_image.tif"

    # Process 720p
    drone_720p = sorted(glob("720p/*.JPG"))
    if drone_720p:
        logging.info("Processing 720p images...")
        process_images(ortho_image_path, drone_720p, output_version="output/720p_sift_v1")

    # Process 1080p
    drone_1080p = sorted(glob("1080p/*.JPG"))
    if drone_1080p:
        logging.info("Processing 1080p images...")
        process_images(ortho_image_path, drone_1080p, output_version="output/1080p_sift_v1")
