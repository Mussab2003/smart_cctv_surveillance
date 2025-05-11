import cv2
import torch
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from facenet_pytorch import InceptionResnetV1
from ai_models.models import FacialEmbedding

class FaceRecognitionSystem:
    def __init__(self, yolo_model_path, device, owner=None):
        self.device = device
        self.owner = owner
        
        # Load models
        self.detector = YOLO(yolo_model_path).to(device)
        self.tracker = DeepSort(max_age=30)
        self.face_recognizer = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        
        # Initialize empty lists
        self.database = {}
        self.embeddings = []
        self.usernames = []
        
        # Load embeddings from database
        self.load_database_embeddings()
        
        # Track recognized faces
        self.recognized_tracks = {}
        self.recognized_names_set = set()

    def load_database_embeddings(self):
        """Load facial embeddings for the current user from the database"""
        try:
            # Get embeddings for the current user
            if self.owner:
                embedding_objects = FacialEmbedding.objects.filter(user=self.owner)
                
                for obj in embedding_objects:
                    username = obj.user.username
                    embedding = np.array(obj.embedding_vector)
                    self.database[username] = embedding
                    self.embeddings.append(embedding)
                    self.usernames.append(username)
                
                if self.embeddings:
                    self.embeddings = np.array(self.embeddings)
                    print(f"Loaded {len(self.embeddings)} embeddings for user {self.owner.username}")
                else:
                    print(f"No embeddings found for user {self.owner.username}")
            else:
                print("No owner specified for loading embeddings")
        except Exception as e:
            print(f"Error loading embeddings: {str(e)}")
            self.embeddings = np.array([])
            self.usernames = []

    def recognize_face(self, face_img):
        """Recognize a face using the stored embeddings"""
        if len(self.embeddings) == 0:
            return "Unknown"

        try:
            # Preprocess face
            face = cv2.resize(face_img, (160, 160))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = face / 255.0
            face = (face - 0.5) / 0.5
            face_tensor = torch.tensor(face.transpose(2, 0, 1)).unsqueeze(0).float().to(self.device)

            # Generate embedding
            with torch.no_grad():
                embedding = self.face_recognizer(face_tensor)
                embedding = embedding.cpu().numpy()

            # Compare with database
            distances = np.linalg.norm(self.embeddings - embedding, axis=1)
            min_dist_idx = np.argmin(distances)
            min_dist = distances[min_dist_idx]

            # Threshold for recognition
            if min_dist < 0.7:  # Adjust this threshold as needed
                return self.usernames[min_dist_idx]

            return "Unknown"
        except Exception as e:
            print(f"Error in face recognition: {str(e)}")
            return "Unknown"

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

            if track_id not in self.recognized_tracks:
                self.recognized_tracks[track_id] = {"name": "Unknown", "counter": 0}

            self.recognized_tracks[track_id]["counter"] += 1

            # Re-run recognition every 10 frames
            if self.recognized_tracks[track_id]["counter"] % 10 == 0 or self.recognized_tracks[track_id]["name"] == "Unknown":
                name = self.recognize_face(face_crop)
                self.recognized_tracks[track_id]["name"] = name
            
            name_to_display = self.recognized_tracks[track_id]["name"]
            if name_to_display != "Unknown":
                self.recognized_names_set.add(name_to_display)
                authorized.append(name_to_display)
            else:
                unauthorized.append(track_id)

            color = (0, 255, 0) if name_to_display != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID: {track_id}, {name_to_display}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Add recognized names to the main frame
        y_offset = 30
        cv2.putText(frame, "Recognized People:", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        for name in sorted(self.recognized_names_set):
            cv2.putText(frame, name, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 30

        return frame, authorized, unauthorized
