# ai_models/ai/fire_smoke_detection/predict.py

import cv2
from ai_models.ai.fire_smoke_detection.model import FireSmokeDetector  # assuming you saved the class here

# Initialize once
fire_smoke_detector = FireSmokeDetector(confidence=0.5)

def detect_fire_smoke(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
            raise ValueError("Error: Unable to open video or stream.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect fire or smoke
        results, custom_names = fire_smoke_detector.detect(frame)

        fire_detected = False
        smoke_detected = False

        if results and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()  # (x1, y1, x2, y2)
            scores = results[0].boxes.conf.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()

            for box, score, cls in zip(boxes, scores, classes):
                class_id = int(cls)
                label = custom_names.get(class_id, "Unknown")
                x1, y1, x2, y2 = map(int, box)

                if label == "fire":
                    fire_detected = True
                elif label == "smoke":
                    smoke_detected = True

                # Draw boxes
                color = (0, 0, 255) if label == "fire" else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # --- Draw Dialog if detected ---
        if fire_detected or smoke_detected:
            text = "FIRE DETECTED!" if fire_detected else "SMOKE DETECTED!"
            color = (0, 0, 255) if fire_detected else (0, 165, 255)

            cv2.rectangle(frame, (50, 50), (400, 150), (0, 0, 0), -1)  # black box
            cv2.putText(frame, text, (60, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

        # Show window
        cv2.imshow('Fire and Smoke Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Send event if detected
        if fire_detected:
            yield {"event": "fire_detected", "message": "Fire detected!"}
        elif smoke_detected:
            yield {"event": "smoke_detected", "message": "Smoke detected!"}

    cap.release()
    cv2.destroyAllWindows()
