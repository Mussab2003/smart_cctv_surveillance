import math

def find_closest_detection(detections, target_x, target_y):
    """
    Find the detection whose center is closest to the user-clicked (x, y) location.
    """
    min_distance = float('inf')
    closest_detection = None

    for bbox, class_num, conf in detections:
        x1, y1, w, h = bbox
        center_x = x1 + w / 2
        center_y = y1 + h / 2

        distance = math.sqrt((center_x - target_x)**2 + (center_y - target_y)**2)
        if distance < min_distance:
            min_distance = distance
            closest_detection = (bbox, class_num, conf)

    return closest_detection
