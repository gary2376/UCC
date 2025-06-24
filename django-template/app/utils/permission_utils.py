#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
權限檢查工具
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from app.models.models import FeaturePermission


def require_feature_permission(feature_code, permission_type='view'):
    """
    檢查用戶是否有特定功能的權限
    
    Args:
        feature_code: 功能代碼
        permission_type: 權限類型 ('view' 或 'edit')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # 超級用戶擁有所有權限
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 檢查用戶權限
            has_permission = FeaturePermission.objects.filter(
                user=user,
                feature_code=feature_code,
                permission_type__in=['edit'] if permission_type == 'edit' else ['view', 'edit']
            ).exists()
            
            if not has_permission:
                raise PermissionDenied(f"您沒有權限訪問此功能：{feature_code}")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def check_user_feature_permission(user, feature_code, permission_type='view'):
    """
    檢查用戶是否有特定功能的權限（用於模板和API）
    
    Args:
        user: 用戶對象
        feature_code: 功能代碼
        permission_type: 權限類型 ('view' 或 'edit')
    
    Returns:
        bool: 是否有權限
    """
    if user.is_superuser:
        return True
    
    if permission_type == 'edit':
        # 編輯權限只檢查 edit
        return FeaturePermission.objects.filter(
            user=user,
            feature_code=feature_code,
            permission_type='edit'
        ).exists()
    else:
        # 查看權限檢查 view 或 edit
        return FeaturePermission.objects.filter(
            user=user,
            feature_code=feature_code,
            permission_type__in=['view', 'edit']
        ).exists()


def get_user_permissions(user):
    """
    獲取用戶的所有權限
    
    Args:
        user: 用戶對象
    
    Returns:
        dict: 用戶權限字典 {feature_code: permission_type}
    """
    if user.is_superuser:
        return {'is_superuser': True}
    
    permissions = {}
    user_perms = FeaturePermission.objects.filter(user=user)
    
    for perm in user_perms:
        permissions[perm.feature_code] = perm.permission_type
    
    return permissions
