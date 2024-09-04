from django.shortcuts import render
from . import consumers
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators import gzip # type: ignore
from django.http import StreamingHttpResponse,HttpResponse,HttpResponseBadRequest
from oldhelper.httpcamera import *
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def incoming(request):
    if request.method=='POST':
        print(request.POST['Body'])
        return HttpResponse("Info recived!",status=200)
    return HttpResponseBadRequest()
# Create your views here.
def lobby(request):
    if request.method == 'POST':
        if 'start' in request.POST:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(  # type: ignore
                'esp32_group',
                {
                    'type': 'start_video',
                    'message': "i sent this message from view?"
                }
            )
            return render(request, 'oldhelperfrontend/lobby.html', {'response': 'Stream started'})
        elif 'stop' in request.POST:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(  # type: ignore
                'esp32_group',
                {
                    'type': 'stop_video',
                    'message': "Stop stream"
                }
            )
            return render(request, 'oldhelperfrontend/lobby.html', {'response': 'Stream stopped'})
    return render(request, 'oldhelperfrontend/lobby.html')


#if somehow i get the http video streaming to get to work!
def video(request):
    cam=videocamera()
    return StreamingHttpResponse(gen(cam),
    content_type='multipart/x-mixed-replace; boundary=frame')
    
    #return render (request,'oldhelperfrontend/lobby.html')

