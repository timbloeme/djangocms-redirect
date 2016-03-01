# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.forms import ModelForm
from django.contrib import admin
from cms.forms.widgets import PageSmartLinkWidget
from .models import Redirect


class RedirectForm(ModelForm):
    class Meta:
        model = Redirect
        fields = ['site', 'old_path', 'new_path', 'response_code']

    def __init__(self, *args, **kwargs):
        super(RedirectForm, self).__init__(*args, **kwargs)
        self.fields['old_path'].widget = PageSmartLinkWidget(ajax_view='admin:cms_page_get_published_pagelist')
        self.fields['new_path'].widget = PageSmartLinkWidget(ajax_view='admin:cms_page_get_published_pagelist')


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ('old_path', 'new_path', 'response_code')
    list_filter = ('site',)
    search_fields = ('old_path', 'new_path')
    radio_fields = {'site': admin.VERTICAL}
    form = RedirectForm 