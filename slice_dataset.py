import os
from PIL import Image
from pathlib import Path

# 📁 INPUT: Pfad zu Ordner mit 130 TIFF-Dateien
input_dir = Path("/home/glasenapp/Schreibtisch/input")  # ggf. anpassen
output_base = Path("/home/glasenapp/Schreibtisch/output")
output_base.mkdir(parents=True, exist_ok=True)

# 🔢 Einstellungen
tile_size = 500
tiles_per_image = 25
images_per_group = 2

# 📦 Hole alle TIFF-Dateien und sortiere sie
tiff_files = sorted([f for f in input_dir.glob("*.tif")])
assert len(tiff_files) == 130, "Es sollten genau 130 TIFF-Dateien im Eingabeordner liegen."

group_index = 1

for i in range(0, len(tiff_files), images_per_group):
    group_folder = output_base / f"Gruppe{group_index:02d}"
    raw_folder = group_folder / "rohdaten"
    anno_folder = group_folder / "annotierte_daten"

    raw_folder.mkdir(parents=True, exist_ok=True)
    anno_folder.mkdir(parents=True, exist_ok=True)

    current_batch = tiff_files[i:i+images_per_group]

    for tif_path in current_batch:
        img = Image.open(tif_path)
        basename = tif_path.stem.replace("TOP_", "")
        
        # Slices in 5x5 Grid (25 Slices à 500×500)
        count = 1
        for y in range(0, tile_size * 5, tile_size):
            for x in range(0, tile_size * 5, tile_size):
                tile = img.crop((x, y, x + tile_size, y + tile_size))
                out_name = f"{count}_{basename}.jpg"
                tile.save(raw_folder / out_name, "JPEG", quality=95)
                count += 1

    group_index += 1

print("✅ Fertig! Alle Bilder wurden gesliced und in rohdaten/ gespeichert.")
