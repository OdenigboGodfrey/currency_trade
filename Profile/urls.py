from django.urls import path, include
from . import views
from django.shortcuts import redirect


app_name = "Profile"

urlpatterns = [
    path('', views.index, name='index-2'),
    path('home', views.index, name='index'),
    path('edit/', views.Edit, name='Edit-Profile'),
    path('bank/', views.Bank, name='Bank-Accounts'),
    path('bank/add/', views.BankAdd, name='Bank-Accounts-Add'),
    path('bank/remove/', views.RemoveBank, name='Bank-Accounts-Remove'),
    path('display/', views.DisplayUpload, name='DisplayPicture'),
    path('', include('Authentication.urls')),
]