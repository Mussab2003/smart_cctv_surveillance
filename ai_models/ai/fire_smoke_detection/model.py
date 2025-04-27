from ultralytics import YOLO
import torch

class FireSmokeDetector:
    def __init__(self, confidence=0.5):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO("ai_models/ai/fire_smoke_detection/fire_smoke_detection.pt")
        self.custom_names = {0: "smoke", 1: "fire", 2: "none"}
        self.confidence = confidence
        
        if self.device == 'cuda':
            print("CUDA Available:", torch.cuda.is_available())
            print("GPU:", torch.cuda.get_device_name(0))
            self.model.to("cuda")
        else:
            print("CUDA not available, using CPU.")

    def detect(self, frame):
        results = self.model.predict(frame, conf=self.confidence)
        return results, self.custom_names
