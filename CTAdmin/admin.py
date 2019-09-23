from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Admins)
admin.site.register(ReviewedTransactions)
admin.site.register(ReviewedTransactionLog)
admin.site.register(KYC)
admin.site.register(KYCLogs)
admin.site.register(AdminTask)
admin.site.register(TransactionFile)
admin.site.register(CTFee)
admin.site.register(Affiliate)
admin.site.register(TaskAssignmentType)
admin.site.register(TaskAssignmentTypeLog)

