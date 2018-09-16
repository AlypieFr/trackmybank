from django.views.generic import TemplateView, View
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

from main.models import Category, Month, Transaction


class IndexView(TemplateView):
    template_name = "index.html"

    def data(self):
        current_month = Month.objects.last()
        return {
            "categories": Category.objects.all().order_by("name"),
            "transactions": Transaction.objects.filter(month=current_month).order_by("date_t"),
            "months": sorted(Month.objects.all(), key=lambda m: (-m.year, -m.month))
        }


class LogoutView(View):

    def get(self, request):
        logout(request)
        return redirect("/")


class TransactionView(View):

    def get(self, request):
        return HttpResponseForbidden()

    def post(self, request):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()