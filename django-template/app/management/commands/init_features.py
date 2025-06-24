from django.core.management.base import BaseCommand
from app.models.models import SystemFeature


class Command(BaseCommand):
    help = '初始化系統基本功能'

    def handle(self, *args, **options):
        features = [
            {
                'code': 'file_upload',
                'name': '檔案上傳',
                'description': '允許上傳檔案到系統中'
            },
            {
                'code': 'upload_history',
                'name': '上傳歷史',
                'description': '查看和管理上傳檔案的歷史記錄'
            },
            {
                'code': 'green_bean_management',
                'name': '生豆管理',
                'description': '管理生豆入庫記錄'
            },
            {
                'code': 'raw_material_management',
                'name': '原料管理',
                'description': '管理原料倉庫記錄'
            },
            {
                'code': 'monthly_summary',
                'name': '月度統計',
                'description': '查看月度統計資料'
            },
            {
                'code': 'user_management',
                'name': '用戶管理',
                'description': '管理系統用戶'
            },
            {
                'code': 'permission_management',
                'name': '權限管理',
                'description': '管理用戶權限設定'
            },
            {
                'code': 'system_settings',
                'name': '系統設定',
                'description': '系統基本設定'
            },
        ]

        created_count = 0
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
                    self.style.SUCCESS(f'創建功能: {feature.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'功能已存在: {feature.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'初始化完成！共創建 {created_count} 個新功能。')
        )
