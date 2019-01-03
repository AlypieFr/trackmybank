from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import Index, Transactions, ObtainExpiringAuthToken

urlpatterns = [
    url(r'^$', Index.as_view()),
    url(r'^transactions/', Transactions.as_view()),
    url(r'^auth/', ObtainExpiringAuthToken.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
