import cv2
from .model import YoloDetector, Tracker
from .utils import find_closest_detection, calculate_movement
import math

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

# def track_vehicle_realtime(cap, selected_tracking_id):
#     prev_box = None

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break  # End of video

#         detections = detector.detect(frame)
#         tracking_ids, boxes = tracker.track(detections, frame)

#         for track_id, bbox in zip(tracking_ids, boxes):
#             if track_id == selected_tracking_id:
#                 print("Tracking Id is: ")
#                 print(track_id)
#                 print(bbox)
#                 if prev_box is not None:
#                     movement = calculate_movement(prev_box, bbox)
#                     print("Movement is: ")
#                     print(movement)
#                     if movement > 15:  # Movement threshold (pixels)
#                         yield {"event": "vehicle_moved", "message": "Vehicle has moved significantly."}
#                 prev_box = bbox
#                 break  # Track only the selected vehicle

def track_vehicle_realtime(cap, selected_tracking_id):
    prev_box = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Detect objects in the current frame
        detections = detector.detect(frame)
        tracking_ids, boxes = tracker.track(detections, frame)

        for track_id, bbox in zip(tracking_ids, boxes):
            if track_id == selected_tracking_id:
                print("Tracking Id is: ", track_id)
                print("Bounding box: ", bbox)

                # Ensure the bbox values are integers
                x1, y1, x2, y2 = map(int, bbox)

                # Draw the tracking rectangle on the frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green color rectangle

                # Put the tracking ID text on the frame
                cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # If we have a previous bounding box, calculate the movement
                if prev_box is not None:
                    movement = calculate_movement(prev_box, bbox)
                    print("Movement is: ", movement)
                    if movement > 4:  # Movement threshold (pixels)
                        yield {"event": "vehicle_moved", "message": "Vehicle has moved significantly."}

                # Update the previous box
                prev_box = bbox

                # Rescale the frame to 640x640
                frame_rescaled = cv2.resize(frame, (640, 640))

                # Display the frame with the rectangle and tracking ID
                cv2.imshow("Tracking Vehicle", frame_rescaled)

                # Wait for key press to continue (if you want to close the window with a key press)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break  # Press 'q' to exit the loop and stop the tracking

    # Clean up when finished
    cap.release()
    cv2.destroyAllWindows()



    
