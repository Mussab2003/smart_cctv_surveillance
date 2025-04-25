
from django.urls import path
from ai_models.views.view_user import LoginUser,RegisterUser, user

urlpatterns = [
    # User URLS
    path('login/', LoginUser.as_view()),
    path('register/', RegisterUser.as_view()),
    path('details/', user),

    # Vehicle URLS
    
]
