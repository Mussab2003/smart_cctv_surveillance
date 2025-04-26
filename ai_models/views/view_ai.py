# views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from ai_models.models import Video
from ai_models.ai.car_tracking.predict import track_vehicle_sse

class VehicleTrackingSSEAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            # Get the latest video for the user
            video = Video.objects.filter(user=user).latest('created_at')
            reference_video_path = video.video_path
            vehicle_location_x = video.vehicle_location_x
            vehicle_location_y = video.vehicle_location_y

        except Video.DoesNotExist:
            return StreamingHttpResponse("No video found for this user.", status=404)

        # Start the tracking generator
        event_stream = track_vehicle_sse(reference_video_path, vehicle_location_x, vehicle_location_y)

        def event_generator():
            for event in event_stream:
                yield f"event: {event['event']}\ndata: {event}\n\n"

        return StreamingHttpResponse(event_generator(), content_type='text/event-stream')
