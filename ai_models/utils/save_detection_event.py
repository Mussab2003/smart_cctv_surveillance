from datetime import timedelta
from django.utils import timezone
from ai_models.models import DetectionEvent, Vehicle
from ai_models.utils.supabase_upload import uploadFileToSupabase, getSupabaseFilePath

from rest_framework import status
from rest_framework.response import Response

EVENT_SAVE_COOLDOWN = timedelta(minutes=5)  # 5 min cooldown

def save_detection_event(vehicle, owner, event_type, description="", video_frame=None):
    now = timezone.now()

    # Check for a recent similar event
    recent_event = DetectionEvent.objects.filter(
        vehicle=vehicle,
        event_type=event_type,
        timestamp__gte=now - EVENT_SAVE_COOLDOWN
    ).first()

    if recent_event:
        # Recent similar event exists, do not save again
        print(f"Skipping event save: recent {event_type} already exists.")
        return

    # No recent event, create new DetectionEvent
    
    file_name = f"owner_{owner.id}_{event_type}"
    file_ext = video_frame.name.split('.')[-1]
    
    try:
        response = uploadFileToSupabase('reference_images', 'image', file_name, file_ext, video_frame.read())
        print(response)
    except Exception as upload_error:
        print("Upload failed:", upload_error)
        return Response({'error': str(upload_error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    file_path = getSupabaseFilePath(file_name, 'reference_images')
    print(file_path)
    
    DetectionEvent.objects.create(
        vehicle=vehicle,
        event_type=event_type,
        description=description,
        video_frame=file_path,
    )
    print(f"Saved new {event_type} event for vehicle {vehicle.id}.")
