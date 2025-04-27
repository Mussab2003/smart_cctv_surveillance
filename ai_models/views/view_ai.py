# views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from ai_models.models import Video, Vehicle
from ai_models.ai.car_tracking.predict import track_vehicle_realtime, initialize_tracking_with_buffer, detect_and_select_vehicle

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

            # vehicle_location_x = vehicle.vehicle_location_x * (1920 // 640)
            # vehicle_location_y = vehicle.vehicle_location_y * (1080 // 384) 
            vehicle_location_x = vehicle.vehicle_location_x * (1920 // 640)
            vehicle_location_y = vehicle.vehicle_location_y * (1080 // 384) 

            if vehicle_location_x is None or vehicle_location_y is None:
                return StreamingHttpResponse(self.event_stream(error="Missing coordinates."), content_type='text/event-stream')

            # Start tracking after accumulating a few frames
            cap, selected_tracking_id, initial_box = initialize_tracking_with_buffer(video_path, vehicle_location_x, vehicle_location_y)

            response = StreamingHttpResponse(
                self.event_stream(cap, selected_tracking_id),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        except Exception as e:
            return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

    def event_stream(self, cap=None, selected_tracking_id=None, error=None):
        if error:
            yield f"event: error\ndata: {error}\n\n"
            return

        try:
            for event in track_vehicle_realtime(cap, selected_tracking_id):
                if event["event"] == "vehicle_moved":
                    yield f"event: vehicle_moved\ndata: {event['message']}\n\n"
        except GeneratorExit:
            pass
        finally:
            if cap:
                cap.release()  # Important to close the video capture
    permission_classes = [IsAuthenticated]  # Protect the API

    # def get(self, request, *args, **kwargs):
    #     try:
    #         # 1. Get the user
    #         user = request.user
    #         print(user)
    #         # 2. Fetch the latest or active video for the user
    #         video = Video.objects.filter(owner=user).last()
    #         vehicle = Vehicle.objects.filter(owner=user).last()
    #         if not video:
    #             return StreamingHttpResponse(self.event_stream(error="No video found."), content_type='text/event-stream')

    #         video_path = video.video_url  # Adjust if your field name is different

    #         # 3. Get the clicked coordinates from query params
    #         vehicle_location_x = vehicle.vehicle_location_x
    #         vehicle_location_y = vehicle.vehicle_location_y

    #         print(vehicle_location_x)
    #         print(vehicle_location_y)
    #         if vehicle_location_x is None or vehicle_location_y is None:
    #             return StreamingHttpResponse(self.event_stream(error="Missing coordinates."), content_type='text/event-stream')

    #         # 4. Initialize tracking
    #         cap, selected_tracking_id, initial_box = initialize_tracking(
    #             video_path,
    #             vehicle_location_x,
    #             vehicle_location_y
    #         )

    #         # 5. Start real-time tracking as SSE stream
    #         response = StreamingHttpResponse(
    #             self.event_stream(cap, selected_tracking_id),
    #             content_type='text/event-stream'
    #         )

    #         response['Cache-Control'] = 'no-cache'
    #         return response

    #     except Exception as e:
    #         return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

    # def event_stream(self, cap=None, selected_tracking_id=None, error=None):
    #     if error:
    #         yield f"event: error\ndata: {error}\n\n"
    #         return

    #     try:
    #         for event in track_vehicle_realtime(cap, selected_tracking_id):
    #             # Example: yield data when vehicle moves
    #             if event["event"] == "vehicle_moved":
    #                 yield f"event: vehicle_moved\ndata: {event['message']}\n\n"
    #     except GeneratorExit:
    #         pass  # Handle client disconnect
    #     finally:
    #         if cap:
    #             cap.release()  # Important to close the video capture