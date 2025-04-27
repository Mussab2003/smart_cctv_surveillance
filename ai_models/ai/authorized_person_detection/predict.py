import cv2
import torch
from .model import FaceRecognitionSystem
from ai_models.utils.save_detection_event import save_detection_event

def run_recognition(video_path=None, owner=None):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    recognition_system = FaceRecognitionSystem(
        yolo_model_path='ai_models/ai/authorized_person_detection/face_detection.pt',
        face_db_path='ai_models/ai/authorized_person_detection/face_db.pkl',
        device=device
    )
    
    #cap = cv2.VideoCapture(video_path)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame, authorized, unauthorized = recognition_system.process_frame(frame)
        cv2.imshow("Face Detection and Recognition", processed_frame)

        if authorized:
            yield {"event" : "authorized", "message": authorized}
        if unauthorized:
            yield {"event" : "unauthorized", "message": unauthorized}
            save_detection_event(vehicle=None, owner=owner, event_type="UNAUTHORIZED_ACCESS", description="An unauthorized person is detected", video_frame=frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

