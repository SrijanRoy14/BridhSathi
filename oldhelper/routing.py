from django.urls import re_path
from .import consumers

websocket_urlpatterns=[
    re_path(r'ws/testing/',consumers.feedfront.as_asgi()),
    re_path(r'ws/video/', consumers.VideoConsumer.as_asgi()),  # WebSocket URL for video streaming
]
