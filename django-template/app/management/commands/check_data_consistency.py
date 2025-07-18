from django.core.management.base import BaseCommand
from django.db import transaction
from app.models.models import FileUploadRecord, GreenBeanInboundRecord, UploadRecordRelation


class Command(BaseCommand):
    help = '檢查並清理孤立的記錄，確保上傳記錄與生豆記錄的一致性'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='僅檢查但不執行刪除操作',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='修復發現的不一致問題',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_issues = options['fix']
        
        self.stdout.write(self.style.SUCCESS('開始檢查記錄一致性...'))
        
        # 1. 檢查孤立的 UploadRecordRelation (關聯的上傳記錄不存在)
        orphaned_relations = UploadRecordRelation.objects.filter(
            upload_record__isnull=True
        )
        
        if orphaned_relations.exists():
            count = orphaned_relations.count()
            self.stdout.write(
                self.style.WARNING(f'發現 {count} 筆孤立的關聯記錄 (上傳記錄已被刪除)')
            )
            if fix_issues and not dry_run:
                orphaned_relations.delete()
                self.stdout.write(self.style.SUCCESS(f'已清理 {count} 筆孤立的關聯記錄'))
        
        # 2. 檢查 UploadRecordRelation 指向不存在的生豆記錄
        orphaned_green_bean_relations = []
        for relation in UploadRecordRelation.objects.filter(content_type='green_bean'):
            try:
                GreenBeanInboundRecord.objects.get(id=relation.object_id)
            except GreenBeanInboundRecord.DoesNotExist:
                orphaned_green_bean_relations.append(relation)
        
        if orphaned_green_bean_relations:
            count = len(orphaned_green_bean_relations)
            self.stdout.write(
                self.style.WARNING(f'發現 {count} 筆指向不存在生豆記錄的關聯')
            )
            if fix_issues and not dry_run:
                for relation in orphaned_green_bean_relations:
                    relation.delete()
                self.stdout.write(self.style.SUCCESS(f'已清理 {count} 筆無效關聯'))
        
        # 3. 檢查沒有關聯記錄的上傳記錄
        uploads_without_relations = FileUploadRecord.objects.filter(
            file_type='green_bean',
            uploadrecordrelation__isnull=True
        ).exclude(status='failed')
        
        if uploads_without_relations.exists():
            count = uploads_without_relations.count()
            self.stdout.write(
                self.style.WARNING(f'發現 {count} 筆沒有關聯記錄的成功上傳')
            )
            
            for upload in uploads_without_relations:
                self.stdout.write(f'  - {upload.file_name} (ID: {upload.id})')
                
                # 嘗試通過 created_record_ids 找回關聯
                if upload.created_record_ids:
                    found_records = 0
                    for record_id in upload.created_record_ids:
                        try:
                            record = GreenBeanInboundRecord.objects.get(id=record_id)
                            if fix_issues and not dry_run:
                                UploadRecordRelation.objects.get_or_create(
                                    upload_record=upload,
                                    content_type='green_bean',
                                    object_id=record.id
                                )
                            found_records += 1
                        except GreenBeanInboundRecord.DoesNotExist:
                            pass
                    
                    if found_records > 0:
                        self.stdout.write(f'    找到 {found_records} 筆相關記錄')
                        if fix_issues and not dry_run:
                            self.stdout.write('    已重新建立關聯')
        
        # 4. 檢查被刪除上傳記錄但仍存在的生豆記錄
        # 這種情況比較複雜，我們需要找出哪些生豆記錄沒有對應的上傳記錄
        all_green_bean_records = GreenBeanInboundRecord.objects.all()
        records_without_upload = []
        
        for record in all_green_bean_records:
            # 檢查是否有關聯記錄
            has_relation = UploadRecordRelation.objects.filter(
                content_type='green_bean',
                object_id=record.id
            ).exists()
            
            if not has_relation:
                # 檢查是否在任何上傳記錄的 created_record_ids 中
                uploads_with_this_record = FileUploadRecord.objects.filter(
                    created_record_ids__contains=[str(record.id)]
                )
                
                if not uploads_with_this_record.exists():
                    records_without_upload.append(record)
        
        if records_without_upload:
            count = len(records_without_upload)
            self.stdout.write(
                self.style.WARNING(f'發現 {count} 筆沒有上傳記錄關聯的生豆記錄 (可能是手動新增或遺留記錄)')
            )
            
            for record in records_without_upload[:10]:  # 只顯示前10筆
                self.stdout.write(f'  - {record.order_number} - {record.green_bean_name}')
            
            if count > 10:
                self.stdout.write(f'  ... 還有 {count - 10} 筆記錄')
        
        # 5. 統計報告
        total_uploads = FileUploadRecord.objects.filter(file_type='green_bean').count()
        total_relations = UploadRecordRelation.objects.filter(content_type='green_bean').count()
        total_green_beans = GreenBeanInboundRecord.objects.count()
        
        self.stdout.write(self.style.SUCCESS('\n=== 統計報告 ==='))
        self.stdout.write(f'上傳記錄總數: {total_uploads}')
        self.stdout.write(f'關聯記錄總數: {total_relations}')
        self.stdout.write(f'生豆記錄總數: {total_green_beans}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n這是預覽模式，未執行任何修改。'))
            self.stdout.write('如要修復問題，請使用 --fix 參數')
        elif not fix_issues:
            self.stdout.write(self.style.WARNING('\n如要修復發現的問題，請使用 --fix 參數'))
        
        self.stdout.write(self.style.SUCCESS('\n檢查完成！'))
