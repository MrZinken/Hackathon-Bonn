import os
import shutil
import random
from tqdm import tqdm
from pycocotools.coco import COCO
import numpy as np

# === 📂 Eingabe-Ordner
gruppen_root = "/home/kai/Downloads/HackathonBonn/"
output_dir = "yolo_dataset"
os.makedirs(output_dir, exist_ok=True)

# === 📁 Zielstruktur anlegen
splits = ["train", "valid"]
for split in splits:
    os.makedirs(os.path.join(output_dir, split, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, split, "labels"), exist_ok=True)

# === 🔄 Alle Gruppen durchgehen
all_images = []

for gruppe in os.listdir(gruppen_root):
    gruppe_path = os.path.join(gruppen_root, gruppe)
    if not os.path.isdir(gruppe_path):
        continue

    annot_dir = os.path.join(gruppe_path, "annotierte_daten")
    if not os.path.exists(annot_dir):
        print(f"⚠️ Kein annotierte_daten-Ordner in {gruppe}")
        continue

    # JSON-Datei finden
    json_files = [f for f in os.listdir(annot_dir) if f.endswith(".json")]
    if not json_files:
        print(f"⚠️ Keine annotations.json in {annot_dir}")
        continue

    coco = COCO(os.path.join(annot_dir, json_files[0]))

    for img in coco.dataset["images"]:
        file_path = os.path.join(annot_dir, img["file_name"])
        if not os.path.exists(file_path):
            print(f"⚠️ Bild fehlt: {file_path}")
            continue

        ann_ids = coco.getAnnIds(imgIds=img["id"])
        anns = coco.loadAnns(ann_ids)
        all_images.append((file_path, anns, img["width"], img["height"]))

# === 🔀 Shuffle und split
random.shuffle(all_images)
split_idx = int(0.7 * len(all_images))
train_data = all_images[:split_idx]
val_data = all_images[split_idx:]

# === 💾 YOLO-Segmentierungsformat speichern
def save_yolo_format(img_path, anns, width, height, split):
    basename = os.path.basename(img_path)
    dest_img_path = os.path.join(output_dir, split, "images", basename)
    shutil.copy(img_path, dest_img_path)

    label_path = os.path.join(output_dir, split, "labels", basename.rsplit(".", 1)[0] + ".txt")
    with open(label_path, "w") as f:
        for ann in anns:
            if "segmentation" not in ann or not isinstance(ann["segmentation"], list):
                continue
            for seg in ann["segmentation"]:
                pts = np.array(seg).reshape(-1, 2)
                if len(pts) < 3:
                    continue
                pts[:, 0] /= width
                pts[:, 1] /= height
                pts = pts.flatten()
                pts_str = " ".join([f"{x:.6f}" for x in pts])
                f.write(f"{ann['category_id']} {pts_str}\n")

# === 📁 Bilder und Labels speichern
for img_path, anns, w, h in tqdm(train_data, desc="📁 Train speichern"):
    save_yolo_format(img_path, anns, w, h, "train")

for img_path, anns, w, h in tqdm(val_data, desc="📁 Val speichern"):
    save_yolo_format(img_path, anns, w, h, "valid")

# === 📝 dataset.yaml schreiben
dataset_yaml_path = os.path.join(output_dir, "dataset.yaml")
with open(dataset_yaml_path, "w") as f:
    f.write(f"""\
train: {os.path.abspath(output_dir)}/train/images
val: {os.path.abspath(output_dir)}/valid/images

nc: 1
names: ['klasse']

roboflow:
  workspace: soloyolo
  project: shadow-segmentation
""")

print("\n✅ YOLOv8-Datensatz ist bereit!")
print(f"📊 Train: {len(train_data)} | Val: {len(val_data)}")
print(f"📄 dataset.yaml gespeichert unter: {dataset_yaml_path}")
