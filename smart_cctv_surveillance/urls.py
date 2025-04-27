from django.contrib import admin
from django.urls import path, include
from ai_models.api import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/models/', include(urls))
]
