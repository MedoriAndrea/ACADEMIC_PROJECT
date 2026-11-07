import cv2
import time
from ultralytics import YOLO

# 1) Carica modello YOLO
model = YOLO("yolov8s.pt") 
model.to("cuda")  # Usa GPU se disponibile
names = model.names
classes_to_detect = [0, 64, 66, 67]

cap = cv2.VideoCapture(0)
W, H = 640, 480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

while True:
    start = time.perf_counter()
    ret, frame = cap.read()
    if not ret:
        print("Errore nell'acquisizione dell'immagine")
        break
    results = model.predict(
        source=frame,
        imgsz=(W, H),
        conf=0.25,
        iou=0.45,
        classes=classes_to_detect,
        verbose=False
    )

    plotted = results[0].plot()

    end = time.perf_counter()
    fps = 1 / (end - start)
    print(f"FPS: {fps:.2f}")

    cv2.imshow("video", plotted)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        print("Chiusura della webcam...")
        break

cap.release()
cv2.destroyAllWindows()