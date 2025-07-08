import os
import numpy as np
from osgeo import gdal
import cv2
from src.feature_extractor import extract_features

def tile_and_extract_features(tiff_folder, output_tile_dir, model_name="sift", tile_size=5000):
    tiff_path = [f for f in os.listdir(tiff_folder) if f.lower().endswith((".tif", ".tiff"))][0]
    full_path = os.path.join(tiff_folder, tiff_path)

    ds = gdal.Open(full_path)
    width = ds.RasterXSize
    height = ds.RasterYSize
    bands = ds.RasterCount

    x_tiles = width // tile_size + (width % tile_size > 0)
    y_tiles = height // tile_size + (height % tile_size > 0)

    for i in range(y_tiles):
        for j in range(x_tiles):
            x_offset = j * tile_size
            y_offset = i * tile_size
            w = min(tile_size, width - x_offset)
            h = min(tile_size, height - y_offset)

            tile = ds.ReadAsArray(x_offset, y_offset, w, h)
            if bands == 1:
                tile = tile
            elif bands == 3:
                tile = tile.transpose(1, 2, 0)
            else:
                tile = tile[:3].transpose(1, 2, 0)

            tile_path = os.path.join(output_tile_dir, f"tile_{i}_{j}.jpg")
            cv2.imwrite(tile_path, tile)

            kp, desc = extract_features(tile, model_name)
            if desc is not None and len(kp) > 0:
                np.savez_compressed(tile_path + ".npz",
                    kp=np.array([[pt.pt[0], pt.pt[1], pt.size, pt.angle, pt.response, pt.octave, pt.class_id]
                                 for pt in kp], dtype=np.float32),
                    desc=desc)
            else:
                print(f"Skipping {tile_path}, no features found.")
