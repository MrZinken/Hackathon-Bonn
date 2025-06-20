from ultralytics import YOLO

model = YOLO("yolov8m-seg.pt")

model.train(
    data="/home/kai/Documents/Hackathon-Bonn/yolo_dataset/dataset.yaml",
    epochs=50,
    imgsz=500,
    batch=4,
    device="0",  # "0" = GPU, "cpu" für CPU
    project="runs/segment",     # Basisordner für Trainingsläufe
    name="shadowsegmentation",   # Jeder Run überschreibt denselben Ordner
    exist_ok=False               # wichtig: erlaubt das Überschreiben
)
