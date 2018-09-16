from django.contrib import admin

from main.models import TransactionGroup, Transaction, Category, Month

# Register your models here.

admin.site.register(TransactionGroup)
admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(Month)
