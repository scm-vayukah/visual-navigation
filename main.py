import os
import shutil
import time
import argparse
from datetime import datetime

from src.tiff_tiler import tile_and_extract_features
from src.image_matcher import match_drone_images
from src.utils import create_output_dirs, clean_up_output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--base_path", required=True, help="Base folder path")
    parser.add_argument("-m", "--model", choices=["sift", "orb", "orb-cuda"], default="sift", help="Feature extraction model")
    parser.add_argument("-t", "--tile_size", type=int, default=5000, help="Tile size for TIFF image")
    args = parser.parse_args()

    base_path = args.base_path
    tiff_folder = os.path.join(base_path, "Tiff")
    drone_folder = os.path.join(base_path, "Drone_images")
    output_base = os.path.join(base_path, f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    tiles_folder, report_path = create_output_dirs(output_base)

    try:
        start = time.time()
        print("Tiling TIFF and extracting features...")
        tile_and_extract_features(tiff_folder, tiles_folder, model_name=args.model, tile_size=args.tile_size)

        print("Starting drone image matching...")
        match_drone_images(drone_folder, tiles_folder, report_path, args.model, start_time=start)

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Cleaning up temporary files...")
        clean_up_output(output_base)

if __name__ == "__main__":
    main()
