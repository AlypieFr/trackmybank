from django.contrib import admin

from main.models import TransactionGroup, Transaction, Category, Month, RecurringCharges

# Register your models here.

admin.site.register(TransactionGroup)
admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(Month)
admin.site.register(RecurringCharges)
