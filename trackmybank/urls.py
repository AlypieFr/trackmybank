"""trackmybank URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required
from django.views.i18n import JavaScriptCatalog

from main.views import IndexView, LogoutView, TransactionView, ChangeMonthView, MonthView

favicon_view = RedirectView.as_view(url='/static/images/favicon.ico', permanent=True)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^favicon\.ico$', favicon_view),
    url(r'^logout/', login_required(LogoutView.as_view(), login_url="/admin/login/"), name='logout'),
    url(r'^transaction/', TransactionView.as_view(), name='transaction'),
    url(r'^select-month/', ChangeMonthView.as_view(), name='select_month'),
    url(r'^month/', MonthView.as_view(), name='month'),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    url(r'^$', login_required(IndexView.as_view(), login_url="/admin/login/"), name='login'),
]
