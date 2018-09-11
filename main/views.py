from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "index.html"

    def data(self):
        dat = {}
        dat["mavar"] = "Ouais salut connard !"

        return dat
