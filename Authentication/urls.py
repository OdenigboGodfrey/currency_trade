from django.urls import path, include
from . import views, base
from django.conf import settings
from django.conf.urls.static import static

app_name = "Authentication"

urlpatterns = [
    path('login/', views.Login, name='Login'),
    path('signup/', views.Signup, name='Signup'),
    path('', views.Homepage, name='Index'),
    path('tfa/<int:Id>/', views.TwoFactor, name='TwoFactor'),
    path('resetpassword/', views.ResetPassword, name='Reset'),
    path('newpassword/<int:Id>', views.NewPassword, name='NewPassword'),
    path('kyc/', views.KYCUpload, name='KYC'),
    path('R/<str:Code>', views.Referred, name='Referred'),
    path('logout/', views.Logout, name='Logout'),
    path('more/', views.More, name='More'),

]