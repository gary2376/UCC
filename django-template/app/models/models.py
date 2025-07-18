from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid


class EditRecordsManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().prefetch_related('model_a', 'model_b')


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        db_table = 'app_user'
        verbose_name = '使用者'
        verbose_name_plural = '使用者'


class AdminUser(models.Model):
    class Meta:
        db_table = 'app_adminuser'
        verbose_name = '管理員'
        verbose_name_plural = '管理員'

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone_number = models.CharField('聯絡電話', max_length=10, validators=[
        RegexValidator(regex=r'^09\d{8}$', message="請依照格式輸入")
    ], help_text='輸入範例：0900123456')
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return self.user.get_full_name()


class FeaturePermission(models.Model):
    """功能權限模型"""
    PERMISSION_CHOICES = [
        ('view', '瀏覽'),
        ('edit', '編輯'),
    ]
    
    class Meta:
        db_table = 'app_feature_permission'
        verbose_name = '功能權限'
        verbose_name_plural = '功能權限'
        unique_together = ['user', 'feature_code']
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    feature_code = models.CharField('功能代碼', max_length=50)
    feature_name = models.CharField('功能名稱', max_length=100)
    permission_type = models.CharField('權限類型', max_length=10, choices=PERMISSION_CHOICES)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.feature_name} ({self.get_permission_type_display()})"


class SystemFeature(models.Model):
    """系統功能模型"""
    class Meta:
        db_table = 'app_system_feature'
        verbose_name = '系統功能'
        verbose_name_plural = '系統功能'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField('功能代碼', max_length=50, unique=True)
    name = models.CharField('功能名稱', max_length=100)
    description = models.TextField('功能描述', blank=True)
    is_active = models.BooleanField('是否啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    def __str__(self):
        return self.name


# ERP 系統相關模型
class GreenBeanInboundRecord(models.Model):
    """生豆入庫記錄"""
    class Meta:
        db_table = 'app_green_bean_inbound_record'
        verbose_name = '生豆入庫記錄'
        verbose_name_plural = '生豆入庫記錄'
        ordering = ['-record_time']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 基本資訊
    is_abnormal = models.BooleanField('異常', default=False)
    record_time = models.DateTimeField('記錄時間', null=True, blank=True)
    order_number = models.CharField('單號', max_length=50, default='')
    roasted_item_sequence = models.IntegerField('炒豆項次', null=True, blank=True)
    green_bean_item_sequence = models.IntegerField('生豆項次', null=True, blank=True)
    batch_sequence = models.IntegerField('波次', null=True, blank=True)
    execution_status = models.CharField('執行狀態', max_length=20, blank=True, default='')
    
    # 生豆資訊
    green_bean_batch_number = models.CharField('生豆批號', max_length=50, blank=True, default='')
    green_bean_code = models.CharField('生豆料號', max_length=50, blank=True, default='')
    green_bean_name = models.CharField('生豆名稱', max_length=100, blank=True, default='')
    green_bean_storage_silo = models.CharField('生豆入庫筒倉', max_length=50, blank=True, default='')
    
    # 重量和數量
    bag_weight_kg = models.DecimalField('一袋重量(kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    input_bag_count = models.IntegerField('投入袋數', null=True, blank=True)
    required_weight_kg = models.DecimalField('需求重量(kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    measured_weight_kg = models.DecimalField('生豆量測重量(kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    manual_input_weight_kg = models.DecimalField('手動投入重量(kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # 時間資訊
    work_start_time = models.DateTimeField('作業開始時間', null=True, blank=True)
    work_end_time = models.DateTimeField('作業結束時間', null=True, blank=True)
    work_duration = models.CharField('作業時間', max_length=20, blank=True)
    
    # 其他
    ico_code = models.CharField('ICO', max_length=50, blank=True)
    remark = models.TextField('備註', blank=True)
    
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return f"{self.order_number} - {self.green_bean_name}"


class RawMaterialWarehouseRecord(models.Model):
    """原料倉進出記錄"""
    class Meta:
        db_table = 'app_raw_material_warehouse_record'
        verbose_name = '原料倉進出記錄'
        verbose_name_plural = '原料倉進出記錄'
        ordering = ['-created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 基本資訊
    product_code = models.CharField('品號', max_length=50, blank=True)
    product_name = models.CharField('品名', max_length=100, blank=True)
    factory_batch_number = models.CharField('工廠批號', max_length=100, blank=True)
    international_batch_number = models.CharField('國際批號', max_length=100, blank=True)
    
    # 重量資訊
    standard_weight_kg = models.DecimalField('標準重(kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # 庫存資訊
    previous_month_inventory = models.DecimalField('上月庫存', max_digits=10, decimal_places=2, null=True, blank=True)
    incoming_stock = models.DecimalField('進貨', max_digits=10, decimal_places=2, null=True, blank=True)
    outgoing_stock = models.DecimalField('領用', max_digits=10, decimal_places=2, null=True, blank=True)
    current_inventory = models.DecimalField('當前庫存', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # 待處理數量
    pending_processing = models.DecimalField('待處理', max_digits=10, decimal_places=2, null=True, blank=True)
    opened_quality_external_remaining = models.DecimalField('開袋+品管+外賣剩下', max_digits=10, decimal_places=2, null=True, blank=True)
    external_sales = models.DecimalField('外賣', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # 時間記錄
    record_date = models.DateField('記錄日期', null=True, blank=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return f"{self.product_code} - {self.product_name}"


class RawMaterialMonthlySummary(models.Model):
    """原料月度統計摘要"""
    class Meta:
        db_table = 'app_raw_material_monthly_summary'
        verbose_name = '原料月度統計'
        verbose_name_plural = '原料月度統計'
        ordering = ['-year', '-month']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.IntegerField('年度')
    month = models.IntegerField('月份')
    
    # 統計資訊
    total_inventory_value = models.DecimalField('總庫存價值', max_digits=15, decimal_places=2, null=True, blank=True)
    total_incoming_stock = models.DecimalField('總進貨量', max_digits=12, decimal_places=2, null=True, blank=True)
    total_outgoing_stock = models.DecimalField('總出貨量', max_digits=12, decimal_places=2, null=True, blank=True)
    total_current_inventory = models.DecimalField('總當前庫存', max_digits=12, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    def __str__(self):
        return f"{self.year}年{self.month}月統計"


# 檔案上傳記錄模型
class FileUploadRecordQuerySet(models.QuerySet):
    """自定義查詢集，支援批量刪除相關記錄"""
    
    def delete(self):
        """批量刪除時也刪除相關記錄"""
        from django.db import transaction
        
        with transaction.atomic():
            from app.models import UploadRecordRelation, GreenBeanInboundRecord
            
            deleted_records = 0
            
            # 對每個上傳記錄刪除相關記錄
            for upload_record in self:
                relations = UploadRecordRelation.objects.filter(upload_record=upload_record)
                
                for relation in relations:
                    try:
                        if relation.content_type == 'green_bean':
                            record = GreenBeanInboundRecord.objects.get(id=relation.object_id)
                            record.delete()
                            deleted_records += 1
                    except GreenBeanInboundRecord.DoesNotExist:
                        pass
                
                # 刪除關聯記錄
                relations.delete()
                
                # 如果還有 created_record_ids 中的記錄，也一併刪除
                if upload_record.created_record_ids:
                    for record_id in upload_record.created_record_ids:
                        try:
                            record = GreenBeanInboundRecord.objects.get(id=record_id)
                            record.delete()
                            deleted_records += 1
                        except GreenBeanInboundRecord.DoesNotExist:
                            pass
            
            # 調用父類的批量刪除
            result = super().delete()
            
            # 檢查是否還有其他上傳記錄，如果沒有則清理所有孤立記錄
            remaining_upload_count = FileUploadRecord.objects.count()
            if remaining_upload_count == 0:
                # 沒有上傳記錄了，清理所有可能的孤立記錄
                orphaned_records = GreenBeanInboundRecord.objects.all()
                additional_deleted = orphaned_records.count()
                if additional_deleted > 0:
                    orphaned_records.delete()
                    
                # 清理所有關聯記錄
                all_relations = UploadRecordRelation.objects.filter(content_type='green_bean')
                if all_relations.exists():
                    all_relations.delete()
            
            return result


class FileUploadRecord(models.Model):
    """檔案上傳記錄"""
    class Meta:
        db_table = 'app_file_upload_record'
        verbose_name = '檔案上傳記錄'
        verbose_name_plural = '檔案上傳記錄'
        ordering = ['-upload_time']

    objects = FileUploadRecordQuerySet.as_manager()  # 使用自定義查詢集

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField('檔案名稱', max_length=255)
    file_hash = models.CharField('檔案雜湊值', max_length=64, unique=True)  # 用於檢查重複
    file_size = models.IntegerField('檔案大小（bytes）')
    upload_time = models.DateTimeField('上傳時間', auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='上傳者')
    file_type = models.CharField('檔案類型', max_length=50, choices=[
        ('green_bean', '生豆入庫記錄'),
        ('raw_material', '原料倉管理'),
        ('monthly_summary', '月度統計')
    ])
    records_count = models.IntegerField('記錄數量', default=0)
    status = models.CharField('處理狀態', max_length=20, choices=[
        ('pending', '處理中'),
        ('success', '成功'),
        ('failed', '失敗'),
        ('duplicate', '重複檔案')
    ], default='pending')
    error_message = models.TextField('錯誤訊息', blank=True, null=True)
    # 新增：用於還原功能的記錄ID列表
    created_record_ids = models.JSONField('創建的記錄ID列表', default=list, blank=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.get_status_display()}"
    
    def delete(self, using=None, keep_parents=False):
        """覆寫刪除方法，確保同時刪除相關記錄"""
        from django.db import transaction
        
        with transaction.atomic():
            # 刪除相關的生豆入庫記錄
            from app.models import UploadRecordRelation, GreenBeanInboundRecord
            
            relations = UploadRecordRelation.objects.filter(upload_record=self)
            deleted_records = 0
            
            for relation in relations:
                try:
                    if relation.content_type == 'green_bean':
                        record = GreenBeanInboundRecord.objects.get(id=relation.object_id)
                        record.delete()
                        deleted_records += 1
                except GreenBeanInboundRecord.DoesNotExist:
                    pass
            
            # 刪除關聯記錄
            relations.delete()
            
            # 如果還有 created_record_ids 中的記錄，也一併刪除
            if self.created_record_ids:
                for record_id in self.created_record_ids:
                    try:
                        record = GreenBeanInboundRecord.objects.get(id=record_id)
                        record.delete()
                        deleted_records += 1
                    except GreenBeanInboundRecord.DoesNotExist:
                        pass
            
            # 檢查是否為最後一個上傳記錄，如果是則清理所有孤立記錄
            remaining_upload_count = FileUploadRecord.objects.exclude(id=self.id).count()
            if remaining_upload_count == 0:
                # 這是最後一個上傳記錄，清理所有可能的孤立記錄
                orphaned_records = GreenBeanInboundRecord.objects.all()
                additional_deleted = orphaned_records.count()
                if additional_deleted > 0:
                    orphaned_records.delete()
                    
                # 清理所有關聯記錄
                all_relations = UploadRecordRelation.objects.filter(content_type='green_bean')
                if all_relations.exists():
                    all_relations.delete()
            
            # 調用父類的刪除方法
            return super().delete(using=using, keep_parents=keep_parents)


# 新增：用於追蹤上傳記錄與業務資料關聯的中間表
class UploadRecordRelation(models.Model):
    """上傳記錄與業務資料關聯表"""
    class Meta:
        db_table = 'app_upload_record_relation'
        verbose_name = '上傳記錄關聯'
        verbose_name_plural = '上傳記錄關聯'
        unique_together = ['upload_record', 'content_type', 'object_id']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    upload_record = models.ForeignKey(FileUploadRecord, on_delete=models.CASCADE, verbose_name='上傳記錄')
    content_type = models.CharField('資料類型', max_length=50, choices=[
        ('green_bean', '生豆入庫記錄'),
        ('raw_material', '原料倉管理'),
        ('monthly_summary', '月度統計')
    ])
    object_id = models.UUIDField('關聯記錄ID')
    created_at = models.DateTimeField('創建時間', auto_now_add=True)
    
    def __str__(self):
        return f"{self.upload_record.file_name} -> {self.content_type}:{self.object_id}"


class UserActivityLog(models.Model):
    """用戶活動記錄"""
    ACTION_CHOICES = [
        ('create', '新增'),
        ('update', '更新'),
        ('delete', '刪除'),
        ('upload', '上傳'),
        ('delete_upload_record', '刪除上傳記錄'),
        ('batch_delete', '批量刪除'),
        ('export', '匯出'),
        ('login', '登入'),
        ('logout', '登出'),
    ]
    
    class Meta:
        db_table = 'app_user_activity_log'
        verbose_name = '用戶活動記錄'
        verbose_name_plural = '用戶活動記錄'
        ordering = ['-created_at']
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用戶')
    action = models.CharField('操作類型', max_length=20, choices=ACTION_CHOICES)
    description = models.CharField('操作描述', max_length=255)
    
    # 關聯的對象（可選）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 額外信息
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.TextField('用戶代理', blank=True)
    details = models.JSONField('詳細信息', default=dict, blank=True)
    
    created_at = models.DateTimeField('創建時間', auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.description}"


# ERP 權限管理代理模型
class ERPGroup(Group):
    """ERP群組代理模型，用於在ERP section顯示群組管理"""
    class Meta:
        proxy = True
        verbose_name = '群組'
        verbose_name_plural = '群組管理'


class ERPPermission(Permission):
    """ERP權限代理模型，用於在ERP section顯示權限管理"""
    class Meta:
        proxy = True
        verbose_name = '權限'
        verbose_name_plural = '權限管理'
