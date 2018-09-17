import re
from datetime import datetime

from django.views.generic import TemplateView, View
from django.template.loader import render_to_string
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext as _
from django.middleware import csrf
from django.db import transaction as db_transaction

import main.functions as functions
import traceback
from main.models import Category, Month, TransactionGroup, Transaction


def context_data(user):
    current_month = functions.get_current_month(user)
    transactions = TransactionGroup.objects.filter(month=current_month).order_by("date_t")
    for group in transactions:
        total = 0
        for transaction in group.transaction_set.all():
            total += transaction.amount
        group.total = total
    return {
        "categories": Category.objects.all().order_by("name"),
        "transactions": transactions,
        "months": sorted(Month.objects.all(), key=lambda m: (-m.year, -m.month)),
        "current_month": current_month
    }


class IndexView(TemplateView):
    template_name = "index.html"

    user = None

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        c = super(TemplateView, self).get_context_data(**kwargs)
        self.user = self.request.user
        return c

    def data(self):
        current_month = functions.get_current_month(self.user)
        return context_data(self.user)


class LogoutView(View):

    def get(self, request):
        logout(request)
        csrf.rotate_token(request)
        return redirect("/")


class TransactionView(View):

    @staticmethod
    def format_date(date):
        return datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            date_t = request.POST["date_t"] if "date_t" in request.POST else None
            date_bank = request.POST["date_bank"] if "date_bank" in request.POST else None
            amount = float(request.POST["amount"].replace(",", "."))
            subject = request.POST["subject"]
            try:
                category = Category.objects.get(pk=request.POST["category"])
            except Category.DoesNotExist:
                return JsonResponse({"success": False, "message": "Category %s does not exists" % request.POST["category"]})
            try:
                month = Month.objects.get(pk=request.POST["month"]) if "month" in request.POST else None
            except Month.DoesNotExist:
                return JsonResponse({"success": False, "message": "Month %s does not exists" % request.POST["month"]})
            tr_id = request.POST["tr_id"] if "tr_id" in request.POST else None
        except (KeyError, ValueError):
            traceback.print_exc()
            return JsonResponse({"success": False, "message":
                                 "Bad query. Please contact the support to report the bug"})

        if "tr_id" is None and (date_t is None or month is None):
            return JsonResponse({"success": False,
                                 "message": "Bad request (2). please contact the support to report the bug"})

        try:
            date_regex = r"^\d\d/\d\d/\d\d\d\d$"
            if date_t is not None:
                if not re.match(date_regex, date_t):
                    raise ValueError("Invalid date: %s" % date_t)
                date_t = self.format_date(date_t)
            elif tr_id is None:
                raise ValueError("Date is required")
            if date_bank is not None:
                if not re.match(date_regex, date_bank):
                    raise ValueError("Invalid date: %s" % date_bank)
                date_bank = self.format_date(date_bank)
        except ValueError as e:
            return JsonResponse({"success": False, "message": str(e)})

        try:
            if tr_id is None:
                # Add a new transaction
                with db_transaction.atomic():
                    transaction_group = TransactionGroup(date_t=date_t, date_bank=date_bank, month=month)
                    transaction_group.save()
                    transaction = Transaction(amount=amount, subject=subject, category=category, group=transaction_group)
                    transaction.save()
        except:
            traceback.print_exc()
            return JsonResponse({"success": False,
                                 "message": "An unexpected error occurred. Please contact the support"})

        return JsonResponse({"success": True,
                             "html": render_to_string("main_content.html",
                                                      {"view": {"data": context_data(request.user)}})})


class ChangeMonthView(View):

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            c_month = Month.objects.filter(pk=request.POST["month"])
            if c_month is None:
                return JsonResponse(
                    {"success": False, "message": _("Selected month does not exists. Please contact the support.")})
            functions.set_current_month(month=c_month.first(), user=request.user)
        except:
            traceback.print_exc()
            return JsonResponse({"success": False, "message": _("Internal server error. An unexpected error occurred. "
                                                                "Unable to change month. Please contact the support.")})
        return JsonResponse({"success": True,
                             "html": render_to_string("main_content.html",
                                                      {"view": {"data": context_data(request.user)}})})
