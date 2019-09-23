from django.db import models

# Create your models here.


class User(models.Model):
    FullName = models.CharField(max_length=250)
    Sex = models.CharField(max_length=8)
    State = models.CharField(max_length=500)
    Country = models.CharField(max_length=500)
    DOB = models.DateTimeField()
    AccountNumber = models.CharField(max_length=11, blank=True, null=True)
    Email = models.EmailField(unique=True)
    PhoneNumber = models.CharField(max_length=16)
    Password = models.CharField(max_length=50)
    TwoFactor = models.CharField(max_length=6, null=True, blank=True)
    OnlineOffline = models.BooleanField()
    IsVerified = models.BooleanField(default=False)
    TwoFactorTime = models.DateTimeField(null=True, blank=True)
    Referrer = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='MyReferrer')
    AccountType = models.IntegerField(default=1, blank=True, null=True)

    def __str__(self):
        return self.FullName + "(" + self.Email + " #" + str(self.pk) + ")"


class Review(models.Model):
    ReviewContent = models.CharField(max_length=100)
    ReviewStars = models.IntegerField()
    ReviewDate = models.DateTimeField()
    FromUser = models.IntegerField()
    ToUser = models.IntegerField()

    def __str__(self):
        return "Review Id " + str(self.ReviewDate)


class Banks(models.Model):
    BankName = models.CharField(max_length=250)
    AccountName = models.CharField(max_length=250)
    AccountNumber = models.CharField(max_length=500)
    UserId = models.IntegerField()
    IsActive = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return str(self.BankName) + "(" + str(self.AccountNumber) + ")"

