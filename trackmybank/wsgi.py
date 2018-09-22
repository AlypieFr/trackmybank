# TrackMyBank, a simple bank management tool
# 
# Copyright (C) 2018 Floreal Cabanettes <comm@flo-art.fr>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3.0

"""
WSGI config for trackmybank project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trackmybank.settings")

application = get_wsgi_application()
