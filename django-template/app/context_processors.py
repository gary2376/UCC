#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模板上下文處理器
為所有模板提供權限相關的上下文變數
"""
from app.utils.permission_utils import get_user_accessible_sections


def permission_context(request):
    """
    為模板提供權限上下文
    
    在模板中可以使用：
    - user_permissions.green_bean
    - user_permissions.raw_material
    - user_permissions.dashboard
    - user_permissions.admin
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'user_permissions': get_user_accessible_sections(request.user)
        }
    return {
        'user_permissions': {
            'green_bean': False,
            'raw_material': False,
            'dashboard': False,
            'admin': False,
        }
    }



