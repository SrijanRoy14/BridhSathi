from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class EmergencyContact(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="CurrentUser")
    name=models.CharField(max_length=50,blank=False,null=False)
    phone_no=models.CharField(max_length=15,blank=False,null=False)

    def __str__(self):
        return self.name
    
class SaveAction(models.Model):
    created_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name="ActionofUser",null=True)
    action=models.CharField(max_length=50,blank=False,null=False)
    lat=models.FloatField(blank=True,null=True)
    long=models.FloatField(blank=True,null=True)
    captured_image=models.ImageField(blank=True,null=True,upload_to='perpetrators/')
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'SaveAction'

class IncomingMessages(models.Model):
    sender=models.CharField(max_length=15)
    content=models.TextField()
    received_at=models.DateTimeField(auto_now_add=True)
    