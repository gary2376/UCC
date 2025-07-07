from django import template
from app.utils.activity_logger import get_recent_user_activities

register = template.Library()

@register.simple_tag
def get_recent_activities(limit=10):
    """
    獲取最近的用戶活動記錄
    """
    return get_recent_user_activities(limit=limit)