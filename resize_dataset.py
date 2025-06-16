import os
import json
import cv2
from tqdm import tqdm

# 📐 Alte und neue Bildgröße
original_size = 640
target_size = 1000
scale = target_size / original_size

# 📂 Pfade
splits = ["train", "valid", "test"]
base_input_dir = "/home/kai/Downloads/dataset"
base_output_dir = "/home/kai/Downloads/resized_dataset"

for split in splits:
    print(f"\n🔄 Bearbeite {split}...")

    input_split_dir = os.path.join(base_input_dir, split)
    input_ann_path = os.path.join(input_split_dir, "annotations.json")

    output_split_dir = os.path.join(base_output_dir, split)
    output_ann_path = os.path.join(output_split_dir, "annotations.json")
    os.makedirs(output_split_dir, exist_ok=True)

    # 📄 COCO-Annotationen laden
    with open(input_ann_path, 'r') as f:
        coco = json.load(f)

    # 🖼️ Bilder skalieren
    for img_info in tqdm(coco['images'], desc=f"[{split}] Bilder skalieren"):
        file_name = img_info['file_name']
        input_path = os.path.join(input_split_dir, file_name)
        output_path = os.path.join(output_split_dir, file_name)

        img = cv2.imread(input_path)
        if img is None:
            print(f"⚠️ Bild nicht gefunden oder ungültig: {input_path}")
            continue

        resized_img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(output_path, resized_img)

        img_info['width'] = target_size
        img_info['height'] = target_size

    # 📝 Annotationen skalieren
    for ann in coco['annotations']:
        ann['bbox'] = [x * scale for x in ann['bbox']]
        ann['area'] *= scale * scale
        if 'segmentation' in ann and isinstance(ann['segmentation'], list):
            ann['segmentation'] = [[coord * scale for coord in seg] for seg in ann['segmentation']]

    # 💾 Neue JSON speichern
    with open(output_ann_path, 'w') as f:
        json.dump(coco, f)

    print(f"✅ {split} abgeschlossen. Neue Bilder und Annotationen gespeichert.")

print("\n🎉 Komplettes Dataset erfolgreich skaliert.")
