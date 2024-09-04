import cv2
import threading
import time
class videocamera(object):
    
    def  __init__(self):

        self.video=cv2.VideoCapture(0)
        #(self.grabbed,self.frame)=self.video.read()
        #threading.Thread(target=self.update,args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success,image=self.video.read()
        if not success:
            print("Frame not grabbed")
            return None
        frame_flip=cv2.flip(image,1)
        ret,jpeg=cv2.imencode('.jpg',frame_flip)
        return jpeg.tobytes()
        """if self.grabbed:
            image=self.frame
            _,jpeg=cv2.imencode('.jpg',image)
            return jpeg.tobytes()
        print("frame not grabbed in get_frame")
        return None"""
    
    def update(self):
        while True:
            (self.grabbed,self.frame)=self.video.read()
            if not self.grabbed:
                print("frame not grabbed")


def gen(camera):
    while True:
        frame=camera.get_frame()
        if frame is None:
            print("Frame is None")
            continue
        print("Yielding frame")  # Debugging line
        yield(b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'+ frame + b'\r\n\r\n')
        time.sleep(0.5)
