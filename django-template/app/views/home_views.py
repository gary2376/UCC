#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

def home_view(request):
    """
    根路徑重定向 - 直接重定向到Django Admin
    """
    # 直接重定向到Django Admin，確保URL統一
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect('/admin/')

@require_http_methods(["GET"])
def health_check(request):
    """健康檢查端點"""
    return HttpResponse("OK", content_type="text/plain")
