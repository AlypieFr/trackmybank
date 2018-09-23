# TrackMyBank, a simple bank management tool
# 
# Copyright (C) 2018 Floreal Cabanettes <comm@flo-art.fr>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3.0

import calendar
import os
import re
from datetime import datetime

from django.views.generic import TemplateView, View
from django.template.loader import render_to_string
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext as _
from django.middleware import csrf
from django.db import transaction as db_transaction
from django.conf import settings

import main.functions as functions
import traceback
from main.models import Category, Month, TransactionGroup, Transaction, RecurringCharges


def content_data(user):
    current_month = functions.get_current_month(user)
    transactions = TransactionGroup.objects.filter(month=current_month).order_by("date_t", "date_bank",
                                                                                 "transaction__subject")
    total_depenses = 0
    goodies_part = 0
    total_bank = 0
    for group in transactions:
        total = 0
        for transaction in group.transaction_set.all():
            total += transaction.amount
            if transaction.category.is_goodies:
                goodies_part += transaction.amount
        group.total = total
        total_depenses += total
        if group.date_bank is not None:
            total_bank += total
    return {
        "transactions": transactions,
        "free_money": current_month.salary - total_depenses if current_month is not None else 0,
        "goodies_part": goodies_part,
        "bank_status": current_month.salary - total_bank if current_month is not None else 0,
        "current_month": current_month
    }


def basic_context_data(user):
    current_month = functions.get_current_month(user)
    with calendar.different_locale(settings.LOCALE):
        all_months = [{"id": m, "name": calendar.month_name[m].capitalize()} for m in range(1, 13)]
    months = sorted(Month.objects.all(), key=lambda m: (-m.year, -m.month))
    next_month = None
    next_year = None
    next_salary = None
    if len(months) > 0:
        next_month = months[0].month + 1 if months[0].month < 12 else 1
        next_year = months[0].year if months[0].month < 12 else months[0].year + 1
        next_salary = months[0].salary
    return {
        "categories": Category.objects.all().order_by("name"),
        "months": months,
        "next_month": next_month,
        "next_year": next_year,
        "next_salary": next_salary,
        "all_months": all_months,
        "current_month": current_month,
        "lang": settings.LANGUAGE_CODE
    }


def format_date(date):
    return datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")


class IndexView(TemplateView):
    template_name = "index.html"

    user = None
    data = None

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        c = super().get_context_data(**kwargs)
        self.user = self.request.user
        self.data = basic_context_data(self.user)
        return c


class LogoutView(View):

    def get(self, request):
        logout(request)
        csrf.rotate_token(request)
        return redirect("/")


class TransactionView(View):

    def get(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()
        return JsonResponse({"success": True,
                             "html": render_to_string("main_content.html",
                                                      {"view": {"data": content_data(request.user)}})})

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            date_t = request.POST["date_t"] if "date_t" in request.POST else None
            date_bank = request.POST["date_bank"] if "date_bank" in request.POST else None
            if date_bank == "":
                date_bank = None
            amount = float(request.POST["amount"].replace(",", "."))
            subject = request.POST["subject"]
            try:
                category = Category.objects.get(pk=request.POST["category"])
            except Category.DoesNotExist:
                return JsonResponse({"success": False,
                                     "message": "Category %s does not exists" % request.POST["category"]})
            try:
                month = Month.objects.get(pk=request.POST["month"]) \
                    if ("month" in request.POST and request.POST["month"] != "") else None
            except Month.DoesNotExist:
                return JsonResponse({"success": False, "message": "Month %s does not exists" % request.POST["month"]})
            tr_id = request.POST["tr_id"] if "tr_id" in request.POST else None
            group_id = request.POST["group_id"] if "group_id" in request.POST else None
            if tr_id == "":
                tr_id = None
        except (KeyError, ValueError):
            traceback.print_exc()
            return JsonResponse({"success": False, "message":
                                 "Bad query. Please contact the support to report the bug"})

        if (group_id is None or group_id == "") and (date_t is None or month is None):
            return JsonResponse({"success": False,
                                 "message": "Bad request (2). please contact the support to report the bug"})

        if group_id is None or group_id == "":
            try:
                date_regex = r"^\d\d/\d\d/\d\d\d\d$"
                if date_t is not None:
                    if not re.match(date_regex, date_t):
                        raise ValueError("Invalid date: %s" % date_t)
                    date_t = format_date(date_t)
                else:
                    raise ValueError("Date is required")
                if date_bank is not None and date_bank != "":
                    if not re.match(date_regex, date_bank):
                        raise ValueError("Invalid date: %s" % date_bank)
                    date_bank = format_date(date_bank)
            except ValueError as e:
                return JsonResponse({"success": False, "message": str(e)})

        try:
            if tr_id is None:
                # Add a new transaction
                try:
                    with db_transaction.atomic():
                        if group_id is None or group_id == "":
                            transaction_group = TransactionGroup(date_t=date_t, date_bank=date_bank, month=month)
                            transaction_group.save()
                        else:
                            try:
                                transaction_group = TransactionGroup.objects.get(pk=int(group_id))
                            except TransactionGroup.DoesNotExist:
                                return JsonResponse({"success": False, "message": "Transaction group does not exists"})
                        transaction = Transaction(amount=amount, subject=subject, category=category, group=transaction_group)
                        transaction.save()
                except:
                    db_transaction.rollback()
                    traceback.print_exc()
                    return JsonResponse({"success": False,
                                         "message": "An unexpected error occurred. Please contact the support"})
            else:
                # Edit existing transaction
                try:
                    with db_transaction.atomic():
                        try:
                            transaction = Transaction.objects.get(pk=tr_id)
                            transaction_group = transaction.group
                            transaction_group.date_t = date_t
                            transaction_group.date_bank = date_bank
                            transaction_group.month = month
                            transaction_group.save()
                            transaction.amount = amount
                            transaction.subject = subject
                            transaction.category = category
                            transaction.save()
                        except:
                            db_transaction.rollback()
                            raise Exception()
                except Transaction.DoesNotExist:
                    db_transaction.rollback()
                    return JsonResponse({"success": False, "message": "Transaction %s does not exists" % tr_id})
                except:
                    db_transaction.rollback()
                    traceback.print_exc()
                    return JsonResponse({"success": False,
                                         "message": "An unexpected error occurred. Please contact the support"})
        except:
            traceback.print_exc()
            return JsonResponse({"success": False,
                                 "message": "An unexpected error occurred. Please contact the support"})

        return JsonResponse({"success": True,
                             "html": render_to_string("main_content.html",
                                                      {"view": {"data": content_data(request.user)}})})


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
                                                      {"view": {"data": content_data(request.user)}})})

class MonthView(View):

    def get(self, request):
        return HttpResponseForbidden()

    def add_recurring_charges(self, r_file, user, month):
        with open(r_file, "r", encoding="utf-8") as rec_file:
            for line in rec_file:
                line = line.rstrip()
                if line != "":
                    parts = line.split("\t")
                    if len(parts) != 3:
                        raise Exception(_("Recurring charges file is not valid"))
                    subject = parts[0]
                    amount = float(parts[1].replace(",", "."))
                    category = Category.objects.get(name=parts[2].lower().capitalize())
                    group = TransactionGroup(date_t="%04d-%02d-%02d" % (month.year, month.month, 1), month=month)
                    group.save()
                    transaction = Transaction(subject=subject, amount=amount, category=category, group=group)
                    transaction.save()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()

        try:
            try:
                month = int(request.POST["month"])
                year = int(request.POST["year"])
                salary = float(request.POST["salary"].replace(",", "."))
            except (KeyError, ValueError):
                traceback.print_exc()
                return JsonResponse({"success": False, "message": _("Invalid request")})

            try:
                with db_transaction.atomic():
                    month_db = Month(month=month, year=year, salary=salary)
                    month_db.save()
                    functions.set_current_month(month_db, self.request.user)

                    if RecurringCharges.objects.filter(user=request.user).exists():
                        r_file = RecurringCharges.objects.get(user=request.user).file
                        if os.path.exists(r_file):
                            self.add_recurring_charges(r_file, request.user, month_db)
            except Exception as e:
                traceback.print_exc()
                db_transaction.rollback()
                return JsonResponse({"success": False, "message": str(e)})

            return JsonResponse({"success": True})
        except:
            traceback.print_exc()
            return JsonResponse({"success": False,
                                 "message": _("An unexpected error occurred. Please contact the support.")})


class BankDateView(View):

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            date_b = request.POST["date_b"]
            transactions = list(map(int, request.POST["transactions"].split("|")))
            date_regex = r"^\d\d/\d\d/\d\d\d\d$"
            if not re.match(date_regex, date_b):
                raise ValueError("Invalid date: %s" % date_b)
            date_b = format_date(date_b)
        except (KeyError, ValueError):
            traceback.print_exc()
            return JsonResponse({"success": False, "message": _("Invalid request")})

        try:
            with db_transaction.atomic():
                for transaction in transactions:
                    transaction = Transaction.objects.get(pk=transaction)
                    group = transaction.group
                    group.date_bank = date_b
                    group.save()
        except Transaction.DoesNotExist:
            db_transaction.rollback()
            return JsonResponse({"success": False, "message": _("Transaction does not exists")})
        except Exception as e:
            traceback.print_exc()
            db_transaction.rollback()
            return JsonResponse({"success": False, "message": str(e)})
        return JsonResponse({"success": True,
                             "html": render_to_string("main_content.html",
                                                      {"view": {"data": content_data(request.user)}})})


class DeleteTransaction(View):

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()
        try:
            transactions = list(map(int, request.POST["transactions"].split("|")))
        except (KeyError, ValueError):
            traceback.print_exc()
            return JsonResponse({"success": False, "message": _("Invalid request")})

        for transaction in transactions:
            try:
                tr_db = Transaction.objects.get(pk=transaction)
                group = tr_db.group
                tr_db.delete()
                if len(Transaction.objects.filter(group=group)) == 0:
                    group.delete()
            except Transaction.DoesNotExist:
                pass

        return JsonResponse({"success": True,
                             "html": render_to_string("main_content.html",
                                                      {"view": {"data": content_data(request.user)}})})

