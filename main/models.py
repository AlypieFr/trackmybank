import calendar

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("name"))
    color = models.CharField(max_length=50, verbose_name=_("color"))
    is_goodies = models.BooleanField(verbose_name=_("Is goodies?"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Month(models.Model):
    month = models.IntegerField(verbose_name=_("month"))
    year = models.IntegerField(verbose_name=_("year"))
    salary = models.FloatField(verbose_name=_("salary"))

    def __str__(self):
        with calendar.different_locale(settings.LOCALE) as encoding:
            return " ".join((calendar.month_name[self.month].capitalize(), str(self.year)))

    class Meta:
        verbose_name = _("Month")
        verbose_name_plural = _("Months")


class CurrentMonth(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    month = models.ForeignKey(Month, verbose_name=_("month"))


class TransactionGroup(models.Model):
    date_t = models.DateField(verbose_name=_("transaction date"))
    date_bank = models.DateField(verbose_name=_("bank added date"), blank=True, null=True)
    month = models.ForeignKey(Month, verbose_name=_("month"))

    def __str__(self):
        return str(self.id) + "-" + calendar.month_name[self.month.month] + "_" + str(self.month.year)

    class Meta:
        verbose_name = _("Transaction group")
        verbose_name_plural = _("Transaction groups")


class Transaction(models.Model):
    subject = models.CharField(max_length=255, verbose_name=_("subject"))
    amount = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_("amount"))
    category = models.ForeignKey(Category, verbose_name=_("category"))
    group = models.ForeignKey(TransactionGroup, verbose_name=_("group"))

    def __str__(self):
        return " ".join((calendar.month_name[self.group.month.month] + "_" + str(self.group.month.year), "-",
                         self.subject, ":",  str(self.group.date_t)))

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
