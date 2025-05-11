# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import json
# from .ai.car_tracking.predict import track_vehicle_realtime
# from .ai.fire_smoke_detection.predict import run_fire_smoke_detection
# from .ai.authorized_person_detection.predict import run_authorized_person_detection
# from .ai.intrusion_detection.predict import run_intrusion_detection
# from .ai.combined_detection.predict import run_combined_detection
# from .utils.save_detection_event import save_detection_event

# @csrf_exempt
# def track_vehicle(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             video_path = data.get('video_path')
#             vehicle_location_x = data.get('vehicle_location_x')
#             vehicle_location_y = data.get('vehicle_location_y')
#             vehicle = data.get('vehicle')
#             owner = data.get('owner')

#             if not all([video_path, vehicle_location_x, vehicle_location_y]):
#                 return JsonResponse({'error': 'Missing required parameters'}, status=400)

#             # Run combined detection
#             events = []
#             for event in run_combined_detection(
#                 video_path=video_path,
#                 vehicle_location_x=vehicle_location_x,
#                 vehicle_location_y=vehicle_location_y,
#                 vehicle=vehicle,
#                 owner=owner
#             ):
#                 events.append(event)

#             return JsonResponse({
#                 'status': 'success',
#                 'events': events
#             })

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method'}, status=405)

# @csrf_exempt
# def detect_fire_smoke(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             video_path = data.get('video_path')
#             vehicle = data.get('vehicle')
#             owner = data.get('owner')

#             if not video_path:
#                 return JsonResponse({'error': 'Missing video path'}, status=400)

#             # Run combined detection
#             events = []
#             for event in run_combined_detection(
#                 video_path=video_path,
#                 vehicle=vehicle,
#                 owner=owner
#             ):
#                 if event['event'] in ['fire_detected', 'smoke_detected']:
#                     events.append(event)

#             return JsonResponse({
#                 'status': 'success',
#                 'events': events
#             })

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method'}, status=405)

# @csrf_exempt
# def detect_authorized_person(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             video_path = data.get('video_path')
#             vehicle = data.get('vehicle')
#             owner = data.get('owner')

#             if not video_path:
#                 return JsonResponse({'error': 'Missing video path'}, status=400)

#             # Run combined detection
#             events = []
#             for event in run_combined_detection(
#                 video_path=video_path,
#                 vehicle=vehicle,
#                 owner=owner
#             ):
#                 if event['event'] in ['authorized', 'unauthorized']:
#                     events.append(event)

#             return JsonResponse({
#                 'status': 'success',
#                 'events': events
#             })

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method'}, status=405)

# @csrf_exempt
# def detect_intrusion(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             video_path = data.get('video_path')
#             vehicle = data.get('vehicle')
#             owner = data.get('owner')

#             if not video_path:
#                 return JsonResponse({'error': 'Missing video path'}, status=400)

#             # Run combined detection
#             events = []
#             for event in run_combined_detection(
#                 video_path=video_path,
#                 vehicle=vehicle,
#                 owner=owner
#             ):
#                 if event['event'] == 'suspicious_activity':
#                     events.append(event)

#             return JsonResponse({
#                 'status': 'success',
#                 'events': events
#             })

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method'}, status=405) 