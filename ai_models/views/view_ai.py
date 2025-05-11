# views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from ai_models.models import Video, Vehicle
from ai_models.ai.car_tracking.predict import track_vehicle_realtime, initialize_tracking_with_buffer
from ai_models.ai.fire_smoke_detection.predict import detect_fire_smoke
from ai_models.ai.authorized_person_detection.predict import run_recognition
# from ai_models.ai.intrusion_detection.predict import detect_intrusion
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import cv2
import time

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

class CombinedDetectionSSE(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            video = Video.objects.filter(owner=user).last()
            vehicle = Vehicle.objects.filter(owner=user).last()

            if not video:
                return StreamingHttpResponse(self.event_stream(error="No video found."), content_type='text/event-stream')

            video_path = video.video_url
            vehicle_location_x = vehicle.vehicle_location_x if vehicle else None
            vehicle_location_y = vehicle.vehicle_location_y if vehicle else None

            response = StreamingHttpResponse(
                self.event_stream(
                    video_path=video_path,
                    vehicle_location_x=vehicle_location_x,
                    vehicle_location_y=vehicle_location_y,
                    vehicle=vehicle,
                    owner=user
                ),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        except Exception as e:
            return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

    def event_stream(self, video_path=None, vehicle_location_x=None, vehicle_location_y=None, error=None, vehicle=None, owner=None):
        if error:
            yield f"event: error\ndata: {error}\n\n"
            return

        try:
            # Create queues for each model's results
            car_queue = Queue()
            fire_queue = Queue()
            person_queue = Queue()

            # Initialize video capture
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                yield f"event: error\ndata: Unable to open video stream\n\n"
                return

            # Initialize car tracking if coordinates are provided
            selected_tracking_id = None
            if vehicle_location_x is not None and vehicle_location_y is not None:
                cap_car, selected_tracking_id, initial_box = initialize_tracking_with_buffer(
                    video_path, vehicle_location_x, vehicle_location_y
                )
                cap_car.release()

            def car_tracking_thread():
                try:
                    for event in track_vehicle_realtime(cap, selected_tracking_id, vehicle, owner):
                        car_queue.put(event)
                except Exception as e:
                    car_queue.put({"event": "error", "message": f"Car tracking error: {str(e)}"})

            def fire_smoke_thread():
                try:
                    for event in detect_fire_smoke(video_path, owner):
                        fire_queue.put(event)
                except Exception as e:
                    fire_queue.put({"event": "error", "message": f"Fire detection error: {str(e)}"})

            def person_detection_thread():
                try:
                    for event in run_recognition(video_path, owner):
                        person_queue.put(event)
                except Exception as e:
                    person_queue.put({"event": "error", "message": f"Person detection error: {str(e)}"})

            # Start all threads
            with ThreadPoolExecutor(max_workers=3) as executor:
                if selected_tracking_id:
                    executor.submit(car_tracking_thread)
                executor.submit(fire_smoke_thread)
                executor.submit(person_detection_thread)

                # Process results from all queues
                while True:
                    # Check car tracking results
                    if not car_queue.empty():
                        event = car_queue.get()
                        yield f"event: {event['event']}\ndata: {event['message']}\n\n"

                    # Check fire/smoke detection results
                    if not fire_queue.empty():
                        event = fire_queue.get()
                        yield f"event: {event['event']}\ndata: {event['message']}\n\n"

                    # Check person detection results
                    if not person_queue.empty():
                        event = person_queue.get()
                        yield f"event: {event['event']}\ndata: {event['message']}\n\n"

                    # Check if video is still playing
                    if not cap.isOpened():
                        break

                    # Small delay to prevent CPU overuse
                    time.sleep(0.1)

        except GeneratorExit:
            pass
        finally:
            if cap:
                cap.release()
            cv2.destroyAllWindows()
        
# class IntrusionDetectionSSE(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:
#             user = request.user
#             video = Video.objects.filter(owner=user).last()

#             if not video:
#                 return StreamingHttpResponse(self.event_stream(error="No video found."), content_type='text/event-stream')

#             video_path = video.video_url

#             response = StreamingHttpResponse(
#                 self.event_stream(video_path=video_path, owner=user),
#                 content_type='text/event-stream'
#             )
#             response['Cache-Control'] = 'no-cache'
#             return response

#         except Exception as e:
#             return StreamingHttpResponse(self.event_stream(error=str(e)), content_type='text/event-stream')

#     def event_stream(self, video_path=None, error=None, owner=None):
#         if error:
#             yield f"event: error\ndata: {error}\n\n"
#             return

#         try:
#             for event in detect_intrusion(video_path, owner):
#                 if event["event"] == "suspicious_activity":
#                     yield f"event: suspicious_activity\ndata: {event['message']}\n\n"
#         except GeneratorExit:
#             pass
        