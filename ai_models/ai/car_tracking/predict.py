# ai_models/ai/car_tracking/predict.py

import cv2
from .model import YoloDetector, Tracker
from .utils import find_closest_detection, calculate_movement

# Global Model Loading
detector = YoloDetector(confidence=0.5)
tracker = Tracker()

def track_vehicle_sse(reference_video_path, vehicle_location_x, vehicle_location_y):
    """
    Generator function to track a specific vehicle and yield updates when it moves.
    Used for Server-Sent Events (SSE).
    """
    cap = cv2.VideoCapture(reference_video_path)

    if not cap.isOpened():
        yield {"event": "error", "message": "Error: Unable to open video stream."}
        return

    # Read the first frame
    ret, frame = cap.read()
    if not ret:
        yield {"event": "error", "message": "Error: Unable to read the video frame."}
        return

    # Detect vehicles in the first frame
    detections = detector.detect(frame)
    closest_detection = find_closest_detection(detections, vehicle_location_x, vehicle_location_y)

    if closest_detection is None:
        yield {"event": "error", "message": "No vehicle found near clicked location."}
        return

    selected_bbox, selected_class, selected_conf = closest_detection
    selected_detections = [(selected_bbox, selected_class, selected_conf)]

    tracking_ids, boxes = tracker.track(selected_detections, frame)

    if not tracking_ids:
        yield {"event": "error", "message": "Tracking ID could not be assigned."}
        return

    selected_tracking_id = tracking_ids[0]
    last_known_box = boxes[0]

    # Start reading subsequent frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Run full detection and tracking
        detections = detector.detect(frame)
        tracking_ids, boxes = tracker.track(detections, frame)

        for tracking_id, bbox in zip(tracking_ids, boxes):
            if tracking_id == selected_tracking_id:
                moved = calculate_movement(last_known_box, bbox)
                if moved:
                    last_known_box = bbox
                    yield {
                        "event": "car_moved",
                        "tracking_id": selected_tracking_id,
                        "bounding_box": bbox
                    }

    cap.release()
    yield {"event": "end", "message": "Video finished or stream ended."}
