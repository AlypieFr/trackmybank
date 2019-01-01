import datetime
import pytz
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.utils.translation import ugettext as _


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):

        try:
            token = self.get_model().objects.get(key=key)
        except self.get_model().DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted'))

        utc = pytz.UTC
        utc_now = utc.localize(datetime.datetime.utcnow())

        if utc.localize(token.created.replace(tzinfo=None)) < utc_now - datetime.timedelta(hours=1):
            raise exceptions.AuthenticationFailed(_('Token has expired'))

        return token.user, token
