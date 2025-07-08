import os
import shutil

def create_output_dirs(base_output):
    tiles = os.path.join(base_output, "tiles")
    report = os.path.join(base_output, "report")
    os.makedirs(tiles, exist_ok=True)
    os.makedirs(report, exist_ok=True)
    report_file = os.path.join(report, "estimated_geolocation_match.csv")
    return tiles, report_file

def clean_up_output(base_output):
    if os.path.exists(base_output):
        shutil.rmtree(base_output)
