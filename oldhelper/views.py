from django.shortcuts import render, redirect
from . import consumers
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators import gzip  # type: ignore
from django.http import StreamingHttpResponse, HttpResponse, HttpResponseBadRequest
from oldhelper.httpcamera import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserForm
from .models import *


def authview(request):
    if request.method == "POST":
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()

            return redirect("login")  # Redirect to the login page
    else:
        form = CustomUserForm()

    return render(request, "registration/signup.html", {"form": form})


@csrf_exempt
def incoming(request):
    if request.method == "POST":
        # print(request.POST)
        print(request.POST["Body"], request.POST["WaId"])

        try:
            income = IncomingMessages.objects.create(
                sender=f'+{request.POST["WaId"]}', content=request.POST["Body"]
            )
            income.save()
        except Exception as e:
            print(f"Problem occured while saving to db {e}")
            return HttpResponseBadRequest()
        return HttpResponse("Info recived!", status=200)
    return HttpResponseBadRequest()


@login_required(login_url="/auth/login/")
# Create your views here.
def lobby(request):
    if request.method == "POST":
        if "start" in request.POST:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(  # type: ignore
                "esp32_group",
                {"type": "start_video", "message": "i sent this message from view?"},
            )
            return render(
                request, "oldhelperfrontend/lobby.html", {"response": "Stream started"}
            )
        elif "stop" in request.POST:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(  # type: ignore
                "esp32_group", {"type": "stop_video", "message": "Stop stream"}
            )
            return render(
                request, "oldhelperfrontend/lobby.html", {"response": "Stream stopped"}
            )
    return render(request, "oldhelperfrontend/lobby.html")


# if somehow i get the http video streaming to get to work!
def video(request):
    cam = videocamera()
    return StreamingHttpResponse(
        gen(cam), content_type="multipart/x-mixed-replace; boundary=frame"
    )

    # return render (request,'oldhelperfrontend/lobby.html')
