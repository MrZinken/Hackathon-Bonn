from ultralytics import YOLO

model = YOLO("yolov8m-seg.pt")

model.train(
    data="/home/kai/Downloads/solarsegmentation.v15i.yolov8/data.yaml",
    epochs=50,
    imgsz=640,
    batch=2,
    device="0"  # oder "0" für GPU
)
