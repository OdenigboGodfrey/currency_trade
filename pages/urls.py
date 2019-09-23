from django.urls import path, include
from . import views
from django.shortcuts import redirect


app_name = "pages"

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.About, name='About'),
    path('contact/', views.Contact, name='Contact'),
    path('faq/', views.FAQ, name='faq'),
    path('services/', views.Services, name='Services'),
    path('newsletter/', views.NewsLetter, name='newsletter'),
]