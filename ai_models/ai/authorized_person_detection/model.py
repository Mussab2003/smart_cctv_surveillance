import cv2

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from facenet_pytorch import InceptionResnetV1
from .utils import (
    recognize_face,
    load_database,
    is_face_big_enough
)

class FaceRecognitionSystem:
    def __init__(self, yolo_model_path, face_db_path, device):
        self.device = device
        
        # Load models
        self.detector = YOLO(yolo_model_path).to(device)
        self.tracker = DeepSort(max_age=30)
        self.face_recognizer = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        
        # Load face database
        self.database, self.embeddings = load_database(face_db_path)
        
        # Track recognized faces
        self.recognized_tracks = {}

    def process_frame(self, frame):
        results = self.detector(frame)
        detections = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                conf = float(box.conf[0])
                detections.append(([x1, y1, w, h], conf, None, None))

        tracks = self.tracker.update_tracks(detections, frame=frame)

        # 🟰 New Lists to store recognized faces
        authorized = []
        unauthorized = []

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            face_crop = frame[y1:y2, x1:x2]

            if face_crop.size == 0:
                continue
            if not is_face_big_enough(x1, y1, x2, y2):
                continue

            if track_id not in self.recognized_tracks or self.recognized_tracks[track_id] == "Unknown":
                name = recognize_face(face_crop, self.face_recognizer, self.embeddings, self.database, self.device)
                self.recognized_tracks[track_id] = name

            name_to_display = self.recognized_tracks[track_id]
            color = (0, 255, 0) if name_to_display != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID: {track_id}, {name_to_display}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # 🟰 Add to authorized or unauthorized list
            if name_to_display != "Unknown":
                authorized.append(name_to_display)
            else:
                unauthorized.append(track_id)  # you can also just put "Unknown" if you prefer

        return frame, authorized, unauthorized
