import os
import json
import shutil
import random

# 🔧 Konfiguration
root_dir = "/home/glasenapp/Downloads/HackathonBonn"
merged_dir = "/home/glasenapp/Downloads/HackathonBonn_merged"
merged_images_dir = os.path.join(merged_dir, "images")
merged_annotations_path = os.path.join(merged_dir, "annotations_merged.json")

# 🔨 Vorbereitung
os.makedirs(merged_dir, exist_ok=True)
os.makedirs(merged_images_dir, exist_ok=True)

merged_coco = {"images": [], "annotations": [], "categories": []}
img_id_counter = 1
ann_id_counter = 1
category_mapping = {}
category_id_counter = 0  # YOLOv8 erwartet IDs ab 0

print("🔍 Suche nach Gruppenordnern...")

for group_name in sorted(os.listdir(root_dir)):
    group_path = os.path.join(root_dir, group_name)
    if not os.path.isdir(group_path) or not group_name.startswith("gruppe"):
        continue

    ann_path = os.path.join(group_path, "annotations_augmented.json")
    if not os.path.exists(ann_path):
        print(f"⚠️ Keine Annotation gefunden in {group_name}")
        continue

    with open(ann_path, "r") as f:
        coco = json.load(f)

    for cat in coco["categories"]:
        cat_name = cat["name"]
        if cat_name not in category_mapping:
            category_mapping[cat_name] = category_id_counter
            merged_coco["categories"].append({
                "id": category_id_counter,
                "name": cat_name,
                "supercategory": cat.get("supercategory", "")
            })
            category_id_counter += 1

    for img in coco["images"]:
        old_id = img["id"]
        img["id"] = img_id_counter
        img_filename = img["file_name"]
        src_img_path = os.path.join(group_path, img_filename)
        dst_img_path = os.path.join(merged_images_dir, f"group{group_name[6:]}_{img_filename}")
        shutil.copyfile(src_img_path, dst_img_path)
        img["file_name"] = os.path.basename(dst_img_path)
        merged_coco["images"].append(img)
        old_to_new_img_id = old_id
        new_img_id = img_id_counter
        img_id_counter += 1

        anns_for_img = [ann for ann in coco["annotations"] if ann["image_id"] == old_to_new_img_id]
        for ann in anns_for_img:
            ann["id"] = ann_id_counter
            ann["image_id"] = new_img_id

            old_cat_id = ann["category_id"]
            matching_cats = [cat for cat in coco["categories"] if cat["id"] == old_cat_id]
            if not matching_cats:
                fallback_name = f"auto_class_{old_cat_id}"
                print(f"⚠️ Kategorie-ID {old_cat_id} fehlt in Datei {ann_path}, fallback → '{fallback_name}'")
                if fallback_name not in category_mapping:
                    category_mapping[fallback_name] = category_id_counter
                    merged_coco["categories"].append({
                        "id": category_id_counter,
                        "name": fallback_name,
                        "supercategory": "auto"
                    })
                    category_id_counter += 1
                ann["category_id"] = category_mapping[fallback_name]
            else:
                old_cat_name = matching_cats[0]["name"]
                ann["category_id"] = category_mapping[old_cat_name]

            merged_coco["annotations"].append(ann)
            ann_id_counter += 1

# 💾 Gesamt-Merge speichern
with open(merged_annotations_path, "w") as f:
    json.dump(merged_coco, f)
print(f"✅ Zusammengeführt: {len(merged_coco['images'])} Bilder, {len(merged_coco['annotations'])} Annotationen.")

# 📦 Shuffle & Split
random.seed(42)
all_images = merged_coco["images"]
random.shuffle(all_images)
split_index = int(0.8 * len(all_images))
train_images = all_images[:split_index]
val_images = all_images[split_index:]
train_ids = {img["id"] for img in train_images}
val_ids = {img["id"] for img in val_images}
train_anns = [ann for ann in merged_coco["annotations"] if ann["image_id"] in train_ids]
val_anns = [ann for ann in merged_coco["annotations"] if ann["image_id"] in val_ids]

# 📁 Ordnerstruktur anlegen
images_train_dir = os.path.join(merged_dir, "images/train")
images_val_dir = os.path.join(merged_dir, "images/val")
labels_train_dir = os.path.join(merged_dir, "labels/train")
labels_val_dir = os.path.join(merged_dir, "labels/val")
os.makedirs(images_train_dir, exist_ok=True)
os.makedirs(images_val_dir, exist_ok=True)
os.makedirs(labels_train_dir, exist_ok=True)
os.makedirs(labels_val_dir, exist_ok=True)

# 🔁 Segmentierungs-Polygon konvertieren
def convert_segmentation(segmentation, img_w, img_h):
    yolo_poly = []
    for i in range(0, len(segmentation), 2):
        x = round(segmentation[i] / img_w, 6)
        y = round(segmentation[i+1] / img_h, 6)
        yolo_poly.extend([x, y])
    return yolo_poly

# ✍️ YOLO-Labels erzeugen
img_id_to_img = {img["id"]: img for img in merged_coco["images"]}
for img_set, ann_set, img_dst_dir, lbl_dst_dir in [
    (train_images, train_anns, images_train_dir, labels_train_dir),
    (val_images, val_anns, images_val_dir, labels_val_dir)
]:
    ann_dict = {}
    for ann in ann_set:
        ann_dict.setdefault(ann["image_id"], []).append(ann)

    for img in img_set:
        src_path = os.path.join(merged_images_dir, img["file_name"])
        dst_path = os.path.join(img_dst_dir, img["file_name"])
        shutil.copy(src_path, dst_path)

        anns = ann_dict.get(img["id"], [])
        label_path = os.path.join(lbl_dst_dir, os.path.splitext(img["file_name"])[0] + ".txt")
        with open(label_path, "w") as f:
            for ann in anns:
                if "segmentation" not in ann or not ann["segmentation"]:
                    continue
                if isinstance(ann["segmentation"], list):
                    polygon = ann["segmentation"][0]  # nur erstes Polygon verwenden
                    yolo_seg = convert_segmentation(polygon, img["width"], img["height"])
                    if len(yolo_seg) >= 6:  # mindestens 3 Punkte (x,y)
                        f.write(f"{ann['category_id']} {' '.join(map(str, yolo_seg))}\n")

print(f"📊 Aufgeteilt in {len(train_images)} Trainingsbilder und {len(val_images)} Validierungsbilder.")

# 📜 YOLOv8 YAML erzeugen
yaml_path = os.path.join(merged_dir, "dataset.yaml")
with open(yaml_path, "w") as f:
    f.write(f"path: {merged_dir}\n")
    f.write("train: images/train\n")
    f.write("val: images/val\n")
    f.write("names:\n")
    for cat in merged_coco["categories"]:
        f.write(f"  {cat['id']}: {cat['name']}\n")

print(f"✅ YOLOv8 Segmentierungs-Dataset bereit.\nTrainiere z. B. mit:\n")
print(f"yolo task=segment mode=train model=yolov8n-seg.pt data={yaml_path} imgsz=1000 epochs=50 batch=2 device=cpu")
