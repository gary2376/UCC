#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
設置用戶活動記錄權限的管理命令
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app.models.models import UserActivityLog


class Command(BaseCommand):
    help = '設置用戶活動記錄權限群組'

    def handle(self, *args, **options):
        # 獲取UserActivityLog的內容類型
        content_type = ContentType.objects.get_for_model(UserActivityLog)
        
        # 獲取或創建查看用戶活動記錄的權限
        view_permission, created = Permission.objects.get_or_create(
            codename='view_useractivitylog',
            name='Can view user activity log',
            content_type=content_type,
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ 創建權限: {view_permission.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  權限已存在: {view_permission.name}')
            )
        
        # 創建用戶活動記錄管理員群組
        group, created = Group.objects.get_or_create(
            name='用戶活動記錄管理員'
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ 創建群組: {group.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  群組已存在: {group.name}')
            )
        
        # 將權限添加到群組
        group.permissions.add(view_permission)
        
        self.stdout.write(
            self.style.SUCCESS('✅ 權限設置完成！')
        )
        self.stdout.write('')
        self.stdout.write('📋 使用說明：')
        self.stdout.write('1. 超級用戶可以直接查看用戶活動記錄')
        self.stdout.write('2. 要給其他用戶查看權限，請將他們加入「用戶活動記錄管理員」群組')
        self.stdout.write('3. 或者直接給用戶分配「Can view user activity log」權限')
