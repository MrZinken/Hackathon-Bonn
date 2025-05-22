from ultralytics import YOLO
import os

# 🔧 Pfade anpassen
base_dir = "/home/glasenapp/Downloads/HackathonBonn_merged"
train_json = os.path.join(base_dir, "annotations_train.json")
val_json = os.path.join(base_dir, "annotations_test.json")
img_dir = os.path.join(base_dir, "images")

# 🔄 Temporäres YAML-Configfile für YOLO
yaml_path = os.path.join(base_dir, "dataset_config.yaml")
with open(yaml_path, "w") as f:
    f.write(f"""\
path: {base_dir}
train: images/train
val: images/val
task: segment
names:
  0: solar_panel
""")

# 🧠 Modell laden
model = YOLO("yolov8n-seg.pt")  # Alternativ: yolov8s-seg.pt oder yolov8m-seg.pt

# 🚀 Training starten
model.train(
    data=yaml_path,
    epochs=10,
    imgsz=1000,  # nutzt volle Auflösung
    batch=4,     # kannst du bei wenig RAM auf 2 oder 1 senken
    device="cpu",    # 0 = erste GPU, "cpu" = ohne GPU
    project=os.path.join(base_dir, "yolov8_runs"),
    name="yolov8n-seg_hackathon",
    val=True,
)
