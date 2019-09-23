from django.db import models
from datetime import datetime


# Create your models here.


class contact(models.Model):
    FirstName = models.CharField(max_length=100, blank=True, null=True)
    LastName = models.CharField(max_length=100, blank=True, null=True)
    Email = models.EmailField(blank=True, null=True)
    Phone = models.CharField(max_length=20, blank=True, null=True)
    Message = models.TextField(blank=True, null=True)
    Date = models.DateTimeField(default=datetime.now, blank=True, null=True)
    HandledBy = models.ForeignKey('CTAdmin.Admins', on_delete=models.CASCADE,
                                  blank=True, null=True)


class newsletter(models.Model):
    Email = models.EmailField(blank=True, null=True)

