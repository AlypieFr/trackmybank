from django.db import models
from django.utils.translation import ugettext as _


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
    month = models.CharField(max_length=20, verbose_name=_("month"))
    year = models.IntegerField(verbose_name=_("year"))

    def __str__(self):
        return " ".join((self.month, str(self.year)))

    class Meta:
        verbose_name = _("Month")
        verbose_name_plural = _("Months")


class Transaction(models.Model):
    date_t = models.DateField(verbose_name=_("transaction date"))
    date_bank = models.DateField(verbose_name=_("bank added date"), blank=True, null=True)
    subject = models.CharField(max_length=255, verbose_name=_("subject"))
    amount = models.FloatField(verbose_name=_("amount"))
    category = models.ForeignKey(Category, verbose_name=_("category"))
    month = models.ForeignKey(Month, verbose_name=_("month"))

    def __str__(self):
        return " ".join((self.month.month + "_" + str(self.month.year), "-", self.subject, ":",  str(self.date_t)))

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")