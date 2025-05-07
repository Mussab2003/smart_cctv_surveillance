import cv2
import torch
from ai_models.ai.car_tracking.model import YoloDetector, Tracker
from ai_models.ai.fire_smoke_detection.model import FireSmokeDetector
from ai_models.ai.authorized_person_detection.model import FaceRecognitionSystem
# from ai_models.ai.intrusion_detection.model import IntrusionDetector
from ai_models.utils.save_detection_event import save_detection_event
from ai_models.ai.car_tracking.utils import calculate_movement

class CombinedDetector:
    def __init__(self):
        print("Initializing CombinedDetector...")
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        
        # Initialize all detectors
        print("Initializing car detector...")
        self.car_detector = YoloDetector(confidence=0.5)
        print("Initializing fire detector...")
        self.fire_detector = FireSmokeDetector(confidence=0.4)
        print("Initializing person detector...")
        self.person_detector = FaceRecognitionSystem(
            yolo_model_path='ai_models/ai/authorized_person_detection/face_detection.pt',
            face_db_path='ai_models/ai/authorized_person_detection/face_db.pkl',
            device=self.device
        )
        # self.intrusion_detector = IntrusionDetector(confidence=0.5)
        self.tracker = Tracker()
        
        # Alert cooldown parameters
        self.frame_count = 0
        self.last_alert_time = 0
        self.alert_cooldown = 30

        # Movement detection parameters
        self.movement_history = []
        self.history_size = 5
        self.cumulative_threshold = 8
        self.frame_threshold = 2
        self.prev_box = None
        print("CombinedDetector initialization complete.")

    def process_frame(self, frame, selected_tracking_id=None, vehicle=None, owner=None):
        self.frame_count += 1
        display_frame = frame.copy()
        events = []

        # Car Tracking
        if selected_tracking_id:
            print(f"Processing car tracking for ID: {selected_tracking_id}")
            car_detections = self.car_detector.detect(frame)
            car_tracking_ids, car_boxes = self.tracker.track(car_detections, frame)
            print(f"Car tracking results - IDs: {car_tracking_ids}, Boxes: {car_boxes}")
            
            for track_id, bbox in zip(car_tracking_ids, car_boxes):
                if track_id == selected_tracking_id:
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, f"Car {track_id}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Check for movement
                    if self.prev_box is not None:
                        movement = calculate_movement(self.prev_box, bbox)
                        self.movement_history.append(movement)
                        if len(self.movement_history) > self.history_size:
                            self.movement_history.pop(0)
                        
                        cumulative_movement = sum(self.movement_history)
                        print(f"Movement detected - Current: {movement:.2f}, Cumulative: {cumulative_movement:.2f}")
                        
                        if (cumulative_movement > self.cumulative_threshold and 
                            movement > self.frame_threshold and 
                            (self.frame_count - self.last_alert_time) > self.alert_cooldown):
                            event = {"event": "vehicle_moved", "message": "Vehicle has moved significantly."}
                            print(f"Vehicle movement event: {event}")
                            events.append(event)
                            save_detection_event(vehicle=vehicle, owner=owner, event_type="CAR_MOVEMENT", description="Car moved from its position.", video_frame=frame)
                            self.last_alert_time = self.frame_count
                            self.movement_history.clear()
                    
                    self.prev_box = bbox

        # Fire/Smoke Detection
        print("Processing fire/smoke detection...")
        fire_results, custom_names = self.fire_detector.detect(frame)
        if fire_results and fire_results[0].boxes is not None:
            boxes = fire_results[0].boxes.xyxy.cpu().numpy()
            scores = fire_results[0].boxes.conf.cpu().numpy()
            classes = fire_results[0].boxes.cls.cpu().numpy()
            
            for box, score, cls in zip(boxes, scores, classes):
                class_id = int(cls)
                label = custom_names.get(class_id, "Unknown")
                x1, y1, x2, y2 = map(int, box)
                color = (0, 0, 255) if label == "fire" else (0, 165, 255)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                print(f"Detected {label} with confidence {score:.2f}")
                
                if self.frame_count - self.last_alert_time > self.alert_cooldown:
                    if label == "fire":
                        event = {"event": "fire_detected", "message": "Fire detected!"}
                        print(f"Fire detection event: {event}")
                        events.append(event)
                        save_detection_event(vehicle=None, owner=owner, event_type="ENVIRONMENTAL_HAZARD", description="A fire has occurred", video_frame=frame)
                    elif label == "smoke":
                        event = {"event": "smoke_detected", "message": "Smoke detected!"}
                        print(f"Smoke detection event: {event}")
                        events.append(event)
                        save_detection_event(vehicle=None, owner=owner, event_type="ENVIRONMENTAL_HAZARD", description="Smoke has occurred", video_frame=frame)
                    self.last_alert_time = self.frame_count

        # Person Detection
        print("Processing person detection...")
        processed_frame, authorized, unauthorized = self.person_detector.process_frame(frame)
        if authorized:
            event = {"event": "authorized", "message": authorized}
            print(f"Authorized person event: {event}")
            events.append(event)
        if unauthorized:
            event = {"event": "unauthorized", "message": unauthorized}
            print(f"Unauthorized person event: {event}")
            events.append(event)
            save_detection_event(vehicle=None, owner=owner, event_type="UNAUTHORIZED_ACCESS", description="An unauthorized person is detected", video_frame=frame)

        # # Intrusion Detection (commented out for now)
        # tracks, suspicious_events = self.intrusion_detector.detect(frame)
        # for event in suspicious_events:
        #     if self.frame_count - self.last_alert_time > self.alert_cooldown:
        #         if event['type'] == 'suspicious_loitering':
        #             message = f"Suspicious activity detected: Person {event['person_id']} loitering near vehicle {event['car_id']}"
        #             events.append({"event": "suspicious_activity", "message": message})
        #             save_detection_event(vehicle=None, owner=owner, event_type="SUSPICIOUS_ACTIVITY", description=message, video_frame=frame)
        #             self.last_alert_time = self.frame_count

        print(f"Total events generated: {len(events)}")
        return display_frame, events

def run_combined_detection(video_path, vehicle_location_x=None, vehicle_location_y=None, vehicle=None, owner=None):
    print(f"Starting combined detection with video: {video_path}")
    detector = CombinedDetector()
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError("Error: Unable to open video or stream.")

    # Initialize car tracking if coordinates are provided
    selected_tracking_id = None
    if vehicle_location_x is not None and vehicle_location_y is not None:
        print(f"Initializing car tracking at coordinates: ({vehicle_location_x}, {vehicle_location_y})")
        from ai_models.ai.car_tracking.predict import initialize_tracking_with_buffer
        cap_car, selected_tracking_id, initial_box = initialize_tracking_with_buffer(
            video_path, vehicle_location_x, vehicle_location_y
        )
        cap_car.release()
        print(f"Car tracking initialized with ID: {selected_tracking_id}")

    # Skip frames for better performance
    skip_frames = 2
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video stream")
            break

        frame_count += 1
        if frame_count % skip_frames != 0:
            continue

        print(f"\nProcessing frame {frame_count}")
        # Process frame with all detectors
        display_frame, events = detector.process_frame(
            frame, 
            selected_tracking_id=selected_tracking_id,
            vehicle=vehicle,
            owner=owner
        )

        # Show the combined frame
        display_frame = cv2.resize(display_frame, (640, 640))
        cv2.imshow("Combined Detection", display_frame)
        
        # Yield any events
        for event in events:
            print(f"Yielding event: {event}")
            yield event

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User requested to quit")
            break

    print("Cleaning up resources")
    cap.release()
    cv2.destroyAllWindows() 