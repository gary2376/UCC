from django.core.management.base import BaseCommand
from app.models.models import SystemFeature


class Command(BaseCommand):
    help = '初始化系統基本功能'

    def handle(self, *args, **options):
        # 基本功能列表
        features = [
            {
                'code': 'file_upload',
                'name': '檔案上傳',
                'description': '上傳Excel文件和其他文檔'
            },
            {
                'code': 'upload_history',
                'name': '上傳歷史',
                'description': '查看和管理檔案上傳記錄'
            },
            {
                'code': 'green_bean_management',
                'name': '生豆管理',
                'description': '管理生豆入庫記錄'
            },
            {
                'code': 'raw_material_management',
                'name': '原料倉管理',
                'description': '管理原料倉進出記錄'
            },
            {
                'code': 'monthly_statistics',
                'name': '月度統計',
                'description': '查看月度統計報表'
            },
            {
                'code': 'user_management',
                'name': '用戶管理',
                'description': '管理系統用戶帳戶'
            },
            {
                'code': 'permission_management',
                'name': '權限管理',
                'description': '管理用戶權限設定'
            },
            {
                'code': 'system_settings',
                'name': '系統設定',
                'description': '系統基本設定和配置'
            },
            {
                'code': 'data_export',
                'name': '資料匯出',
                'description': '匯出各種報表和資料'
            },
            {
                'code': 'data_import',
                'name': '資料匯入',
                'description': '批量匯入資料到系統'
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
