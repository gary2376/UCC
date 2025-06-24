"""
模板標籤 - 權限檢查已移除
"""
from django import template

register = template.Library()


@register.simple_tag
def has_permission(user, permission_key):
    """所有用戶都有權限（已移除權限檢查）"""
    return True


@register.simple_tag
def user_role(user):
    """回傳基本用戶（已移除角色檢查）"""
    return 'user'


@register.simple_tag
def is_erp_manager(user):
    """所有用戶都有管理權限（已移除權限檢查）"""
    return True


@register.simple_tag
def is_erp_viewer(user):
    """所有用戶都有查看權限（已移除權限檢查）"""
    return True


@register.simple_tag
def has_basic_access(user):
    """所有用戶都有基本存取權限（已移除權限檢查）"""
    return True


@register.filter
def user_groups(user):
    """回傳空群組列表（已移除群組檢查）"""
    return []


@register.inclusion_tag('erp/permission_badge.html')
def permission_badge(user, permission_key):
    """顯示權限徽章（所有用戶都有權限）"""
    return {
        'has_permission': True,
        'permission_key': permission_key,
        'user': user
    }
