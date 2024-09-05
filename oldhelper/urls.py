from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.authview, name="authview"),
    path("auth/", include("django.contrib.auth.urls")),
    path("lobby/", views.lobby, name="lobby"),
    path("feed/", views.video, name="video_feed"),
    path("incoming/", views.incoming, name="incoming"),
]  # type: ignore
