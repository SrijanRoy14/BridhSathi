from django.urls import path
from .import views

urlpatterns=[
    path('',views.lobby,name="lobby"),
    path('feed/',views.video,name="video_feed"),
    path('incoming/',views.incoming,name="incoming"),]#type: ignore
    