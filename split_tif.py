from PIL import Image
import os

# 🔧 Ordnerpfade
input_folder = "/home/glasenapp/Schreibtisch/input"         # Ordner mit .tif-Dateien
output_folder = "/home/glasenapp/Schreibtisch/output"   # Zielordner für 500x500 JPGs

tile_size = 500  # Zielgröße der Kacheln

# 📁 Zielordner anlegen
os.makedirs(output_folder, exist_ok=True)

# 🔁 Alle .tif-Dateien verarbeiten
for filename in os.listdir(input_folder):
    if filename.lower().endswith(".tif"):
        tif_path = os.path.join(input_folder, filename)
        img = Image.open(tif_path)

        # 📐 Bildgröße prüfen
        width, height = img.size
        if width != 2500 or height != 2500:
            print(f"⚠️  {filename} hat nicht die erwartete Größe 2500x2500. Übersprungen.")
            continue

        base_name = os.path.splitext(filename)[0]

        # 🧩 5x5 Kacheln erzeugen
        for i in range(0, width, tile_size):
            for j in range(0, height, tile_size):
                box = (i, j, i + tile_size, j + tile_size)
                tile = img.crop(box)
                tile_filename = f"{base_name}_x{i//tile_size}_y{j//tile_size}.jpg"
                tile.save(os.path.join(output_folder, tile_filename), "JPEG", quality=95)

        print(f"✅ {filename} → 25 JPG-Kacheln erzeugt.")
