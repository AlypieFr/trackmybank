from django.views.generic import TemplateView, View
from django.contrib.auth import logout
from django.shortcuts import redirect

from main.models import Category


class IndexView(TemplateView):
    template_name = "index.html"

    def data(self):
        dat = {
            "categories": Category.objects.all().order_by("name")
        }

        return dat


class LogoutView(View):

    def get(self, request):
        logout(request)
        return redirect("/")
