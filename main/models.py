# TrackMyBank, a simple bank management tool
# 
# Copyright (C) 2018 Floreal Cabanettes <comm@flo-art.fr>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3.0

import calendar

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User


class Role(models.Model):
    id = models.IntegerField(verbose_name=_("Id"), primary_key=True)
    name = models.CharField(max_length=20, verbose_name=_("Role"))

    def __str__(self):
        return _(self.name)


class UserRole(models.Model):
    class Meta:
        unique_together = (("user", "role"),)
        verbose_name = _("User role")

    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    role = models.ForeignKey(Role, verbose_name=_("Role"), on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username + " - " + _(self.role.name)


class Group(models.Model):
    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

    id = models.IntegerField(verbose_name=_("Id"), primary_key=True)
    name = models.CharField(max_length=20, verbose_name=_("Group"))

    def __str__(self):
        return _(self.name)


class UserGroup(models.Model):
    class Meta:
        verbose_name = _("User group")
        verbose_name_plural = _("User groups")

    user = models.OneToOneField(User, primary_key=True, verbose_name=_("User"), on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_("Group"), on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username + " - " + _(self.group.name)


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("name"))
    color = models.CharField(max_length=50, verbose_name=_("color"))
    is_goodies = models.BooleanField(verbose_name=_("Is goodies?"))
    is_saving = models.BooleanField(verbose_name=_("Is saving?"), default=False)
    ignore_week_filters = models.BooleanField(default=False, verbose_name=_("ignore weekly spending filters"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Month(models.Model):
    month = models.IntegerField(verbose_name=_("month"))
    year = models.IntegerField(verbose_name=_("year"))
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("salary"))
    ugroup = models.ForeignKey(Group, verbose_name=_("user group"), on_delete=models.CASCADE)

    def __str__(self):
        with calendar.different_locale(settings.LOCALE):
            return " ".join((calendar.month_name[self.month].capitalize(), str(self.year)))

    class Meta:
        verbose_name = _("Month")
        verbose_name_plural = _("Months")
        unique_together = ("month", "year")


class CurrentMonth(models.Model):
    group = models.OneToOneField(Group, primary_key=True, on_delete=models.CASCADE)
    month = models.ForeignKey(Month, verbose_name=_("month"), on_delete=models.CASCADE)


class TransactionGroup(models.Model):
    date_t = models.DateField(verbose_name=_("transaction date"))
    date_bank = models.DateField(verbose_name=_("bank added date"), blank=True, null=True)
    month = models.ForeignKey(Month, verbose_name=_("month"), on_delete=models.CASCADE)
    ignore_week_filters = models.BooleanField(default=False, verbose_name=_("ignore weekly spending filters"))

    def __str__(self):
        return str(self.id) + "-" + calendar.month_name[self.month.month] + "_" + str(self.month.year) + \
               " (" + str(self.date_t) + ")"

    class Meta:
        verbose_name = _("Transaction group")
        verbose_name_plural = _("Transaction groups")


class Transaction(models.Model):
    subject = models.CharField(max_length=255, verbose_name=_("subject"))
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_("amount"))
    category = models.ForeignKey(Category, verbose_name=_("category"), on_delete=models.CASCADE)
    group = models.ForeignKey(TransactionGroup, verbose_name=_("group"), on_delete=models.CASCADE)

    def __str__(self):
        return " ".join((calendar.month_name[self.group.month.month] + "_" + str(self.group.month.year), "-",
                         self.subject, ":",  str(self.group.date_t)))

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class RecurringCharges(models.Model):
    group = models.OneToOneField(Group, primary_key=True, on_delete=models.CASCADE)
    file = models.CharField(max_length=1000, verbose_name=_("File path"))

    def __str__(self):
        return self.group.name + " - " + self.file

    class Meta:
        verbose_name = _("Recurring charges")
        verbose_name_plural = _("Recurring charges")
