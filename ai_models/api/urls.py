
from django.urls import path
from ai_models.views.view_user import LoginUser,RegisterUser, user
from ai_models.views.view_video import VideoUploadView, VideoStreamView, FrameExtractView

urlpatterns = [
    # User URLS
    path('user/login/', LoginUser.as_view()),
    path('user/register/', RegisterUser.as_view()),
    path('user/details/', user),

    # Video URLS
    path('video/upload/', VideoUploadView.as_view()),
    path('video/stream/', VideoStreamView.as_view()),
    path('video/extract-frames/', FrameExtractView.as_view())
    # Vehicle URLS
    
]
