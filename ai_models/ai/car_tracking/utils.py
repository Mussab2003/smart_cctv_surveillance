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

def calculate_movement(box1, box2):
    """
    Calculate movement distance between two bounding boxes.
    """
    x1_center = (box1[0] + box1[2]) / 2
    y1_center = (box1[1] + box1[3]) / 2
    x2_center = (box2[0] + box2[2]) / 2
    y2_center = (box2[1] + box2[3]) / 2

    distance = ((x2_center - x1_center) ** 2 + (y2_center - y1_center) ** 2) ** 0.5
    return distance

