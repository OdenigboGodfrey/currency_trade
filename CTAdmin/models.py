from django.db import models
from datetime import datetime

# Create your models here.


class Admins(models.Model):
    FullName = models.CharField(max_length=250)
    Email = models.EmailField()
    Password = models.CharField(max_length=250)
    PhoneNumber = models.CharField(max_length=250)  #models.CharField(max_length=250)
    Star = models.CharField(max_length=1, null=True, blank=True)
    Tasks = models.IntegerField(null=True, blank=True, default=0)
    CompletedTasks = models.IntegerField(null=True, blank=True, default=0)
    IsActive = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return self.FullName + " (" + self.Email + ")"


class ReviewedTransactions(models.Model):
    TransactionID = models.ForeignKey('Transactions.Transactions', on_delete=models.CASCADE, blank=True, null=True)
    StartDate = models.DateTimeField()
    EndDate = models.DateTimeField(default=datetime.now)
    Status = models.IntegerField()
    HandledBy = models.ForeignKey(Admins, on_delete=models.CASCADE, blank=True, null=True)


class ReviewedTransactionLog(models.Model):
    TransactionID = models.ForeignKey('Transactions.Transactions', on_delete=models.CASCADE, blank=True, null=True)
    Log = models.TextField()
    LogDate = models.DateTimeField(default=datetime.now, blank=True)
    IsAdminAction = models.BooleanField(default=False, blank=True, null=True)
    UserNotified = models.BooleanField(default=False, blank=True, null=True)
    AdminNotified = models.BooleanField(default=False, blank=True, null=True)
    LogActionBy = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return "Transaction Id #[" + str(self.TransactionID.pk) + "] Date (" + str(self.LogDate) + ")"


class KYC(models.Model):
    IsApproved = models.BooleanField(default=False, blank=True, null=True)
    UserId = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, blank=True, null=True)
    HandledBy = models.ForeignKey(Admins, on_delete=models.CASCADE, null=True, blank=True)
    IsKYCDone = models.BooleanField(default=False, null=True, blank=True)
    Status = models.IntegerField(default=0, null=True, blank=True)
    RejectionMessage = models.TextField(null=True, blank=True)
    StartDate = models.DateTimeField(default=datetime.now, blank=True, null=True)

    def __str__(self):
        return str(self.UserId) + "(" + str(self.pk) + ")"


class KYCLogs(models.Model):
    KYCId = models.ForeignKey(KYC, on_delete=models.CASCADE, blank=True, null=True)
    Log = models.TextField()
    LogDate = models.DateTimeField(default=datetime.now, blank=True)
    IsAdminAction = models.BooleanField(default=False, blank=True, null=True)
    UserNotified = models.BooleanField(default=False, blank=True, null=True)
    AdminNotified = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return "KYC #" + str(self.pk) + " User (" + str(self.KYCId) + ") on (" + self.LogDate.strftime("%Y-%m-%d %H:%M:%S") + ")"


class AdminTask(models.Model):
    AdminId = models.ForeignKey(Admins, on_delete=models.CASCADE, blank=True, null=True)
    TaskId = models.IntegerField(blank=True, null=True)
    TaskType = models.CharField(max_length=50, blank=True, null=True)
    TaskDate = models.DateTimeField(default=datetime.now, blank=True)
    Completed = models.BooleanField(default=False, blank=True, null=True)


class KunubaFee(models.Model):
    AdminId = models.ForeignKey(Admins,  on_delete=models.CASCADE, blank=True, null=True)
    Percentage = models.FloatField(null=True, blank=True, default=3)
    SetDate = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return str(self.Percentage)


class TransactionFile(models.Model):
    FileName = models.CharField(max_length=100)
    UploadDate = models.DateTimeField(default=datetime.now, blank=True)
    TransactionId = models.ForeignKey('Transactions.Transactions', on_delete=models.CASCADE, related_name='Transaction', blank=True, null=True)
    UploadedBy = models.ForeignKey(Admins, on_delete=models.CASCADE, related_name='Admin', blank=True, null=True)
    User = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, related_name='User', null=True, blank=True)

    def __str__(self):
        return str(self.FileName) + " " + str(self.TransactionId)


class AdminLog(models.Model):
    LogDate = models.DateTimeField(default=datetime.now, blank=True, null=True)
    LogContent = models.TextField()
    AdminId = models.ForeignKey(Admins, on_delete=models.CASCADE, blank=True, null=True)


class Affiliate(models.Model):
    Percentage = models.FloatField(blank=True, null=True)
    Admin = models.ForeignKey(Admins, on_delete=models.CASCADE, blank=True, null=True)
    SetDate = models.DateTimeField(default=datetime.now, blank=True, null=True)

    def __str__(self):
        return str(self.Percentage)


class TaskAssignmentType(models.Model):
    Type = models.CharField(blank=True, null=True, default="Polling", max_length=20)
    Admin = models.ForeignKey(Admins, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.Type


class TaskAssignmentTypeLog(models.Model):
    LogDate = models.DateTimeField(default=datetime.now, blank=True, null=True)
    LogContent = models.TextField()
    Admin = models.ForeignKey(Admins, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return "on " + str(self.LogDate) + " - " + self.LogContent
