# views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from ai_models.models import Video, Vehicle
from ai_models.ai.car_tracking.predict import track_vehicle_realtime, initialize_tracking_with_buffer
from ai_models.ai.fire_smoke_detection.predict import detect_fire_smoke
from ai_models.ai.authorized_person_detection.predict import run_recognition

class VehicleTrackingSSEView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            video = Video.objects.filter(owner=user).last()
            vehicle = Vehicle.objects.filter(owner=user).last()

            if not video:
                return StreamingHttpResponse(self.event_stream(error="No video found."), content_type='text/event-stream')

            video_path = video.video_url

            vehicle_location_x = vehicle.vehicle_location_x
            vehicle_location_y = vehicle.vehicle_location_y
             

            if vehicle_location_x is None or vehicle_location_y is None:
                return StreamingHttpResponse(self.event_stream(error="Missing coordinates."), content_type='text/event-stream')

            # Start tracking after accumulating a few frames
            cap, selected_tracking_id, initial_box = initialize_tracking_with_buffer(video_path, vehicle_location_x, vehicle_location_y)

            response = StreamingHttpResponse(
                self.event_stream(cap = cap, selected_tracking_id = selected_tracking_id, vehicle = vehicle, owner=user),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        except Exception as e:
            return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

    def event_stream(self, cap=None, selected_tracking_id=None, error=None, vehicle = None, owner = None):
        if error:
            yield f"event: error\ndata: {error}\n\n"
            return

        try:
            for event in track_vehicle_realtime(cap, selected_tracking_id, vehicle, owner):
                if event["event"] == "vehicle_moved":
                    yield f"event: vehicle_moved\ndata: {event['message']}\n\n"
        except GeneratorExit:
            pass
        finally:
            if cap:
                cap.release()  # Important to close the video capture
    
    
class FireSmokeDetectionSSE(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            video = Video.objects.filter(owner=user).last()

            if not video:
                return StreamingHttpResponse(self.event_stream(error="No video found."), content_type='text/event-stream')

            video_path = video.video_url


            response = StreamingHttpResponse(
                self.event_stream(video_path=video_path, owner=user),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        except Exception as e:
            return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

    def event_stream(self, video_path, error=None, owner=None):
        if error:
            yield f"event: error\ndata: {error}\n\n"
            return

        try:
            for event in detect_fire_smoke(video_path, owner):
                if event["event"] == "fire_detected":
                    yield f"event: Fire Detected\ndata: {event['message']}\n\n"
                if event["event"] == "smoke_detected":
                    yield f"event: Smoke Detected\ndata: {event['message']}\n\n"
        except GeneratorExit:
            pass
        
class AuthorizedPersonDetectionSSE(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            video = Video.objects.filter(owner=user).last()

            if not video:
                return StreamingHttpResponse(self.event_stream(error="No video found."), content_type='text/event-stream')

            video_path = video.video_url

            response = StreamingHttpResponse(
                self.event_stream(video_path=video_path, owner=user),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        except Exception as e:
            return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

    def event_stream(self, video_path, error=None, owner=None):
        if error:
            yield f"event: error\ndata: {error}\n\n"
            return

        try:
            for event in run_recognition(video_path, owner):
                if event["event"] == "authorized":
                    yield f"event: Authorized person detected \ndata: {event['message']}\n\n"
                elif event["event"] == "unauthorized":
                    yield f"event: Unknown person detected\ndata: {event['message']}\n\n"
        except GeneratorExit:
            pass

        