from datetime import timedelta
from django.utils import timezone
from ai_models.models import DetectionEvent, Vehicle
from ai_models.utils.supabase_upload import uploadFileToSupabase, getSupabaseFilePath

from rest_framework import status
from rest_framework.response import Response
import cv2
import numpy as np
from io import BytesIO


EVENT_SAVE_COOLDOWN = timedelta(minutes=5)  # 5 min cooldown

def get_image_extension_and_data(frame, format='jpeg'):
    # Encode the frame as an image (in the specified format)
    if format == 'jpeg':
        _, img_encoded = cv2.imencode('.jpg', frame)
    elif format == 'png':
        _, img_encoded = cv2.imencode('.png', frame)
    else:
        raise ValueError("Unsupported format. Use 'jpeg' or 'png'.")

    # Create a byte stream to hold the encoded image data
    img_bytes = BytesIO(img_encoded.tobytes())
    
    # Return the image data and extension
    return img_bytes, format

# Example usage in your `save_detection_event` function
def save_detection_event(vehicle, owner, event_type, description="", video_frame=None):
    # Get the image data (NumPy array) and extension
    # img_bytes, file_ext = get_image_extension_and_data(video_frame, format='jpeg')

    # Construct the file name
    # file_name = f"vehicle_{vehicle.id}_{event_type}"

    # try:
    #     # Upload to Supabase (assuming uploadFileToSupabase expects bytes)
    #     response = uploadFileToSupabase('detection_images', 'image', file_name, file_ext, img_bytes)
    #     print(response)
    # except Exception as upload_error:
    #     print("Upload failed:", upload_error)
    #     raise upload_error  # Let the view handle the error response

    # # After uploading, get the file path from Supabase
    # file_path = getSupabaseFilePath(file_name, 'detection_images')
    # print(file_path)

    # Create and save the DetectionEvent
    DetectionEvent.objects.create(
        vehicle=vehicle,
        event_type=event_type,
        description=description,
        owner=owner
    )
    print(f"Saved new {event_type}")
