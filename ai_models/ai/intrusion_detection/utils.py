import numpy as np
import cv2

def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union between two bounding boxes.
    """
    # Get coordinates
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    # Calculate intersection area
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    # Calculate union area
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = box1_area + box2_area - intersection
    
    # Calculate IoU
    iou = intersection / union if union > 0 else 0
    
    return iou

def is_person_touching_car(person_box, car_box, threshold=0.1):
    """
    Check if a person is touching or very close to a car.
    """
    iou = calculate_iou(person_box, car_box)
    return iou > threshold

def calculate_movement_speed(track_history, fps=30):
    """
    Calculate the speed of movement for a tracked object.
    """
    if len(track_history) < 2:
        return 0
    
    # Calculate center points
    centers = []
    for box in track_history:
        center_x = (box[0] + box[2]) / 2
        center_y = (box[1] + box[3]) / 2
        centers.append((center_x, center_y))
    
    # Calculate total distance
    total_distance = 0
    for i in range(1, len(centers)):
        dx = centers[i][0] - centers[i-1][0]
        dy = centers[i][1] - centers[i-1][1]
        distance = np.sqrt(dx*dx + dy*dy)
        total_distance += distance
    
    # Calculate speed (pixels per second)
    time_elapsed = len(track_history) / fps
    speed = total_distance / time_elapsed if time_elapsed > 0 else 0
    
    return speed

def is_suspicious_movement(track_history, fps=30, speed_threshold=50):
    """
    Detect suspicious movement patterns.
    """
    if len(track_history) < 10:  # Need enough history
        return False
    
    speed = calculate_movement_speed(track_history, fps)
    return speed > speed_threshold

def draw_tracking_info(frame, track_id, class_name, box, color, additional_info=None):
    """
    Draw tracking information on the frame.
    """
    x1, y1, x2, y2 = map(int, box)
    
    # Draw bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # Draw label
    label = f"{class_name} {track_id}"
    if additional_info:
        label += f" - {additional_info}"
    
    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame 