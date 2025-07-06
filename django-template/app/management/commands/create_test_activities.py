#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Django 管理命令：創建測試用戶活動記錄
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.models.models import UserActivityLog
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = '創建測試用戶活動記錄'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='創建的活動記錄數量'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # 確保有用戶存在
        if not User.objects.exists():
            self.stdout.write(
                self.style.WARNING('沒有找到用戶，請先創建用戶')
            )
            return
        
        users = list(User.objects.all())
        actions = ['create', 'update', 'delete', 'upload', 'view', 'export']
        descriptions = [
            '查看 ERP 儀表板',
            '新增生豆入庫記錄',
            '更新原料倉庫存',
            '上傳 Excel 文件',
            '匯出統計報表',
            '刪除過期記錄',
            '修改用戶權限',
            '查看庫存警示',
            '生成月度報表',
            '備份系統數據',
            '清理暫存檔案',
            '更新產品資訊',
            '檢查系統狀態',
            '處理異常記錄',
            '維護數據庫',
        ]
        
        # 創建活動記錄
        created_count = 0
        for i in range(count):
            # 隨機選擇用戶和操作
            user = random.choice(users)
            action = random.choice(actions)
            description = random.choice(descriptions)
            
            # 創建隨機時間（過去7天內）
            random_days = random.randint(0, 7)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            created_at = timezone.now() - timedelta(
                days=random_days,
                hours=random_hours,
                minutes=random_minutes
            )
            
            # 創建活動記錄
            activity = UserActivityLog.objects.create(
                user=user,
                action=action,
                description=description,
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                details={
                    'test_data': True,
                    'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                    'random_id': random.randint(1000, 9999)
                }
            )
            
            # 手動設置創建時間
            activity.created_at = created_at
            activity.save()
            
            created_count += 1
            
            if created_count % 5 == 0:
                self.stdout.write(f'已創建 {created_count} 筆活動記錄...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功創建了 {created_count} 筆用戶活動記錄！'
            )
        )
