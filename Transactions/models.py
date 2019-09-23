from _ast import mod

from django.db import models
from Authentication.models import User
from CTAdmin.models import Admins
from datetime import datetime

# Create your models here.


class Transactions(models.Model):
    FromCurrency = models.CharField(null=True, blank=True, max_length=10)
    ToCurrency = models.CharField(null=True, blank=True, max_length=10)
    Amount = models.FloatField(null=True, blank=True)
    Negotiable = models.BooleanField(null=True, blank=True)
    ExchangeRate = models.FloatField(null=True, blank=True)
    Seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Seller', blank=True, null=True)
    Buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Buyer', null=True, blank=True)
    HandledBy = models.ForeignKey('CTAdmin.Admins', on_delete=models.CASCADE, null=True, blank=True)
    TransactionDate = models.DateTimeField(default=datetime.now, null=True, blank=True)
    Paid = models.BooleanField(default=False, null=True, blank=True)
    Completed = models.BooleanField(default=False, null=True, blank=True)
    BTID = models.ForeignKey('Transactions.BulkTransaction', on_delete=models.CASCADE, null=True, blank=True)
    CTFee = models.FloatField(default=2.2, null=True, blank=True)
    Bank = models.ForeignKey('Authentication.Banks', on_delete=models.CASCADE, null=True, blank=True)
    Approved = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return "[Ad #" + str(self.pk) + "] User #" + str(self.Seller.pk) + "('" + str(self.Amount) + "', '" + self.FromCurrency + "-" + self.ToCurrency + "' on " + str(self.TransactionDate) + ")"


class BulkTransaction(models.Model):
    """ bulk transaction is used for trades which would be sold in bits"""
    FromCurrency = models.CharField(null=True, blank=True, max_length=10)
    ToCurrency = models.CharField(null=True, blank=True, max_length=10)
    Amount = models.FloatField(null=True, blank=True)
    ExchangeRate = models.FloatField(null=True, blank=True)
    Seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='BulkSeller', blank=True, null=True)
    BitsPercentage = models.FloatField(null=True, blank=True)
    Completed = models.BooleanField(default=False, null=True, blank=True)
    Automate = models.BooleanField(default=False, null=True, blank=True)
    Negotiable = models.BooleanField(null=True, blank=True)
    Flag = models.BooleanField(null=False, blank=True, default=False)
    CTFee = models.FloatField(default=2.2, null=True, blank=True)
    TransactionDate = models.DateTimeField(default=datetime.now, null=True, blank=True)
    AmountLeft = models.FloatField(default=0, blank=True, null=True)
    Bank = models.ForeignKey('Authentication.Banks', on_delete=models.CASCADE, null=True, blank=True)
    Approved = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return "BT " + str(self.pk) + "{" + self.FromCurrency + "-" + self.ToCurrency + ", Amount " + str(self.Amount) \
               + " #" + str(self.Seller.pk)


class Negotiations(models.Model):
    ProposedRate = models.FloatField(null=True, blank=True)
    UserId = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, blank=True, null=True)
    Accepted = models.BooleanField(null=True, blank=True)
    TransactionsId = models.ForeignKey(Transactions, on_delete=models.CASCADE, null=True, blank=True)
    NegotiationDate = models.DateTimeField(default=datetime.now, null=True, blank=True)
    Message = models.CharField(max_length=100, null=True, blank=True)
    Paid = models.BooleanField(default=False, null=True, blank=True)
    Approved = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return "Transaction #" + str(self.TransactionsId.pk) + " " + str(self.UserId) + "(" + str(self.Accepted) + ")"


class ExchangeRate(models.Model):
    ShortForm = models.CharField(max_length=10, null=True, blank=True)
    ExchangeRate = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.ShortForm + "-" + str(self.ExchangeRate)


class Currencies(models.Model):
    CountryCurrencyShort = models.CharField(max_length=10, null=True, blank=True)
    CurrencyName = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.CurrencyName + "-" + self.CountryCurrencyShort


class TransactionFile(models.Model):
    FileName = models.CharField(max_length=100)
    UploadDate = models.DateTimeField(default=datetime.now, blank=True)
    TransactionId = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True)
    UploadedBy = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, related_name='TFUser', blank=True, null=True)
    Approved = models.IntegerField(default=0, blank=True, null=True)
    Message = models.CharField(max_length=100, default='n/a', blank=True, null=True)

    def __str__(self):
        return self.FileName + " " + str(self.Approved) + " Transaction #" + str(self.TransactionId.pk)


class Review(models.Model):
    TransactionId = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True)
    ReviewBy = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, blank=True, null=True)
    ReviewDate = models.DateTimeField(default=datetime.now, blank=True, null=True)
    ReviewContent = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.ReviewBy.Email) + " posted a review on " + str(self.ReviewDate) + " on Trade Ad #" + str(self.TransactionId.pk)


class AffiliatePayment(models.Model):
    Transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True)
    Amount = models.FloatField(blank=True, null=True)
    Referrer = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, blank=True, null=True, related_name='APReferrer')
    User = models.ForeignKey('Authentication.User', on_delete=models.CASCADE, blank=True, null=True, related_name='APUser')
    Paid = models.BooleanField(blank=True, null=True, default=False)
    PayDate = models.DateTimeField(blank=True, null=True)
    Flag = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return str(self.Referrer) + " " + str(self.Paid)




