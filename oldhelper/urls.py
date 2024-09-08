from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.authview, name="authview"),
    path("auth/", include("django.contrib.auth.urls")),
    path("lobby/", views.lobby, name="lobby"),
    path("feed/", views.video, name="video_feed"),
    path("incoming/", views.incoming, name="incoming"),
    path("emer/ins/", views.emer_form, name="emer_insert"),
    path("emer/li/", views.emer_list, name="emer_list"),
    path("emer/ins/<int:id>/", views.emer_form, name="emer_update"),
    path("emer/delete/<int:id>/", views.emer_delete, name="emer_delete"),
    path("pred/li/", views.pred_list, name="pred_list"),
    path("pred/delete/<int:id>/", views.pred_delete, name="pred_delete"),
]  # type: ignore
