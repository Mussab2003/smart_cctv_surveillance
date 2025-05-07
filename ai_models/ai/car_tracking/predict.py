import math
import cv2
from .model import YoloDetector, Tracker
from .utils import find_closest_detection, calculate_movement
from ai_models.utils.save_detection_event import save_detection_event
detector = YoloDetector(confidence=0.5)
tracker = Tracker()

def initialize_tracking_with_buffer( video_path, vehicle_location_x, vehicle_location_y):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error: Unable to open video or stream.")

        frame_buffer = []
        frame_count = 0
        tracking_initialized = False
        selected_tracking_id = None
        initial_box = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break  # End of video

            frame_buffer.append(frame)
            frame_count += 1
            print("Frame Count is ", frame_count)
            if frame_count < 3:
                continue  # Wait until we have 3 frames to initialize tracking

            # Once we have 3 frames, start detecting and tracking
            if not tracking_initialized:
                detections = detect_and_select_vehicle(frame_buffer, vehicle_location_x, vehicle_location_y)
                if detections:
                    print("Detection is : ")
                    selected_tracking_id, initial_box = detections
                    tracking_initialized = True

            if tracking_initialized:
                break

        return cap, selected_tracking_id, initial_box

def detect_and_select_vehicle(frame_buffer, vehicle_location_x, vehicle_location_y):
    detections = []
    print("In this detect function")
    print(detections)
    for frame in frame_buffer:
        frame_detections = detector.detect(frame)
        closest_detection = find_closest_detection(frame_detections, vehicle_location_x, vehicle_location_y)
        if closest_detection:
            detections.append(closest_detection)
    print("length of detection: ", len(detections))
    if len(detections) >= 3:  # Ensure we have detections across 3 frames
        selected_bbox, selected_class, selected_conf = detections[0]
        selected_detections = [(selected_bbox, selected_class, selected_conf)]
        tracking_ids, boxes = tracker.track(selected_detections, frame_buffer[0])  # Initialize tracking with the first frame
        print("Tracking Id is: ", tracking_ids)
        print(boxes)
        
        if tracking_ids:
            print("Tracking Ids: ", tracking_ids)
            return tracking_ids[0], boxes[0]

    return None

def track_vehicle_realtime(cap, selected_tracking_id, vehicle, owner):
    prev_box = None
    frame_count = 0
    skip_frames = 2  # Process every 3rd frame
    show_frames = True  # Enable visualization for testing
    
    # Movement detection parameters
    movement_history = []  # Store recent movements
    history_size = 5  # Number of frames to consider
    cumulative_threshold = 8  # Total movement threshold
    frame_threshold = 2  # Minimum movement per frame to consider
    last_alert_time = 0  # Track when we last sent an alert
    alert_cooldown = 30  # Frames to wait before sending another alert
    movement = 0  # Initialize movement
    cumulative_movement = 0  # Initialize cumulative movement

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % skip_frames != 0:
            continue  # Skip frames to improve performance

        # Detect objects in the current frame
        detections = detector.detect(frame)
        tracking_ids, boxes = tracker.track(detections, frame)

        # Create a copy of the frame for visualization
        display_frame = frame.copy()

        for track_id, bbox in zip(tracking_ids, boxes):
            if track_id == selected_tracking_id:
                if prev_box is not None:
                    movement = calculate_movement(prev_box, bbox)
                    
                    # Add movement to history
                    movement_history.append(movement)
                    if len(movement_history) > history_size:
                        movement_history.pop(0)
                    
                    # Calculate cumulative movement
                    cumulative_movement = sum(movement_history)
                    
                    # Check if we should alert
                    should_alert = (
                        cumulative_movement > cumulative_threshold and  # Total movement threshold
                        movement > frame_threshold and  # Current frame movement threshold
                        (frame_count - last_alert_time) > alert_cooldown  # Cooldown period
                    )
                    
                    if should_alert:
                        yield {"event": "vehicle_moved", "message": "Vehicle has moved significantly."}
                        save_detection_event(vehicle=vehicle, owner=owner, event_type="CAR_MOVEMENT", description="Car moved from its position.", video_frame=frame)
                        last_alert_time = frame_count
                        movement_history.clear()  # Reset history after alert
                
                prev_box = bbox

                # Draw tracking visualization
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display_frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Add movement information
                if prev_box is not None:
                    cv2.putText(display_frame, f"Current Movement: {movement:.2f}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(display_frame, f"Cumulative: {cumulative_movement:.2f}", (x1, y1 - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Resize frame for display
        display_frame = cv2.resize(display_frame, (640, 640))
        
        # Show the frame
        cv2.imshow("Vehicle Tracking", display_frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()



    
