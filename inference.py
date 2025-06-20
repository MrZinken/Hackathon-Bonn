import os
import glob
import time
import rasterio
from rasterio.windows import Window
import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import transform
from pyproj import Transformer
from ultralytics import YOLO
from PIL import Image
import torch
import json
import cv2

# ⚙️ Pfade
image_dir = "/home/kai/Documents/10-1_TrueOrthophoto_RGBI_TIF_250x250m_10cm"
model_path = "/home/kai/.local/lib/python3.10/site-packages/ultralytics/runs/segment/train/weights/best.pt"
tile_size = 500
confidence_threshold = 0.25
mask_dir = os.path.join(image_dir, "masks")
os.makedirs(mask_dir, exist_ok=True)

# 🧠 Modell
model = YOLO(model_path)

# ⏱ Zeittracking
timings = {}
overall_start = time.time()

for tif_path in glob.glob(os.path.join(image_dir, "*.tif")):
    start_time = time.time()
    tif_name = os.path.basename(tif_path)
    print(f"🔍 Bearbeite {tif_name}")

    with rasterio.open(tif_path) as src:
        tfm = src.transform
        w, h = src.width, src.height
        n_tiles_x = w // tile_size
        n_tiles_y = h // tile_size

        for i in range(n_tiles_y):
            for j in range(n_tiles_x):
                tile_id = f"{os.path.splitext(tif_name)[0]}_tile_{i}_{j}"
                tile_geojson_path = os.path.join(mask_dir, f"{tile_id}.geojson")

                if os.path.exists(tile_geojson_path):
                    continue

                win = Window(j * tile_size, i * tile_size, tile_size, tile_size)
                tile = src.read(window=win)
                if tile.shape[0] > 3:
                    tile = tile[:3]

                tile_img = np.moveaxis(tile, 0, -1).astype(np.uint8)
                img_pil = Image.fromarray(tile_img)
                results = model.predict(img_pil, imgsz=tile_size, conf=confidence_threshold, verbose=False)

                tile_features = []
                for r in results:
                    masks = r.masks
                    if masks is None:
                        continue
                    for mask in masks.data:
                        mask_np = mask.cpu().numpy().astype(np.uint8)
                        contours, _ = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        for contour in contours:
                            if len(contour) < 3:
                                continue
                            poly = Polygon([(pt[0][0], pt[0][1]) for pt in contour])
                            poly = transform(
                                lambda x, y: rasterio.transform.xy(
                                    tfm, y + i * tile_size, x + j * tile_size, offset="center"
                                )[:2],
                                poly
                            )
                            tile_features.append({
                                "type": "Feature",
                                "geometry": mapping(poly),
                                "properties": {
                                    "source_tile": tile_id
                                }
                            })

                if tile_features:
                    with open(tile_geojson_path, "w") as f:
                        json.dump({
                            "type": "FeatureCollection",
                            "features": tile_features,
                            "crs": {
                                "type": "name",
                                "properties": {"name": "EPSG:25832"}
                            }
                        }, f)

    duration = time.time() - start_time
    timings[tif_name] = duration
    print(f"✅ {tif_name} verarbeitet in {duration:.2f} Sekunden")

overall_duration = time.time() - overall_start

# 📊 Zeitstatistiken
if timings:
    total_images = len(timings)
    avg_time = sum(timings.values()) / total_images
    fastest = min(timings.items(), key=lambda x: x[1])
    slowest = max(timings.items(), key=lambda x: x[1])

    print("\n⏱ Zeitstatistik:")
    print(f"🔢 Verarbeitete Bilder: {total_images}")
    print(f"🚀 Schnellstes Bild: {fastest[0]} ({fastest[1]:.2f} Sekunden)")
    print(f"🐢 Langsamstes Bild: {slowest[0]} ({slowest[1]:.2f} Sekunden)")
    print(f"📊 Durchschnittszeit pro Bild: {avg_time:.2f} Sekunden")
    print(f"⏲️ Gesamtdauer: {overall_duration:.2f} Sekunden")

print("\n✅ Alle Kacheln verarbeitet. Starte Zusammenführung...")

# 📦 Alle Kachel-GeoJSONs zusammenfassen
merged = {
    "type": "FeatureCollection",
    "features": [],
    "crs": {
        "type": "name",
        "properties": {"name": "EPSG:25832"}
    }
}

for tile_file in sorted(glob.glob(os.path.join(mask_dir, "*.geojson"))):
    with open(tile_file, "r") as f:
        data = json.load(f)
        merged["features"].extend(data["features"])

out_path = os.path.join(image_dir, "prediction_merged.geojson")
with open(out_path, "w") as f:
    json.dump(merged, f)

print(f"\n✅ Gesamt-GeoJSON gespeichert: {out_path}")
