# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import http
from django.apps import apps
from django.conf import settings
from .models import Redirect
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured


class RedirectFallbackMiddleware(object):

    # Defined as class-level attributes to be subclassing-friendly.
    response_gone_class = http.HttpResponseGone
    response_redirect_class = http.HttpResponsePermanentRedirect

    def __init__(self):
        if not apps.is_installed('django.contrib.sites'):
            raise ImproperlyConfigured(
                "You cannot use RedirectFallbackMiddleware when "
                "django.contrib.sites is not installed."
            )

    def process_request(self, request):

        full_path = request.get_full_path()
        current_site = get_current_site(request)
        #response = http.HttpResponseRedirect('/')
        r = None
        try:
            r = Redirect.objects.get(site=current_site, old_path=full_path)
        except Redirect.DoesNotExist:
            pass
        if r is None and settings.APPEND_SLASH and not request.path.endswith('/'):
            try:
                r = Redirect.objects.get(
                    site=current_site,
                    old_path=request.get_full_path(force_append_slash=True),
                )
            except Redirect.DoesNotExist:
                pass
        if r is not None:
            if r.new_path == '':
                return self.response_gone_class()
            return self.response_redirect_class(r.new_path)
        #return response