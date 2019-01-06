import datetime
import pytz
import re
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError
import json
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db import transaction as db_transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from consts import ROLE_API

import main.functions as functions
from main.models import Category, Transaction, TransactionGroup, Month


class ObtainExpiringAuthToken(ObtainAuthToken):

    def post(self, request, **kwargs):
        data = request.data
        if "username" not in data or "password" not in data or "authorized_key" not in data:
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid request")}))
        if data["authorized_key"] not in settings.API_AUTHORIZED_KEYS:
            return HttpResponseForbidden(json.dumps({"success": False, "message": _("Unauthorized")}))
        user = authenticate(username=data["username"], password=data["password"])
        if user is None:
            return HttpResponseForbidden(json.dumps({"success": False, "message": _("Bad username or password")}))
        allowed = False
        for userrole in user.userrole_set.all():
            if userrole.role.id == ROLE_API:
                allowed = True
                break
        if not allowed:
            return HttpResponseForbidden(json.dumps({"success": False, "message": _("Unauthorized user")}))
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)

            now = datetime.datetime.now(pytz.utc)
            if not created or token.created < now - datetime.timedelta(hours=1):
                token.delete()
                token = Token.objects.create(user=user)
                token.created = now
                token.save()

            all_cats = [{"name": c.name, "id": c.pk} for c in Category.objects.all().order_by("name")]
            u_group = user.usergroup.group
            months_o = sorted(Month.objects.filter(ugroup=u_group), key=lambda m: (-m.year, -m.month))
            months = []
            for month in months_o:
                months.append({
                    "id": month.pk,
                    "name": str(month)
                })
            current_month = functions.get_current_month(u_group)

            response_data = {'success': True, 'token': token.key, "categories": all_cats, "months": months,
                             "current_month": current_month.pk}
            return HttpResponse(json.dumps(response_data), content_type="application/json")


class Index(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        return Response("Bienvenue sur l'API")


class Transactions(APIView):

    parser_classes = (MultiPartParser, FormParser)

    @staticmethod
    def is_date_valid(date):
        match = re.match(r"(\d{2})/(\d{2})/(\d{4})", date)
        if match is None:
            return False
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        try:
            testdate = datetime.datetime(year=year, month=month, day=day)
        except ValueError:
            return False
        return True

    @staticmethod
    def is_transaction_valid(transaction):
        if "description" not in transaction or type(transaction["description"]) != str or "amount" not in transaction \
                or type(transaction["amount"]) not in [int, float] or "category" not in transaction \
                or type(transaction["category"]) != int:
            return False, None
        try:
            category = Category.objects.get(pk=transaction["category"])
        except Category.DoesNotExist:
            return False, _("category does not exists")
        transaction["category"] = category
        return True, transaction

    def post(self, request):
        data = request.POST

        # Check data:
        if "transaction_date" not in data:
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid request")}))
        transaction_date = data.get("transaction_date")
        if not self.is_date_valid(transaction_date):
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid date")}))
        if "transactions" not in data:
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid request")}))
        try:
            transactions = json.loads(data.get("transactions"))
        except ValueError:
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid request")}))

        for i in range(0, len(transactions)):
            valid, tr_or_message = self.is_transaction_valid(transactions[i])
            if valid:
                transactions[i] = tr_or_message
            else:
                return HttpResponseBadRequest(json.dumps({"success": False, "message": _("At least one transaction"
                                                                                         "is not valid") + \
                                                          ("" if tr_or_message is None else tr_or_message)}))

        if "month" not in data or (type(data.get("month")) != int and ((type(data.get("month")) == str and
                                   not data.get("month").isdigit()) or type(data.get("month")) != str)):
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid request")}))
        try:
            month = Month.objects.get(pk=int(data.get("month")))
        except Month.DoesNotExist:
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid month")}))

        # Insert data:
        try:
            with db_transaction.atomic():
                tr_group = TransactionGroup(date_t=functions.format_date(transaction_date), month=month)
                tr_group.save()

                for transaction in transactions:
                    tr = Transaction(group=tr_group, subject=transaction["description"], amount=transaction["amount"],
                                     category=transaction["category"])
                    tr.save()
        except:
            db_transaction.rollback()
            return HttpResponseServerError(json.dumps({"success": False, "message": _("Unexpected server error")}))

        response_data = {'success': True}
        return HttpResponse(json.dumps(response_data), content_type="application/json")
