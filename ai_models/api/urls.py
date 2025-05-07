from django.urls import path
from ai_models.views.view_user import LoginUser,RegisterUser, user
from ai_models.views.view_video import VideoUploadView, VideoStreamView, FrameExtractView
from ai_models.views.view_vehicle import VehicleView, VehicleLocationUpdateView
from ai_models.views.view_ai import VehicleTrackingSSEView, FireSmokeDetectionSSE, AuthorizedPersonDetectionSSE, CombinedDetectionSSE

urlpatterns = [
    # User URLS
    path('user/login/', LoginUser.as_view()),
    path('user/register/', RegisterUser.as_view()),
    path('user/details/', user),

    # Video URLS
    path('video/upload/', VideoUploadView.as_view()),
    path('video/stream/', VideoStreamView.as_view()),
    path('video/extract-frames/', FrameExtractView.as_view()),
    
    # Vehicle URLS
    path('vehicle/', VehicleView.as_view()),
    path('vehicle/location/', VehicleLocationUpdateView.as_view()),
    
    # AI Models Views
    path('ai/vehicle/track/', VehicleTrackingSSEView.as_view()),
    path('ai/fire-smoke/detect/', FireSmokeDetectionSSE.as_view()),
    path('ai/authorized-person/detect/', AuthorizedPersonDetectionSSE.as_view()),
    path('ai/combined-detect/', CombinedDetectionSSE.as_view()),
    # path('ai/intrusion-detect/', IntrusionDetectionSSE.as_view())
]
