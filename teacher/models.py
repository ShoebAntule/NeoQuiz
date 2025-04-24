from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from student.models import Student

class Teacher(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/Teacher/', default='teacher/default.png')
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    status= models.BooleanField(default=False)
    subject = models.CharField(
        max_length=100,
        default='General',
        help_text="Main subject taught by this teacher"
    )
    joined_date = models.DateField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    blocked_students = models.ManyToManyField(
        Student,
        related_name='blocked_by_teachers',
        blank=True,
        help_text="Students blocked by this teacher"
    )
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name
