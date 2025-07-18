#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
權限工具函數
用於檢查使用者是否有特定模型的權限，以及在模板中過濾顯示內容
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import render


def has_model_permission(user, app_label, model_name, action='view'):
    """
    檢查使用者是否有特定模型的權限
    
    Args:
        user: Django User 對象
        app_label: 應用名稱 (如 'app')
        model_name: 模型名稱 (如 'greenbeaninboundrecord')
        action: 操作類型 ('view', 'add', 'change', 'delete')
    
    Returns:
        bool: 是否有權限
    """
    if user.is_superuser:
        return True
    
    permission_codename = f"{action}_{model_name}"
    permission_name = f"{app_label}.{permission_codename}"
    
    return user.has_perm(permission_name)


def check_green_bean_permission(user):
    """檢查使用者是否有生豆相關權限"""
    return has_model_permission(user, 'app', 'greenbeaninboundrecord', 'view')


def check_raw_material_permission(user):
    """檢查使用者是否有原料相關權限"""
    return has_model_permission(user, 'app', 'rawmaterialwarehouserecord', 'view')


def get_user_accessible_sections(user):
    """
    獲取使用者可存取的系統區塊
    
    Returns:
        dict: 包含各個區塊的存取權限
    """
    if user.is_superuser:
        return {
            'green_bean': True,
            'raw_material': True,
            'dashboard': True,
            'admin': True,
        }
    
    return {
        'green_bean': check_green_bean_permission(user),
        'raw_material': check_raw_material_permission(user),
        'dashboard': (check_green_bean_permission(user) or check_raw_material_permission(user)),  # 有相關權限才能查看儀表板
        'admin': user.is_staff,  # 員工才能存取管理功能
    }


def require_model_permission(app_label, model_name, action='view'):
    """
    裝飾器：要求特定模型權限
    
    Usage:
        @require_model_permission('app', 'greenbeaninboundrecord', 'view')
        def green_bean_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not has_model_permission(request.user, app_label, model_name, action):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_green_bean_permission(action='view'):
    """生豆權限裝飾器"""
    return require_model_permission('app', 'greenbeaninboundrecord', action)


def require_raw_material_permission(action='view'):
    """原料權限裝飾器"""
    return require_model_permission('app', 'rawmaterialwarehouserecord', action)
