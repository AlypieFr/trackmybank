from django.views.generic import TemplateView, View
from django.contrib.auth import logout
from django.shortcuts import redirect


class IndexView(TemplateView):
    template_name = "index.html"

    def data(self):
        dat = {}
        dat["mavar"] = "Ouais salut connard !"

        return dat


class LogoutView(View):

    def get(self, request):
        logout(request)
        return redirect("/")
