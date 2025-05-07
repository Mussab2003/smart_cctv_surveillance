import cv2

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from facenet_pytorch import InceptionResnetV1
from .utils import (
    recognize_face,
    load_database,
    is_face_big_enough,
    is_face_usable,
)

import torch
from gfpgan import GFPGANer
import numpy as np
restorer = GFPGANer(    
    model_path='GFPGANv1.3.pth',
    upscale=1,
    arch='clean',
    channel_multiplier=2,
    bg_upsampler=None,
    device='cuda' if torch.cuda.is_available() else 'cpu'
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
        self.recognized_names_set = set()  # <== NEW: Collect recognized names

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
            if not is_face_usable(x1, y1, x2, y2):
                try:
                    _, _, restored = restorer.enhance(
                        face_rgb,
                        has_aligned=False,
                        only_center_face=False,
                        paste_back=False
                    )
                    if restored is not None:
                        face_rgb = restored
                except Exception as e:
                    print(f"GFPGAN restoration failed: {e}")


            face_for_recognition = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR)

            if track_id not in self.recognized_tracks:
                self.recognized_tracks[track_id] = {"name": "Unknown", "counter": 0}

            self.recognized_tracks[track_id]["counter"] += 1

            # Re-run recognition every 10 frames
            if self.recognized_tracks[track_id]["counter"] % 10 == 0 or self.recognized_tracks[track_id]["name"] == "Unknown":
                name = recognize_face(face_for_recognition, self.face_recognizer, self.embeddings, self.database, self.device)
                self.recognized_tracks[track_id]["name"] = name
            
            
        
            name_to_display = self.recognized_tracks[track_id]["name"]
            if name_to_display != "Unknown":
                self.recognized_names_set.add(name_to_display) 
            color = (0, 255, 0) if name_to_display != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID: {track_id}, {name_to_display}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 🟰 Add to authorized or unauthorized list
            if name_to_display != "Unknown":
                authorized.append(name_to_display)
            else:
                unauthorized.append(track_id)  # you can also just put "Unknown" if you prefer

        info_window = np.zeros((300, 400, 3), dtype=np.uint8)

        y_offset = 50
        cv2.putText(info_window, "Recognized People:", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        for name in sorted(self.recognized_names_set):  # use the persistent set
            cv2.putText(info_window, name, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 30

        # === Show in a separate window ===
        cv2.imshow("Recognized Names", info_window)

        

        return frame, authorized, unauthorized
