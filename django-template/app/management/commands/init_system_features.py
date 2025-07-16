from django.core.management.base import BaseCommand
from app.models.models import SystemFeature


class Command(BaseCommand):
    help = '初始化系統基本功能'

    def handle(self, *args, **options):
        # 基本功能列表 - 根據需求調整為6個主要功能
        features = [
            {
                'code': 'green_bean_records',
                'name': '生豆入庫記錄',
                'description': '管理生豆入庫記錄，包括查看、新增、編輯和刪除記錄'
            },
            {
                'code': 'raw_material_management',
                'name': '原料倉管理',
                'description': '管理原料倉進出記錄和庫存狀況'
            },
            {
                'code': 'monthly_statistics',
                'name': '月度統計',
                'description': '查看和分析月度統計報表'
            },
            {
                'code': 'system_users',
                'name': '系統用戶',
                'description': '管理系統用戶帳戶和基本資訊'
            },
            {
                'code': 'admin_management',
                'name': '管理員',
                'description': '系統管理員功能和高級設定'
            },
            {
                'code': 'permission_management',
                'name': '權限管理',
                'description': '管理用戶權限設定和功能授權'
            }
        ]

        created_count = 0
        updated_count = 0

        for feature_data in features:
            feature, created = SystemFeature.objects.get_or_create(
                code=feature_data['code'],
                defaults={
                    'name': feature_data['name'],
                    'description': feature_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 創建功能: {feature.name} ({feature.code})')
                )
            else:
                # 更新現有功能的名稱和描述（如果需要）
                if feature.name != feature_data['name'] or feature.description != feature_data['description']:
                    feature.name = feature_data['name']
                    feature.description = feature_data['description']
                    feature.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠ 更新功能: {feature.name} ({feature.code})')
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(f'- 功能已存在: {feature.name} ({feature.code})')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n初始化完成！\n'
                f'新增功能: {created_count} 項\n'
                f'更新功能: {updated_count} 項\n'
                f'總功能數: {SystemFeature.objects.count()} 項'
            )
        )
