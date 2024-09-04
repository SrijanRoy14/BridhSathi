import json
from channels.generic.websocket import WebsocketConsumer,AsyncWebsocketConsumer
import cv2
import base64
import asyncio
from asgiref.sync import async_to_sync
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

load_dotenv()

class feedfront(WebsocketConsumer):
    def connect(self):
        self.accept()
        

        self.send(text_data="hello esp32! we are connected "
                   
         )
        self.room_group_name='esp32_group2'
       
        self.channel_name = self.channel_name  
        async_to_sync(self.channel_layer.group_add)( # type: ignore
            self.room_group_name,
            self.channel_name
        )
    
    def send_frame(self, event):
        
        frame_data = event['frame_data']
        if frame_data is not None:
            #print("receiving frame buffer")
            self.send(bytes_data=frame_data)  
        

    def receive(self, text_data=None, bytes_data=None):
        #print(text_data)
        if text_data is not None:
            async_to_sync(self.channel_layer.group_send)( # type: ignore
                        'esp32_group3', 
                        {
                            'type': 'pred_res',
                            'data': text_data  # Send predicted class
                        }
                        )
        #asyncio.sleep(0.03)
        return super().receive(text_data, bytes_data)
    
    
    

class VideoConsumer(AsyncWebsocketConsumer):
    API_KEY = os.getenv("account_sid")
    API_SECRET = os.getenv("auth_token")

    prediction_labels="fine danger stolen call".split(' ')
    user=None
    async def connect(self):
        await self.accept()

        self.account_sid = self.API_KEY
        self.auth_token = self.API_SECRET
        self.client = Client(self.account_sid, self.auth_token)


        self.room_group_name = 'esp32_group3'
        self.channel_name = self.channel_name

        self.user=self.scope['user']
        print(await self.perform_action("fine"))
        await self.channel_layer.group_add(self.room_group_name, self.channel_name) # type: ignore
        print(f"VideoConsumer connected and joined group: {self.room_group_name}")

        
        self.video_capture = cv2.VideoCapture(0)
        self.is_streaming = False  

    async def receive(self, text_data, bytes_data=None):
        
        try:
            data = json.loads(text_data)
              
            action = data.get('action')
            
            if action == 'start':
                await self.start_video('start')
            elif action=='capture':
                await self.capture_image(action,"Saved_Image",None)
            elif action=='capturemulti':
                label=data.get('label')
                number=data.get('number')
                #print(label,number)
                

                response=await self.capture_image(action,label,number)
                async def sendresponse():
                    print(response)
                    await self.send(text_data="Done") 
                await asyncio.create_task(sendresponse())
                
            elif action == 'stop':
                await self.stop_video(None)  
        except json.JSONDecodeError:
            print("Received non-JSON message")

    async def click_pic(self,dir_name,label):
        success, frame = self.video_capture.read()
        if success:
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            newuuid=uuid.uuid4()
            print(f"saved image for {label}")
            #frame=cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(dir_name+f"/{label}_{newuuid}.jpeg",frame)

    async def capture_image(self,event,label,number):
        try:
           
            dir_name=label if event=='capture' else f"C:/Users/SRIJAN/Dropbox/PC/Desktop/{label}"
            
            os.mkdir(dir_name) if not (os.path.isdir(dir_name)) else print("Directory already exists")
                
                
            if event=='capture':
                
                await self.click_pic(dir_name,label)
                response="Clicked Single pic"
            else:
                i=0
                while i<int(number):
                    await asyncio.sleep(0.1)
                    await self.click_pic(dir_name,label)
                    i=i+1
                response=f"Clicked  {number}  pics for {label}"
            return response

        except Exception as e:
            return f"error occured:{e}"
             
    

    async def start_video(self, event):
        self.video_capture = cv2.VideoCapture(0)
        self.is_streaming = False  
        print("Starting video stream")
        self.is_streaming = True  
        async def stream_video():
            while self.is_streaming:
                #await asyncio.sleep(0.03)
                success, frame = self.video_capture.read()
                if not success:
                    
                    print("Failed to read frame from camera")
                    break

                fframe = cv2.flip(frame, 1)
                _, jpeg = cv2.imencode('.jpg', fframe)
                frame_data = base64.b64encode(jpeg.tobytes()).decode('utf-8')

                try:
                    await self.send(text_data=frame_data)
                    
                    esp32_frame = cv2.resize(frame, (96, 96))
                    gray_frame = cv2.cvtColor(esp32_frame, cv2.COLOR_BGR2GRAY)
                    data = gray_frame.flatten().tobytes()

                    

                    await self.channel_layer.group_send( # type: ignore
                    'esp32_group2', 
                    {
                        'type': 'send_frame',
                        'frame_data': data  # Send the frame as binary data
                    }
                    )
                    await asyncio.sleep(0.03)
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break

                await asyncio.sleep(0.03)  

        asyncio.create_task(stream_video())

    async def pred_res(self,event):
        #print(event)
        preddata=event['data']
        
        if preddata is not None:
            preddata=self.prediction_labels[int(preddata)]
            await self.perform_action(preddata)

    
    async def stop_video(self, event):
        print("Stopping video stream")
        self.is_streaming = False  
        self.video_capture.release()  
        #return render(request, 'oldhelperfrontend/lobby2.html')

    async def disconnect(self, close_code):
        print("Disconnecting VideoConsumer")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name) # type: ignore
        self.video_capture.release()
     
    async def perform_action(self,preddata):
        

        if preddata =="fine":
            #await self.save_action_to_db(self,preddata,None,None,None)
            body="hey i am in danger!"
            await self.send_message(body)

    @database_sync_to_async
    def save_action_to_db(self,preddata,lat,long,captured_image):
       saveaction=SaveAction.objects.create(
           created_by=None,
           action=preddata,
           lat=lat,
           long=long,
           captured_image=captured_image
       )
       saveaction.save()
       return saveaction
    
    @database_sync_to_async  
    def send_message(self,body):
        message = self.client.messages.create(
        from_='whatsapp:+14155238886',
        body=body,
            to='whatsapp:+919163437332'
            )

        print(message.sid)
        