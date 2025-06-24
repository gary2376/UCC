# -*- coding: utf-8 -*-
"""
清空所有權限設置
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = '清空所有權限和群組設置'
    
    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write('=== 開始清理權限設置 ===')
        
        # 1. 移除所有用戶的群組關聯
        self.stdout.write('1. 清除所有用戶的群組關聯...')
        for user in User.objects.all():
            groups_before = list(user.groups.values_list('name', flat=True))
            user.groups.clear()
            if groups_before:
                self.stdout.write(f'   - 用戶 {user.username}: 移除群組 {groups_before}')
            else:
                self.stdout.write(f'   - 用戶 {user.username}: 無群組需要移除')
        
        # 2. 刪除所有群組
        self.stdout.write('2. 刪除所有群組...')
        groups_count = Group.objects.count()
        if groups_count > 0:
            group_names = list(Group.objects.values_list('name', flat=True))
            Group.objects.all().delete()
            self.stdout.write(f'   - 已刪除 {groups_count} 個群組: {group_names}')
        else:
            self.stdout.write('   - 沒有群組需要刪除')
        
        # 3. 顯示當前狀態
        self.stdout.write('3. 檢查清理結果...')
        remaining_groups = Group.objects.count()
        self.stdout.write(f'   - 剩餘群組數量: {remaining_groups}')
        
        for user in User.objects.all():
            user_groups = user.groups.count()
            self.stdout.write(f'   - 用戶 {user.username}: {user_groups} 個群組')
        
        self.stdout.write(self.style.SUCCESS('✅ 權限清理完成！'))
        self.stdout.write('')
        self.stdout.write('現在所有用戶都沒有任何群組權限。')
        self.stdout.write('只有超級用戶(superuser)仍然擁有完整權限。')
