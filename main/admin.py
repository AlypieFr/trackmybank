# TrackMyBank, a simple bank management tool
# 
# Copyright (C) 2018 Floreal Cabanettes <comm@flo-art.fr>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3.0

from django.contrib import admin

from main.models import TransactionGroup, Transaction, Category, Month, RecurringCharges, UserRole, Group, UserGroup

# Register your models here.

admin.site.register(TransactionGroup)
admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(Month)
admin.site.register(RecurringCharges)
admin.site.register(UserRole)
admin.site.register(Group)
admin.site.register(UserGroup)

admin.site.site_header = "Track My Bank!"
admin.site.site_title = "Track My Bank!"
