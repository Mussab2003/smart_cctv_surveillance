import cv2
import torch
from .model import FaceRecognitionSystem
from ai_models.utils.save_detection_event import save_detection_event

def run_recognition(video_path=None, owner=None):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    recognition_system = FaceRecognitionSystem(
        yolo_model_path='ai_models/ai/authorized_person_detection/face_detection.pt',
        device=device,
        owner=owner
    )
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    # Create a single window
    cv2.namedWindow("Face Detection and Recognition", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Face Detection and Recognition", 1280, 720)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed_frame, authorized, unauthorized = recognition_system.process_frame(frame)
            
            # Display the processed frame
            cv2.imshow("Face Detection and Recognition", processed_frame)

            # Handle events
            if authorized:
                yield {"event": "authorized", "message": authorized}
            if unauthorized:
                yield {"event": "unauthorized", "message": unauthorized}
                save_detection_event(vehicle=None, owner=owner, event_type="UNAUTHORIZED_ACCESS", 
                                  description="An unauthorized person is detected", video_frame=frame)
            
            # Check for window close
            if cv2.getWindowProperty("Face Detection and Recognition", cv2.WND_PROP_VISIBLE) < 1:
                break

            # Break on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error in face recognition: {str(e)}")
        yield {"event": "error", "message": str(e)}
    finally:
        cap.release()
        cv2.destroyAllWindows()

