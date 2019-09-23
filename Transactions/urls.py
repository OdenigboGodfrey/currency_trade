from django.urls import path, include
from . import views

app_name = "Transactions"

urlpatterns = [
    path('', views.index, name='index'),
    path('place/', views.Place, name='Place'),
    path('mytrades/', views.MyTrades, name='MyTrades'),
    path('trades/', views.Trades, name='Trades'),
    path('buy/<int:AdId>', views.BuyAd, name='BuyAd'),
    path('negotiations/<int:AdId>', views.Negotiations, name='Negotiations'),
    path('nlog/<int:AdId>', views.NLog, name='NLog'),
    path('ongoing/', views.OnGoing, name='OnGoing'),
    path('paid/<int:AdId>', views.Paid, name='Paid'),
    path('completed/', views.Completed, name='Completed'),
    path('placereview/<int:AdId>', views.PlaceReview, name='PlaceReview'),
    path('rejected/', views.Rejected, name='Rejected'),
    path('close/<int:AdId>', views.Close, name='Close'),
    path('btransactions', views.BTransactions, name='BulkTransactions'),

    path('', include('Authentication.urls')),
    path('', include('CTAdmin.urls')),
]