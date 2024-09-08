import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import cv2
import base64
import asyncio
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.shortcuts import render
from datetime import datetime
import os
import uuid
from channels.db import database_sync_to_async
from oldhelper.models import *
from django.contrib.auth.models import User
from twilio.rest import Client
from dotenv import load_dotenv
from django.core.files import File
from django.utils import timezone
import time

# from geopy.geocoders import Nominatim
import geocoder


load_dotenv()


class feedfront(WebsocketConsumer):

    def connect(self):
        self.accept()

        self.send(text_data="hello esp32! we are connected ")
        self.room_group_name = "esp32_group2"

        self.channel_name = self.channel_name
        async_to_sync(self.channel_layer.group_add)(  # type: ignore
            self.room_group_name, self.channel_name
        )

    def send_frame(self, event):
        frame_data = event["frame_data"]

        if frame_data is not None:  # type: ignore
            # print("receiving frame buffer")
            self.send(bytes_data=frame_data)

            print("Frame sent at:", time.strftime("%H:%M:%S"))

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        if text_data is not None:
            async_to_sync(self.channel_layer.group_send)(  # type: ignore
                "esp32_group3",
                {"type": "pred_res", "data": text_data},  # Send predicted class
            )
        # asyncio.sleep(0.03)

        return super().receive(text_data, bytes_data)


class VideoConsumer(AsyncWebsocketConsumer):
    API_KEY = os.getenv("account_sid")
    API_SECRET = os.getenv("auth_token")
    dirfordb = None
    prediction_labels = "fine danger stolen call".split(" ")
    user_id = None

    async def initcamera(self):
        self.video_capture = cv2.VideoCapture(0)
        self.is_streaming = False

    async def connect(self):

        if self.scope["user"].is_authenticated:
            await self.accept()

            await self.initcamera()
            self.video_capture = cv2.VideoCapture(0)
            self.is_streaming = False

            self.account_sid = self.API_KEY
            self.auth_token = self.API_SECRET
            self.client = Client(self.account_sid, self.auth_token)

            self.room_group_name = "esp32_group3"
            self.channel_name = self.channel_name

            self.user_id = self.scope["user"].id

            # self.user=self.scope['user']
            """for pred in self.prediction_labels:
                await self.perform_action(pred)"""
            # await self.perform_action("danger")
            # await self.delete_all()
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)  # type: ignore
            print(f"VideoConsumer connected and joined group: {self.room_group_name}")

            self.video_capture = cv2.VideoCapture(0)
            self.is_streaming = False

        else:
            await self.close()

    async def receive(self, text_data, bytes_data=None):

        try:
            data = json.loads(text_data)

            action = data.get("action")

            if action == "start":
                await self.start_video("start")
            elif action == "capture":
                await self.capture_image(action, "Saved_Image", None)
            elif action == "capturemulti":
                label = data.get("label")
                number = data.get("number")
                # print(label,number)

                response = await self.capture_image(action, label, number)

                async def sendresponse():
                    print(response)
                    await self.send(text_data="Done")

                await asyncio.create_task(sendresponse())

            elif action == "stop":
                await self.stop_video(None)
        except json.JSONDecodeError:
            print("Received non-JSON message")

    async def click_pic(self, dir_name, label):
        success, frame = self.video_capture.read()
        if success:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            newuuid = uuid.uuid4()
            print(f"saved image for {label}")
            # frame=cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(dir_name + f"/{label}_{newuuid}.jpeg", frame)
            if label in self.prediction_labels:
                self.dirfordb = dir_name + f"/{label}_{newuuid}.jpeg"

    async def capture_image(self, event, label, number):
        try:
            dir_name = (
                label
                if event == "capture"
                else f"C:/Users/SRIJAN/Dropbox/PC/Desktop/{label}"
            )
            (
                os.mkdir(dir_name)
                if not (os.path.isdir(dir_name))
                else print("Directory already exists")
            )

            if event == "capture":
                await self.click_pic(dir_name, label)
                response = "Clicked Single pic"
            else:
                captured = 0
                while captured < int(number):
                    await asyncio.sleep(0.1)
                    await self.click_pic(dir_name, label)
                    captured = captured + 1
                response = f"Clicked  {number}  pics for {label}"
            return response

        except Exception as e:
            return f"error occured:{e}"

    async def start_video(self, event):

        await self.initcamera()
        print("Starting video stream")
        self.is_streaming = True

        async def stream_video():
            previous_time = time.time()
            while self.is_streaming:
                # await asyncio.sleep(0.03)

                success, frame = self.video_capture.read()
                if not success:
                    print("Failed to read frame from camera")
                    break

                fframe = cv2.flip(frame, 1)
                _, jpeg = cv2.imencode(".jpg", fframe)
                frame_data = base64.b64encode(jpeg.tobytes()).decode("utf-8")

                try:
                    await self.send(text_data=frame_data)
                    esp32_frame = cv2.resize(frame, (96, 96))
                    gray_frame = cv2.cvtColor(esp32_frame, cv2.COLOR_BGR2GRAY)
                    data = gray_frame.flatten().tobytes()
                    current_time = time.time()
                    if current_time - previous_time >= 15:
                        await self.channel_layer.group_send(  # type: ignore
                            "esp32_group2",
                            {
                                "type": "send_frame",
                                "frame_data": data,  # Send the frame as binary data
                            },
                        )
                        previous_time = current_time
                    await asyncio.sleep(0.03)
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break

                await asyncio.sleep(0.03)

        asyncio.create_task(stream_video())

    async def pred_res(self, event):
        # print(event)
        preddata = event["data"]
        try:
            if preddata is not None:
                pred = self.prediction_labels[int(preddata)]
                await self.perform_action(pred)  # type: ignore
        except Exception as e:
            print(f"Error occured while performing label action {e}")

    async def stop_video(self, event):
        print("Stopping video stream")
        self.is_streaming = False
        self.video_capture.release()
        # return render(request, 'oldhelperfrontend/lobby2.html')

    async def disconnect(self, close_code):
        print("Disconnecting VideoConsumer")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)  # type: ignore
        self.video_capture.release()

    async def perform_action(self, preddata):
        try:
            lat, long = await self.get_lat_and_long()  # type: ignore
            # print(lat)
            location_url = f"https://maps.google.com/?q={lat},{long}"
            # print(location_url)
            body = (
                "Hey I am fine now!"
                if preddata == "fine"
                else (
                    (
                        f"hey i need you to {preddata}"
                        if preddata == "call"
                        else (
                            f"hey my things are {preddata}"
                            if preddata == "stolen"
                            else f"hey i am in {preddata}"
                        )
                    )
                    + f"\r\nlocation: {location_url}"
                )
            )
            (
                None
                if preddata == "fine"
                else await self.click_pic(
                    "C:/Users/SRIJAN/Dropbox/PC/Documents/Programing/Projects/iotfullstack/iotfullstack/media/perpetrators",
                    preddata,
                )
            )

            # print(self.dirfordb)
            # print(type(self.user))

            user = await self.get_user_by_id(self.user_id)
            try:
                await self.save_action_to_db(
                    user, preddata, lat, long, location_url, self.dirfordb
                )
            except Exception as e:
                print(f"Some error occured while saving to db {e}")

            os.remove(self.dirfordb) if os.path.exists(self.dirfordb) else print("The file doesnt exist!")  # type: ignore
            # print(user)
            emergency_contacts = await self.get_all_em_foruser(user)
            # print(emergency_contacts)
            await self.send_message(body, emergency_contacts)

            # await self.delete_all()
            try:
                data = await self.send_latest_action()
                await self.send(json.dumps(data))
            except Exception as e:
                print(f"Some error occured while fetching latest data {e}")

        except Exception as e:
            print(f"Some error occured {e}")

    async def get_lat_and_long(self):
        g = geocoder.ip("")  # Uses IP address to get location
        # print(g)
        latitude = g.latlng[0]
        longitude = g.latlng[1]

        return latitude, longitude

    @database_sync_to_async
    def save_action_to_db(
        self, user, preddata, lat, long, location_url, captured_image_path
    ):
        # print(File(captured_image))
        filename = (
            os.path.basename(captured_image_path)
            if captured_image_path is not None
            else None
        )
        # print(captured_image_path,)
        try:
            if captured_image_path is not None:
                with open(captured_image_path, "rb") as img_file:
                    django_file = File(img_file, name=filename)

                    # print(captured_image_path,type(django_file))
                    saveaction = SaveAction.objects.create(
                        created_by=user,
                        action=preddata,
                        lat=lat,
                        long=long,
                        location=location_url,
                        captured_image=django_file,
                    )
                    saveaction.save()
            else:
                saveaction = SaveAction.objects.create(
                    created_by=user,
                    action=preddata,
                    lat=lat,
                    long=long,
                    captured_image=None,
                    location=location_url,
                )
                saveaction.save()
        except Exception as e:
            print(f"this error occured: {e}")

    @database_sync_to_async
    def delete_all(self):
        # return
        return SaveAction.objects.all().delete()

    @database_sync_to_async
    def send_message(self, body, contacts):

        for con in contacts:
            message = self.client.messages.create(
                from_="whatsapp:+14155238886",
                body=body,
                to=f"whatsapp:+91{con}",
            )

        # print(message.sid)

    @database_sync_to_async
    def send_latest_action(self):
        latest_data = SaveAction.objects.latest("created_at")
        # print(latest_data.location)
        image = None
        if latest_data.captured_image:
            image = latest_data.captured_image.url

        data = {
            "action": "DB_Latest",
            "user": (self.scope["user"].username),
            "label": latest_data.action,
            "lat": latest_data.lat if latest_data.lat is not None else None,
            "long": latest_data.long if latest_data.long is not None else None,
            "captured_image": image,
            "location": latest_data.location,
            "created_at": str(latest_data.created_at.strftime("%d-%m-%Y %H:%M:%S")),
        }
        return data

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            user = User.objects.get(id=user_id)

            return user
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_all_em_foruser(self, user):
        em = []
        emer_contacts = EmergencyContact.objects.filter(user=user)
        for emer in emer_contacts:
            em.append(str(emer.phone_no))
        return em
