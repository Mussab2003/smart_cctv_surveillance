from ultralytics import YOLO
import torch
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

class IntrusionDetector:
    def __init__(self, confidence=0.5):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO("ai_models/ai/intrusion_detection/intrusion_detection.pt")
        self.tracker = DeepSort(max_age=30)
        self.confidence = confidence
        
        # Tracking data
        self.tracked_objects = {}  # track_id -> {class_id, last_position, loitering_time}
        self.loitering_threshold = 30  # frames to consider as loitering
        self.proximity_threshold = 100  # pixels to consider as "near" vehicle
        
        if self.device == 'cuda':
            print("CUDA Available:", torch.cuda.is_available())
            print("GPU:", torch.cuda.get_device_name(0))
            self.model.to("cuda")
        else:
            print("CUDA not available, using CPU.")

    def detect(self, frame):
        # Detect objects
        results = self.model.predict(frame, conf=self.confidence)
        detections = []

        # Process detections
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                detections.append(([x1, y1, w, h], conf, class_id, None))

        # Track objects
        tracks = self.tracker.update_tracks(detections, frame=frame)
        
        # Update tracking data and check for suspicious behavior
        suspicious_events = self.update_tracking_data(tracks)
        
        return tracks, suspicious_events

    def update_tracking_data(self, tracks):
        suspicious_events = []
        current_tracks = set()

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            current_tracks.add(track_id)
            ltrb = track.to_ltrb()
            class_id = track.det_class  # Changed from get_class() to det_class

            # Initialize tracking data for new tracks
            if track_id not in self.tracked_objects:
                self.tracked_objects[track_id] = {
                    'class_id': class_id,
                    'last_position': ltrb,
                    'loitering_time': 0
                }
            else:
                # Update existing track
                track_data = self.tracked_objects[track_id]
                
                # Check for movement
                last_pos = track_data['last_position']
                current_pos = ltrb
                movement = np.sqrt(
                    (current_pos[0] - last_pos[0])**2 + 
                    (current_pos[1] - last_pos[1])**2
                )

                # Update loitering time if minimal movement
                if movement < 5:  # threshold for considering as "not moving"
                    track_data['loitering_time'] += 1
                else:
                    track_data['loitering_time'] = 0

                # Check for suspicious behavior
                if track_data['loitering_time'] > self.loitering_threshold:
                    # Check if near any vehicle
                    for other_track in tracks:
                        if other_track.track_id != track_id and other_track.det_class == 2:  # Assuming 2 is vehicle class
                            other_ltrb = other_track.to_ltrb()
                            distance = np.sqrt(
                                (current_pos[0] - other_ltrb[0])**2 + 
                                (current_pos[1] - other_ltrb[1])**2
                            )
                            
                            if distance < self.proximity_threshold:
                                suspicious_events.append({
                                    'type': 'suspicious_loitering',
                                    'person_id': track_id,
                                    'car_id': other_track.track_id
                                })
                                break

                # Update position
                track_data['last_position'] = current_pos

        # Clean up old tracks
        for track_id in list(self.tracked_objects.keys()):
            if track_id not in current_tracks:
                del self.tracked_objects[track_id]

        return suspicious_events 