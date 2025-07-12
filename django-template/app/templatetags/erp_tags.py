"""
ERP 相關的模板標籤
"""
from django import template
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.simple_tag
def get_recent_activities():
    """獲取最近的用戶活動記錄"""
    # 由於沒有具體的活動記錄模型，我們返回一個模擬的活動列表
    # 您可以根據實際的模型來修改這個函數
    try:
        recent_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).order_by('-last_login')[:10]
        
        activities = []
        for user in recent_users:
            activities.append({
                'user': user,
                'description': f'用戶 {user.username} 最近登入系統',
                'created_at': user.last_login or timezone.now(),
            })
        
        return activities
    except Exception:
        # 如果出現錯誤，返回空列表
        return []


@register.simple_tag
def get_system_stats():
    """獲取系統統計資訊"""
    try:
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
        }
    except Exception:
        return {
            'total_users': 0,
            'active_users': 0,
        }


@register.filter
def format_activity_time(value):
    """格式化活動時間"""
    if not value:
        return ''
    
    now = timezone.now()
    diff = now - value
    
    if diff.days > 0:
        return f'{diff.days} 天前'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} 小時前'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} 分鐘前'
    else:
        return '剛剛'


@register.inclusion_tag('admin/activity_widget.html')
def activity_widget():
    """活動記錄小工具"""
    activities = get_recent_activities()
    return {
        'activities': activities[:5],  # 只顯示最近 5 個活動
    }
