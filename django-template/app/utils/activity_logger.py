#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用戶活動記錄工具
"""
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from app.models.models import UserActivityLog


def log_user_activity(user, action, description, content_object=None, request=None, details=None):
    """
    記錄用戶活動
    
    Args:
        user: 用戶對象
        action: 操作類型 ('create', 'update', 'delete', 'upload', 'export', 'login', 'logout')
        description: 操作描述
        content_object: 相關的對象（可選）
        request: HTTP 請求對象（可選）
        details: 額外詳細信息（可選）
    """
    try:
        activity_data = {
            'user': user,
            'action': action,
            'description': description,
            'details': details or {}
        }
        
        # 如果有相關對象，設置 content_type 和 object_id
        if content_object:
            activity_data['content_type'] = ContentType.objects.get_for_model(content_object)
            activity_data['object_id'] = content_object.pk
        
        # 如果有請求對象，提取 IP 和 User-Agent
        if request:
            # 獲取真實 IP（考慮代理）
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            activity_data['ip_address'] = ip
            activity_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # 創建活動記錄
        UserActivityLog.objects.create(**activity_data)
        
        # 同時記錄到 Django 的管理員日誌系統
        _log_to_django_admin(user, action, description, content_object)
        
    except Exception as e:
        # 記錄錯誤但不影響主要業務流程
        print(f"記錄用戶活動失敗: {e}")


def _log_to_django_admin(user, action, description, content_object=None):
    """
    記錄操作到 Django 管理員日誌系統
    
    Args:
        user: 用戶對象
        action: 操作類型
        description: 操作描述
        content_object: 相關的對象（可選）
    """
    try:
        # 將我們的動作類型映射到 Django 的日誌動作
        action_flag_map = {
            'create': ADDITION,
            'update': CHANGE,
            'delete': DELETION,
            'upload': ADDITION,  # 上傳視為新增
            'export': CHANGE,    # 匯出視為變更
            'batch_delete': DELETION,
            'delete_upload_record': DELETION,
        }
        
        action_flag = action_flag_map.get(action, CHANGE)  # 預設為變更
        
        # 如果有相關對象，記錄到該對象的日誌
        if content_object:
            LogEntry.objects.log_action(
                user_id=user.pk,
                content_type_id=ContentType.objects.get_for_model(content_object).pk,
                object_id=content_object.pk,
                object_repr=str(content_object),
                action_flag=action_flag,
                change_message=description
            )
        else:
            # 如果沒有相關對象，記錄到 UserActivityLog 模型
            LogEntry.objects.log_action(
                user_id=user.pk,
                content_type_id=ContentType.objects.get_for_model(UserActivityLog).pk,
                object_id=None,
                object_repr=f"系統操作: {description}",
                action_flag=action_flag,
                change_message=description
            )
    except Exception as e:
        # 記錄錯誤但不影響主要業務流程
        print(f"記錄到管理員日誌失敗: {e}")


def get_recent_user_activities(user=None, limit=50, exclude_actions=None):
    """
    獲取最近的用戶活動記錄
    
    Args:
        user: 特定用戶（可選），如果不指定則返回所有用戶的活動
        limit: 返回記錄數量限制
        exclude_actions: 要排除的操作類型列表（可選）
    
    Returns:
        QuerySet: 用戶活動記錄
    """
    queryset = UserActivityLog.objects.all().select_related('user').order_by('-created_at')
    
    if user:
        queryset = queryset.filter(user=user)
    
    # 排除指定的操作類型
    if exclude_actions:
        queryset = queryset.exclude(action__in=exclude_actions)
    
    return queryset[:limit]


def get_user_activity_summary(days=30):
    """
    獲取用戶活動統計摘要
    
    Args:
        days: 統計天數
    
    Returns:
        dict: 統計信息
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count
    
    start_date = timezone.now() - timedelta(days=days)
    
    activities = UserActivityLog.objects.filter(created_at__gte=start_date)
    
    summary = {
        'total_activities': activities.count(),
        'unique_users': activities.values('user').distinct().count(),
        'activities_by_action': activities.values('action').annotate(count=Count('action')),
        'activities_by_user': activities.values('user__username').annotate(count=Count('user')).order_by('-count')[:10],
        'recent_activities': activities.order_by('-created_at')[:20]
    }
    
    return summary


def get_important_user_activities(user=None, limit=50):
    """
    獲取重要的用戶活動記錄（包含所有檔案和資料操作）
    
    Args:
        user: 特定用戶（可選），如果不指定則返回所有用戶的活動
        limit: 返回記錄數量限制
    
    Returns:
        QuerySet: 重要的用戶活動記錄
    """
    # 定義重要操作類型 - 包含所有檔案和資料操作
    important_actions = ['create', 'update', 'upload', 'delete', 'delete_upload_record', 'batch_delete', 'export']
    
    queryset = UserActivityLog.objects.filter(action__in=important_actions).select_related('user')
    
    if user:
        queryset = queryset.filter(user=user)
    
    return queryset.order_by('-created_at')[:limit]


def get_weekly_charts_data():
    """
    獲取生豆入庫和原料倉管理的每日統計數據，用於繪製折線圖
    顯示過去14天的數據，包含今天到目前為止的數據
    
    Returns:
        dict: 包含兩個系列數據的字典
    """
    from django.utils import timezone
    from datetime import timedelta
    from app.models import GreenBeanInboundRecord, RawMaterialWarehouseRecord
    
    now = timezone.now()
    
    # 計算過去14天的數據（包含今天）
    days_data = []
    green_bean_data = []
    raw_material_data = []
    
    for i in range(13, -1, -1):  # 從13天前到今天
        # 計算該天的開始時間
        day_start = now - timedelta(days=i)
        day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 計算該天的結束時間
        if i == 0:  # 今天：結束時間是現在
            day_end = now
            day_label = day_start.strftime('%m/%d') + '(今日)'
        else:  # 過去的天：結束時間是當天晚上11:59:59
            day_end = day_start + timedelta(hours=23, minutes=59, seconds=59)
            day_label = day_start.strftime('%m/%d')
        
        days_data.append(day_label)
        
        # 計算生豆入庫記錄數 - 優先使用 created_at，因為 record_time 可能是歷史日期
        green_bean_count = 0
        try:
            # 使用 created_at（記錄創建時間）而不是 record_time（業務記錄時間）
            green_bean_count = GreenBeanInboundRecord.objects.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()
            
        except Exception as e:
            green_bean_count = 0
            
        green_bean_data.append(green_bean_count)
        
        # 計算原料倉記錄數
        raw_material_count = 0
        try:
            raw_material_count = RawMaterialWarehouseRecord.objects.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()
        except Exception as e:
            raw_material_count = 0
            
        raw_material_data.append(raw_material_count)
    
    return {
        'weeks': days_data,  # 保持原來的鍵名以免破壞前端程式碼
        'green_bean_data': green_bean_data,
        'raw_material_data': raw_material_data
    }


def get_weekly_records_comparison():
    """
    獲取本週記錄數與上個月週均記錄數的比較
    
    Returns:
        dict: 包含本週記錄數、上個月週均記錄數、增減百分比等統計信息
    """
    from django.utils import timezone
    from datetime import timedelta, datetime
    import calendar
    
    now = timezone.now()
    
    # 計算本週開始時間（週一）
    days_since_monday = now.weekday()
    this_week_start = now - timedelta(days=days_since_monday)
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 計算上個月的開始和結束時間
    if now.month == 1:
        last_month_year = now.year - 1
        last_month = 12
    else:
        last_month_year = now.year
        last_month = now.month - 1
    
    # 使用當前時區創建日期時間
    last_month_start = now.replace(
        year=last_month_year, 
        month=last_month, 
        day=1, 
        hour=0, 
        minute=0, 
        second=0, 
        microsecond=0
    )
    
    # 計算上個月有多少天
    last_month_days = calendar.monthrange(last_month_year, last_month)[1]
    last_month_end = last_month_start + timedelta(days=last_month_days)
    
    # 計算上個月有多少週（大約）
    last_month_weeks = last_month_days / 7
    
    # 定義重要操作類型 - 包含所有檔案和資料操作
    important_actions = ['create', 'update', 'upload', 'delete', 'delete_upload_record', 'batch_delete', 'export']
    
    try:
        # 計算本週的記錄數
        this_week_count = UserActivityLog.objects.filter(
            action__in=important_actions,
            created_at__gte=this_week_start
        ).count()
        
        # 計算上個月的總記錄數
        last_month_total = UserActivityLog.objects.filter(
            action__in=important_actions,
            created_at__gte=last_month_start,
            created_at__lt=last_month_end
        ).count()
        
        # 計算上個月週均記錄數
        last_month_weekly_avg = round(last_month_total / last_month_weeks, 1) if last_month_weeks > 0 else 0
        
        # 計算增減百分比
        if last_month_weekly_avg > 0:
            percentage_change = round(((this_week_count - last_month_weekly_avg) / last_month_weekly_avg) * 100, 1)
        else:
            percentage_change = 100 if this_week_count > 0 else 0
        
        # 判斷趨勢
        if percentage_change > 0:
            trend = 'up'
            trend_text = '上升'
        elif percentage_change < 0:
            trend = 'down'
            trend_text = '下降'
        else:
            trend = 'stable'
            trend_text = '持平'
        
        return {
            'this_week_count': this_week_count,
            'last_month_weekly_avg': last_month_weekly_avg,
            'percentage_change': percentage_change,
            'trend': trend,
            'trend_text': trend_text,
            'week_start': this_week_start.strftime('%Y-%m-%d'),
            'comparison_month': f"{last_month_year}年{last_month}月"
        }
    
    except Exception as e:
        # 如果出現錯誤，返回默認值
        print(f"計算週統計時出現錯誤: {e}")
        return {
            'this_week_count': 0,
            'last_month_weekly_avg': 0,
            'percentage_change': 0,
            'trend': 'stable',
            'trend_text': '持平',
            'week_start': now.strftime('%Y-%m-%d'),
            'comparison_month': f"{last_month_year}年{last_month}月"
        }
