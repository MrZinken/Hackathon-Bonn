import os
import json
import random
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pycocotools import mask as mask_utils

# 📂 Pfade anpassen
split = "valid"  # oder "train", "test"
dataset_dir = "/home/kai/Downloads/resized_dataset"
image_dir = os.path.join(dataset_dir, split)
ann_path = os.path.join(image_dir, "annotations.json")

# 🔄 Anzahl zufälliger Bilder zur Anzeige
num_samples = 5

# 🔧 COCO-Daten laden
with open(ann_path, "r") as f:
    coco = json.load(f)

images = coco["images"]
annotations = coco["annotations"]

# 🔎 Zuordnung von Image-ID → Annotationen
ann_dict = {}
for ann in annotations:
    image_id = ann["image_id"]
    ann_dict.setdefault(image_id, []).append(ann)

# 🎲 Zufällige Auswahl
samples = random.sample(images, num_samples)

for img_info in samples:
    file_name = img_info["file_name"]
    img_path = os.path.join(image_dir, file_name)
    img = cv2.imread(img_path)
    if img is None:
        print(f"⚠️ Bild nicht lesbar: {img_path}")
        continue
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    height, width = img_rgb.shape[:2]

    mask_canvas = np.zeros((height, width), dtype=np.uint8)

    anns = ann_dict.get(img_info["id"], [])
    for ann in anns:
        # Polygon-Segmentierung in Maske umwandeln
        if isinstance(ann["segmentation"], list):
            for seg in ann["segmentation"]:
                pts = np.array(seg).reshape((-1, 2)).astype(np.int32)
                cv2.fillPoly(mask_canvas, [pts], color=255)

    # 🎨 Visualisierung
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    ax[0].imshow(img_rgb)
    ax[0].set_title("Originalbild")
    ax[1].imshow(img_rgb)
    ax[1].imshow(mask_canvas, cmap='Reds', alpha=0.5)
    ax[1].set_title("Mit Maske")
    for a in ax:
        a.axis('off')
    plt.tight_layout()
    output_path = f"/home/kai/Documents/Hackathon-Bonn/visualized_{file_name}"
    plt.savefig(output_path)
    print(f"✅ Gespeichert: {output_path}")
    plt.close()
