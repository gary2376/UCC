#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
import json

from app.models.models import User, FeaturePermission, SystemFeature


def is_admin_user(user):
    """檢查是否為管理員 - 暫時允許所有登入用戶訪問"""
    return user.is_authenticated  # 暫時設為只需要登入即可


@login_required
@user_passes_test(is_admin_user)
def permission_management_view(request):
    """權限管理主頁面"""
    
    # 獲取所有用戶（除了超級用戶）
    users = User.objects.filter(is_superuser=False).order_by('username')
    
    # 獲取所有系統功能
    features = SystemFeature.objects.filter(is_active=True).order_by('name')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # 分頁
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 統計信息
    total_users = User.objects.filter(is_superuser=False).count()
    total_features = features.count()
    total_permissions = FeaturePermission.objects.count()
    
    context = {
        'page_obj': page_obj,
        'features': features,
        'search_query': search_query,
        'total_users': total_users,
        'total_features': total_features,
        'total_permissions': total_permissions,
    }
    
    return render(request, 'erp/permission_management_clean.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_permissions_view(request, user_id):
    """單個用戶權限管理頁面"""
    
    user = get_object_or_404(User, id=user_id)
    features = SystemFeature.objects.filter(is_active=True).order_by('name')
    
    # 獲取用戶現有權限
    user_permissions = {}
    permissions = FeaturePermission.objects.filter(user=user)
    for perm in permissions:
        user_permissions[perm.feature_code] = perm.permission_type
    
    context = {
        'target_user': user,
        'features': features,
        'user_permissions': user_permissions,
    }
    
    return render(request, 'user_permissions_clean.html', context)


@login_required
@user_passes_test(is_admin_user)
@csrf_exempt
@require_http_methods(["POST"])
def update_user_permissions(request, user_id):
    """更新用戶權限"""
    
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body)
        permissions_data = data.get('permissions', {})
        
        with transaction.atomic():
            # 清除用戶現有權限
            FeaturePermission.objects.filter(user=user).delete()
            
            # 添加新權限
            for feature_code, permission_type in permissions_data.items():
                if permission_type == 'edit':  # 只允許編輯權限
                    try:
                        feature = SystemFeature.objects.get(code=feature_code)
                        FeaturePermission.objects.create(
                            user=user,
                            feature_code=feature_code,
                            feature_name=feature.name,
                            permission_type=permission_type
                        )
                    except SystemFeature.DoesNotExist:
                        continue
        
        return JsonResponse({
            'success': True,
            'message': f'已成功更新 {user.username} 的權限設定'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新權限時發生錯誤：{str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_user)
@csrf_exempt
@require_http_methods(["POST"])
def batch_update_permissions(request):
    """批量更新權限"""
    
    try:
        data = json.loads(request.body)
        users_permissions = data.get('users_permissions', {})
        
        with transaction.atomic():
            for user_id, permissions_data in users_permissions.items():
                try:
                    user = User.objects.get(id=user_id)
                    
                    # 清除用戶現有權限
                    FeaturePermission.objects.filter(user=user).delete()
                    
                    # 添加新權限
                    for feature_code, permission_type in permissions_data.items():
                        if permission_type == 'edit':  # 只允許編輯權限
                            try:
                                feature = SystemFeature.objects.get(code=feature_code)
                                FeaturePermission.objects.create(
                                    user=user,
                                    feature_code=feature_code,
                                    feature_name=feature.name,
                                    permission_type=permission_type
                                )
                            except SystemFeature.DoesNotExist:
                                continue
                                
                except User.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'message': '批量權限更新成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'批量更新權限時發生錯誤：{str(e)}'
        }, status=500)





@login_required
def get_user_permissions_api(request, user_id):
    """獲取用戶權限API"""
    
    try:
        user = get_object_or_404(User, id=user_id)
        permissions = FeaturePermission.objects.filter(user=user)
        
        permissions_data = {}
        for perm in permissions:
            permissions_data[perm.feature_code] = {
                'permission_type': perm.permission_type,
                'feature_name': perm.feature_name
            }
        
        return JsonResponse({
            'success': True,
            'permissions': permissions_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'獲取權限時發生錯誤：{str(e)}'
        }, status=500)
