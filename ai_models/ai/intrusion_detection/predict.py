import cv2
from .model import IntrusionDetector
from ai_models.utils.save_detection_event import save_detection_event

# Initialize detector
intrusion_detector = IntrusionDetector(confidence=0.5)

def detect_intrusion(video_path, owner):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Error: Unable to open video or stream.")
    
    frame_count = 0
    last_alert_time = 0
    alert_cooldown = 30  # frames to wait between alerts
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Detect and track objects
        tracks, suspicious_events = intrusion_detector.detect(frame)
        
        # Create display frame
        display_frame = frame.copy()
        
        # Draw tracking boxes and labels
        for track in tracks:
            if not track.is_confirmed():
                continue
                
            track_id = track.track_id
            ltrb = track.to_ltrb()
            class_id = track.get_class()
            
            # Get color based on class and suspicious behavior
            if class_id == 2:  # Person
                color = (0, 0, 255)  # Red for person
                label = f"Person {track_id}"
            else:  # Car or bike
                color = (0, 255, 0)  # Green for vehicle
                label = f"Vehicle {track_id}"
            
            # Draw box
            x1, y1, x2, y2 = map(int, ltrb)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Process suspicious events
        for event in suspicious_events:
            if frame_count - last_alert_time > alert_cooldown:
                if event['type'] == 'suspicious_loitering':
                    message = f"Suspicious activity detected: Person {event['person_id']} loitering near vehicle {event['car_id']} for {event['duration']} frames"
                    yield {"event": "suspicious_activity", "message": message}
                    save_detection_event(
                        vehicle=None,
                        owner=owner,
                        event_type="SUSPICIOUS_ACTIVITY",
                        description=message,
                        video_frame=frame
                    )
                    last_alert_time = frame_count
                    
                    # Draw warning on frame
                    cv2.putText(
                        display_frame,
                        "SUSPICIOUS ACTIVITY DETECTED!",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2
                    )
        
        # Show the frame
        display_frame = cv2.resize(display_frame, (640, 640))
        cv2.imshow("Intrusion Detection", display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows() 