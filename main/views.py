from django.views.generic import TemplateView, View
from django.template.loader import render_to_string
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext as _
from django.middleware import csrf

import main.functions as functions
import traceback
from main.models import Category, Month, Transaction


def context_data(user):
    current_month = functions.get_current_month(user)
    return {
        "categories": Category.objects.all().order_by("name"),
        "transactions": Transaction.objects.filter(month=current_month).order_by("date_t"),
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

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()


class ChangeMonthView(View):

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        t= 1
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
