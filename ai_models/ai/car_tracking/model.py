from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import torch

class YoloDetector:
    def __init__(self, confidence=0.5):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO("ai_models/ai/car_tracking/car_movement_tracking.pt")
        self.classList = ['car', 'bike']
        self.confidence = confidence

        if self.device == 'cuda':
            print("CUDA Available:", torch.cuda.is_available())
            print("GPU:", torch.cuda.get_device_name(0))
            self.model.to("cuda")
            # Enable half precision for faster inference
            self.model.fuse()
        else:
            print("CUDA not available, using CPU.")

    def detect(self, image):
        # Use a smaller inference size for faster processing
        results = self.model.predict(
            image, 
            conf=self.confidence, 
            device=0 if self.device == 'cuda' else 'cpu',
            verbose=False,  # Disable verbose output
            imgsz=640  # Use a smaller image size for inference
        )
        result = results[0]
        return self.make_detections(result)

    def make_detections(self, result):
        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            w, h = x2 - x1, y2 - y1
            class_number = int(box.cls[0])

            if result.names[class_number] not in self.classList:
                continue

            conf = float(box.conf[0])
            detections.append(([x1, y1, w, h], class_number, conf))
        return detections

# class Tracker:
#     def __init__(self):
#         self.object_tracker = DeepSort(
#             max_age=30,
#             n_init=3,
#             nms_max_overlap=0.3,
#             max_cosine_distance=0.4,
#             nn_budget=None,
#             override_track_class=None,
#             embedder="mobilenet",
#             half=True,
#             bgr=True,
#             embedder_model_name=None,
#             embedder_wts=None,
#             polygon=False,
#             today=None
#         )

#     def track(self, detections, frame):
#         print("In the track function")
#         print(detections)
#         print(frame)
#         tracks = self.object_tracker.update_tracks(detections, frame=frame)
#         tracking_ids = []
#         boxes = []
#         for track in tracks:
#             if not track.is_confirmed():
#                 continue
#             tracking_ids.append(track.track_id)
#             ltrb = track.to_ltrb()
#             boxes.append(ltrb)
#         return tracking_ids, boxes

class Tracker:
  def __init__(self):
    self.object_tracker = DeepSort(
        max_age=30,
        n_init=3,
        nms_max_overlap=0.3,
        max_cosine_distance=0.4,
        nn_budget=None,
        override_track_class=None,
        embedder="mobilenet",
        half=True,
        bgr=True,
        embedder_model_name=None,
        embedder_wts=None,
        polygon=False,
        today=None
    )

  def track(self, detections, frame):
    tracks = self.object_tracker.update_tracks(detections, frame=frame)

    tracking_ids = []
    boxes = []
    for track in tracks:
      if not track.is_confirmed():
        continue
      tracking_ids.append(track.track_id)
      ltrb = track.to_ltrb()
      boxes.append(ltrb)

    return tracking_ids, boxes
