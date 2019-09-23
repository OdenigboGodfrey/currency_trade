from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ExchangeRate)
admin.site.register(Currencies)
admin.site.register(Transactions)
admin.site.register(Negotiations)
admin.site.register(TransactionFile)
admin.site.register(Review)
admin.site.register(BulkTransaction)
admin.site.register(AffiliatePayment)