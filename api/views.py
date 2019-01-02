import datetime
import pytz
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
import json
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils.translation import ugettext as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from consts import ROLE_API


class ObtainExpiringAuthToken(ObtainAuthToken):

    def post(self, request, **kwargs):
        if "username" not in request.data or "password" not in request.data or "authorized_key" not in request.data:
            return HttpResponseBadRequest(json.dumps({"success": False, "message": _("Invalid request")}))
        if request.data["authorized_key"] not in settings.API_AUTHORIZED_KEYS:
            return HttpResponseForbidden(json.dumps({"success": False, "message": _("Unauthorized")}))
        user = authenticate(username=request.data["username"], password=request.data["password"])
        allowed = False
        for userrole in user.userrole_set.all():
            if userrole.role.id == ROLE_API:
                allowed = True
                break
        if not allowed:
            return HttpResponseForbidden(json.dumps({"success": False, "message": _("Unauthorized user")}))
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)

            utc = pytz.UTC
            utc_now = utc.localize(datetime.datetime.utcnow())
            if not created and utc.localize(token.created.replace(tzinfo=None)) < utc_now - datetime.timedelta(hours=1):
                token.delete()
                token = Token.objects.create(user=user)
                token.created = datetime.datetime.utcnow()
                token.save()

            response_data = {'token': token.key}
            return HttpResponse(json.dumps(response_data), content_type="application/json")


class Index(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        return Response("Bienvenue sur l'API")
