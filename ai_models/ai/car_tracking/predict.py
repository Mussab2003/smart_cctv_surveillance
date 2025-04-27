import cv2
from .model import YoloDetector, Tracker
from .utils import find_closest_detection, calculate_movement
import math

detector = YoloDetector(confidence=0.5)
tracker = Tracker()

# def initialize_tracking(video_path, vehicle_location_x, vehicle_location_y):
#     """
#     Initialize vehicle tracking by selecting the closest vehicle to clicked location.
#     Returns cap (open video), tracking_id, and initial bounding box.
#     """

#     cap = cv2.VideoCapture(video_path)
#     if not cap.isOpened():
#         raise ValueError("Error: Unable to open video or stream.")

#     ret, frame = cap.read()
#     if not ret:
#         raise ValueError("Error: Unable to read video/stream frame.")

#     detections = detector.detect(frame)
#     print(detections)
#     closest_detection = find_closest_detection(detections, vehicle_location_x, vehicle_location_y)
#     print("closest detection is: ")
#     print(closest_detection)
#     if closest_detection is None:
#         raise ValueError("No vehicle found near clicked location.")

#     selected_bbox, selected_class, selected_conf = closest_detection
#     selected_detections = [(selected_bbox, selected_class, selected_conf)]

#     tracking_ids, boxes = tracker.track(selected_detections, frame)

#     if not tracking_ids:
#         raise ValueError("Unable to initialize tracking for the selected vehicle.")

#     # Return opened cap, tracking id, and first frame bounding box
#     return cap, tracking_ids[0], boxes[0]


# def track_vehicle_realtime(cap, selected_tracking_id):
#     """
#     Generator that yields when the tracked vehicle moves significantly.
#     Used in Server-Sent Events (SSE).
#     """

#     prev_box = None

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break  # Video/Stream ended

#         detections = detector.detect(frame)
#         tracking_ids, boxes = tracker.track(detections, frame)

#         for track_id, bbox in zip(tracking_ids, boxes):
#             if track_id == selected_tracking_id:
#                 # Compare movement
#                 if prev_box is not None:
#                     movement = calculate_movement(prev_box, bbox)
#                     if movement > 50:  # Movement threshold (pixels)
#                         yield "vehicle_moved"
#                 prev_box = bbox
#                 break  # only track selected vehicle


# def find_closest_box_idx(boxes, target_x, target_y):
#     min_distance = float('inf')
#     closest_idx = None

#     for idx, box in enumerate(boxes):
#         x1, y1, x2, y2 = box
#         center_x = (x1 + x2) / 2
#         center_y = (y1 + y2) / 2
#         distance = math.sqrt((center_x - target_x)**2 + (center_y - target_y)**2)
#         if distance < min_distance:
#             min_distance = distance
#             closest_idx = idx

#     return closest_idx

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

def track_vehicle_realtime(cap, selected_tracking_id):
    prev_box = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        detections = detector.detect(frame)
        tracking_ids, boxes = tracker.track(detections, frame)

        for track_id, bbox in zip(tracking_ids, boxes):
            if track_id == selected_tracking_id:
                print("Tracking Id is: ")
                print(track_id)
                print(bbox)
                if prev_box is not None:
                    movement = calculate_movement(prev_box, bbox)
                    print("Movement is: ")
                    print(movement)
                    if movement > 15:  # Movement threshold (pixels)
                        yield {"event": "vehicle_moved", "message": "Vehicle has moved significantly."}
                prev_box = bbox
                break  # Track only the selected vehicle


    
