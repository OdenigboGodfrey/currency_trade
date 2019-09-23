from django.urls import path, include
from . import views


app_name = "CTAdmin"

urlpatterns = [
    path('', views.index, name='index'),
    path('registeradmin/', views.RegisterAdmin, name='RegisterAdmin'),
    path('login/', views.Login, name='Login'),
    path('logout/', views.Logout, name='Logout'),
    path('assign/<int:TaskId>', views.AssignTask, name='Assign'),
    path('changelevel/', views.ChangeLevel, name='ChangeLevel'),
    path('kyctasks/', views.KYCTasks, name='KYCTasks'),
    path('trans-tasks/', views.TransactionTasks, name='TransactionTasks'),
    path('mytasks/', views.MyTasks, name='MyTasks'),
    path('completed/', views.Completed, name='Completed'),
    path('transaction/<int:AdId>', views.Transaction, name='Transaction'),
    path('approve/<int:AdId>', views.Approve, name='Approve'),
    path('CTfee/', views.CTFee, name='CTFee'),
    path('paid/<int:AdId>', views.Paid, name='Paid'),
    path('close/<int:AdId>', views.Close, name='Close'),
    path('deactivate/', views.Deactivate, name='Deactivate'),
    path('eaglewatch/', views.EagleWatch, name='EagleWatch'),
    path('unpaidreferrers/', views.UPReferrers, name='UpReferrers'),
    path('assignmenttype/', views.AssignmentType, name='AssignmentType'),
]