from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django import forms
from datetime import datetime

from app.models import AdminUser, User, GreenBeanInboundRecord, RawMaterialWarehouseRecord, RawMaterialMonthlySummary, FileUploadRecord, UploadRecordRelation
from app.utils.activity_logger import log_user_activity
from app.utils.green_bean_utils import get_green_bean_names


class GreenBeanInboundRecordForm(forms.ModelForm):
    """自定義生豆入庫記錄表單"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 確保 green_bean_name 欄位存在
        if 'green_bean_name' in self.fields:
            # 獲取生豆名稱選項
            green_bean_names_list = get_green_bean_names()
            green_bean_choices = [('', '請選擇生豆名稱')] + [(name, name) for name in green_bean_names_list]
            
            # 設置欄位為 ChoiceField 而不是修改 widget
            self.fields['green_bean_name'] = forms.ChoiceField(
                choices=green_bean_choices,
                required=False,
                label='生豆名稱',
                help_text=f'共有 {len(green_bean_names_list)} 個生豆名稱可選擇',
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'style': 'width: 100%;'
                })
            )
        
    class Meta:
        model = GreenBeanInboundRecord
        fields = '__all__'


class CustomUserCreationForm(UserCreationForm):
    """自定義使用者創建表單"""
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")


class CustomUserChangeForm(UserChangeForm):
    """自定義使用者修改表單"""
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    '''自定義使用者管理界面'''
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'get_groups_display', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'groups', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'date_joined', 'last_login']
    filter_horizontal = ['groups', 'user_permissions']
    def has_module_permission(self, request):
        perms = [
            'auth.view_user', 'auth.add_user', 'auth.change_user', 'auth.delete_user'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)
    
    def get_groups_display(self, obj):
        """顯示使用者所屬群組"""
        groups = obj.groups.all()
        if groups:
            return ', '.join([group.name for group in groups])
        return '無群組'
    get_groups_display.short_description = '所屬群組'
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('個人資訊'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('狀態'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        (_('群組權限'), {
            'fields': ('groups',),
            'description': '透過群組分配權限是推薦的方式。選擇使用者應該屬於的群組。'
        }),
        (_('個別權限'), {
            'fields': ('user_permissions',),
            'description': '特定權限。通常建議使用群組而非個別權限。',
            'classes': ('collapse',)
        }),
        (_('重要日期'), {
            'fields': ('last_login', 'date_joined'),
        }),
        (_('系統資訊'), {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
        (_('狀態'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        (_('權限管理'), {
            'fields': ('groups', 'user_permissions'),
            'description': '建議優先使用群組分配權限'
        }),
    )


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    pass
    def has_module_permission(self, request):
        perms = [
            'app.view_adminuser', 'app.add_adminuser', 'app.change_adminuser', 'app.delete_adminuser'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)


# ERP 系統管理介面

@admin.register(GreenBeanInboundRecord)
class GreenBeanInboundRecordAdmin(admin.ModelAdmin):
    form = GreenBeanInboundRecordForm  # 使用自定義表單
    
    list_display = [
        'order_number', 'green_bean_name', 'green_bean_code', 
        'required_weight_kg', 'measured_weight_kg', 'record_time', 'is_abnormal',
        'get_upload_info'
    ]
    list_filter = [
        'is_abnormal', 'execution_status', 'green_bean_storage_silo',
        'record_time', 'work_start_time'
    ]
    search_fields = [
        'order_number', 'green_bean_name', 'green_bean_code',
        'green_bean_batch_number', 'ico_code'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'record_time'
    def has_module_permission(self, request):
        perms = [
            'app.view_greenbeaninboundrecord', 'app.add_greenbeaninboundrecord', 'app.change_greenbeaninboundrecord', 'app.delete_greenbeaninboundrecord'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)
    
    def get_upload_info(self, obj):
        """顯示上傳信息"""
        try:
            # 查找與此記錄相關的上傳記錄
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(obj)
            relation = UploadRecordRelation.objects.filter(
                content_type=content_type,
                object_id=obj.id
            ).select_related('upload_record').first()
            
            if relation:
                upload_record = relation.upload_record
                return format_html(
                    '<span title="上傳時間: {}"><i class="fas fa-file-excel"></i> {}</span>',
                    upload_record.upload_time.strftime('%Y-%m-%d %H:%M'),
                    upload_record.file_name[:20] + '...' if len(upload_record.file_name) > 20 else upload_record.file_name
                )
            else:
                return format_html('<span title="手動新增"><i class="fas fa-keyboard"></i> 手動</span>')
        except:
            return format_html('<span title="手動新增"><i class="fas fa-keyboard"></i> 手動</span>')
    
    get_upload_info.short_description = '數據來源'
    get_upload_info.admin_order_field = 'created_at'
    
    # 權限檢查
    def has_add_permission(self, request):
        """只有有 add 權限的用戶才能新增"""
        return request.user.is_superuser or request.user.has_perm('app.add_greenbeaninboundrecord')
    
    def has_change_permission(self, request, obj=None):
        """只有有 change 權限的用戶才能修改"""
        return request.user.is_superuser or request.user.has_perm('app.change_greenbeaninboundrecord')
    
    def has_delete_permission(self, request, obj=None):
        """只有有 delete 權限的用戶才能刪除"""
        return request.user.is_superuser or request.user.has_perm('app.delete_greenbeaninboundrecord')
    
    def changelist_view(self, request, extra_context=None):
        """自定義列表視圖，添加上傳功能的連結"""
        extra_context = extra_context or {}
        extra_context.update({
            'upload_url': '/erp/green-bean-records/upload/',
            'upload_records_url': '/erp/green-bean-records/uploads/',
            'show_upload_button': True,
            'custom_buttons': [
                {
                    'url': '/erp/green-bean-records/upload/',
                    'title': '上傳 Excel 檔案',
                    'icon': 'fas fa-upload',
                    'class': 'btn btn-success'
                },
                {
                    'url': '/admin/app/fileuploadrecord/',
                    'title': '查看上傳記錄',
                    'icon': 'fas fa-history',
                    'class': 'btn btn-info'
                }
            ]
        })
        return super().changelist_view(request, extra_context=extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """自定義編輯視圖，隱藏「儲存並繼續新增」按鈕"""
        extra_context = extra_context or {}
        extra_context['show_save_and_add_another'] = False
        return super().change_view(request, object_id, form_url, extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        """自定義新增視圖，隱藏「儲存並繼續新增」按鈕"""
        extra_context = extra_context or {}
        extra_context['show_save_and_add_another'] = False
        return super().add_view(request, form_url, extra_context)
    
    fieldsets = (
        ('基本資訊', {
            'fields': (
                'is_abnormal', 'record_time', 'order_number', 
                'roasted_item_sequence', 'green_bean_item_sequence',
                'batch_sequence', 'execution_status'
            )
        }),
        ('生豆資訊', {
            'fields': (
                'green_bean_batch_number', 'green_bean_code',
                'green_bean_name', 'green_bean_storage_silo'
            )
        }),
        ('重量和數量', {
            'fields': (
                'bag_weight_kg', 'input_bag_count', 'required_weight_kg',
                'measured_weight_kg', 'manual_input_weight_kg'
            )
        }),
        ('作業時間', {
            'fields': (
                'work_start_time', 'work_end_time', 'work_duration'
            )
        }),
        ('其他資訊', {
            'fields': ('ico_code', 'remark')
        }),
        ('系統資訊', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # 移除自定義返回邏輯，使用標準 Django Admin 行為
    
    def save_model(self, request, obj, form, change):
        """重寫保存模型方法以記錄活動"""
        # 獲取舊值（如果是編輯）
        old_values = {}
        if change and obj.pk:
            try:
                old_obj = GreenBeanInboundRecord.objects.get(pk=obj.pk)
                old_values = {
                    'order_number': old_obj.order_number,
                    'green_bean_name': old_obj.green_bean_name,
                    'green_bean_code': old_obj.green_bean_code,
                    'green_bean_batch_number': old_obj.green_bean_batch_number,
                    'required_weight_kg': float(old_obj.required_weight_kg) if old_obj.required_weight_kg else None,
                    'measured_weight_kg': float(old_obj.measured_weight_kg) if old_obj.measured_weight_kg else None,
                    'execution_status': old_obj.execution_status,
                    'is_abnormal': old_obj.is_abnormal,
                    'record_time': old_obj.record_time.isoformat() if old_obj.record_time else None,
                }
            except GreenBeanInboundRecord.DoesNotExist:
                pass
        
        # 保存物件
        super().save_model(request, obj, form, change)
        
        # 記錄活動
        if change:
            # 獲取新值
            new_values = {
                'order_number': obj.order_number,
                'green_bean_name': obj.green_bean_name,
                'green_bean_code': obj.green_bean_code,
                'green_bean_batch_number': obj.green_bean_batch_number,
                'required_weight_kg': float(obj.required_weight_kg) if obj.required_weight_kg else None,
                'measured_weight_kg': float(obj.measured_weight_kg) if obj.measured_weight_kg else None,
                'execution_status': obj.execution_status,
                'is_abnormal': obj.is_abnormal,
                'record_time': obj.record_time.isoformat() if obj.record_time else None,
            }
            
            # 找出變更的欄位
            changed_fields = []
            for key, new_value in new_values.items():
                old_value = old_values.get(key)
                if old_value != new_value:
                    changed_fields.append({
                        'field': key,
                        'old_value': old_value,
                        'new_value': new_value
                    })
            
            # 記錄編輯活動
            log_user_activity(
                request.user,
                'update',
                f'從管理後台編輯生豆入庫記錄: {obj.order_number} - {obj.green_bean_name}',
                content_object=obj,
                request=request,
                details={
                    'record_id': str(obj.id),
                    'changed_fields': changed_fields,
                    'old_values': old_values,
                    'new_values': new_values,
                    'update_time': datetime.now().isoformat(),
                    'update_source': 'admin_backend'
                }
            )
        else:
            # 記錄新增活動
            log_user_activity(
                request.user,
                'create',
                f'從管理後台新增生豆入庫記錄: {obj.order_number} - {obj.green_bean_name}',
                content_object=obj,
                request=request,
                details={
                    'record_id': str(obj.id),
                    'order_number': obj.order_number,
                    'green_bean_name': obj.green_bean_name,
                    'green_bean_code': obj.green_bean_code,
                    'creation_time': datetime.now().isoformat(),
                    'creation_source': 'admin_backend'
                }
            )

    def delete_model(self, request, obj):
        """重寫刪除模型方法以記錄活動"""
        # 保存記錄資訊用於記錄
        record_info = {
            'order_number': obj.order_number,
            'green_bean_name': obj.green_bean_name,
            'green_bean_code': obj.green_bean_code,
            'green_bean_batch_number': obj.green_bean_batch_number,
            'required_weight_kg': float(obj.required_weight_kg) if obj.required_weight_kg else None,
            'measured_weight_kg': float(obj.measured_weight_kg) if obj.measured_weight_kg else None,
            'execution_status': obj.execution_status,
            'is_abnormal': obj.is_abnormal,
        }
        
        # 記錄刪除活動（在刪除前記錄）
        log_user_activity(
            request.user,
            'delete',
            f'從管理後台刪除生豆入庫記錄: {obj.order_number} - {obj.green_bean_name}',
            content_object=obj,
            request=request,
            details={
                'record_id': str(obj.id),
                'deleted_record': record_info,
                'deletion_time': datetime.now().isoformat(),
                'deletion_source': 'admin_backend'
            }
        )
        
        # 執行刪除
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """重寫批量刪除方法以記錄活動"""
        # 記錄所有要被刪除的記錄
        deleted_records = []
        for obj in queryset:
            record_info = {
                'order_number': obj.order_number,
                'green_bean_name': obj.green_bean_name,
                'green_bean_code': obj.green_bean_code,
                'green_bean_batch_number': obj.green_bean_batch_number,
                'required_weight_kg': float(obj.required_weight_kg) if obj.required_weight_kg else None,
                'measured_weight_kg': float(obj.measured_weight_kg) if obj.measured_weight_kg else None,
                'execution_status': obj.execution_status,
                'is_abnormal': obj.is_abnormal,
            }
            deleted_records.append(record_info)
        
        # 記錄批量刪除活動
        log_user_activity(
            request.user,
            'batch_delete',
            f'從管理後台批量刪除 {len(deleted_records)} 筆生豆入庫記錄',
            request=request,
            details={
                'records_count': len(deleted_records),
                'deleted_records': deleted_records,
                'deletion_time': datetime.now().isoformat(),
                'deletion_source': 'admin_backend'
            }
        )
        
        # 執行批量刪除
        super().delete_queryset(request, queryset)


@admin.register(RawMaterialWarehouseRecord)
class RawMaterialWarehouseRecordAdmin(admin.ModelAdmin):
    list_display = [
        'product_code', 'product_name', 'factory_batch_number',
        'standard_weight_kg', 'current_inventory', 'record_date'
    ]
    list_filter = [
        'record_date', 'created_at'
    ]
    search_fields = [
        'product_code', 'product_name', 'factory_batch_number',
        'international_batch_number'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'record_date'
    def has_module_permission(self, request):
        perms = [
            'app.view_rawmaterialwarehouserecord', 'app.add_rawmaterialwarehouserecord', 'app.change_rawmaterialwarehouserecord', 'app.delete_rawmaterialwarehouserecord'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)
    
    def has_add_permission(self, request):
        """只有有 add 權限的用戶才能新增"""
        return request.user.is_superuser or request.user.has_perm('app.add_rawmaterialwarehouserecord')
    
    def has_change_permission(self, request, obj=None):
        """只有有 change 權限的用戶才能修改"""
        return request.user.is_superuser or request.user.has_perm('app.change_rawmaterialwarehouserecord')
    
    def has_delete_permission(self, request, obj=None):
        """只有有 delete 權限的用戶才能刪除"""
        return request.user.is_superuser or request.user.has_perm('app.delete_rawmaterialwarehouserecord')
    
    fieldsets = (
        ('基本資訊', {
            'fields': (
                'product_code', 'product_name', 'factory_batch_number',
                'international_batch_number', 'standard_weight_kg'
            )
        }),
        ('庫存資訊', {
            'fields': (
                'previous_month_inventory', 'incoming_stock',
                'outgoing_stock', 'current_inventory'
            )
        }),
        ('處理狀態', {
            'fields': (
                'pending_processing', 'opened_quality_external_remaining',
                'external_sales'
            )
        }),
        ('時間資訊', {
            'fields': ('record_date',)
        }),
        ('系統資訊', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(RawMaterialMonthlySummary)
class RawMaterialMonthlySummaryAdmin(admin.ModelAdmin):
    list_display = [
        'year', 'month', 'total_inventory_value',
        'total_incoming_stock', 'total_outgoing_stock',
        'total_current_inventory'
    ]
    list_filter = ['year', 'month']
    readonly_fields = ['id', 'created_at', 'updated_at']
    def has_module_permission(self, request):
        perms = [
            'app.view_rawmaterialmonthlysummary', 'app.add_rawmaterialmonthlysummary', 'app.change_rawmaterialmonthlysummary', 'app.delete_rawmaterialmonthlysummary'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)
    
    def has_add_permission(self, request):
        """只有有 add 權限的用戶才能新增"""
        return request.user.is_superuser or request.user.has_perm('app.add_rawmaterialmonthlysummary')
    
    def has_change_permission(self, request, obj=None):
        """只有有 change 權限的用戶才能修改"""
        return request.user.is_superuser or request.user.has_perm('app.change_rawmaterialmonthlysummary')
    
    def has_delete_permission(self, request, obj=None):
        """只有有 delete 權限的用戶才能刪除"""
        return request.user.is_superuser or request.user.has_perm('app.delete_rawmaterialmonthlysummary')
    
    fieldsets = (
        ('時間資訊', {
            'fields': ('year', 'month')
        }),
        ('統計資訊', {
            'fields': (
                'total_inventory_value', 'total_incoming_stock',
                'total_outgoing_stock', 'total_current_inventory'
            )
        }),
        ('系統資訊', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(FileUploadRecord)
class FileUploadRecordAdmin(admin.ModelAdmin):
    """檔案上傳記錄管理"""
    list_display = ['file_name', 'file_type', 'upload_time', 'uploaded_by', 'records_count', 'status', 'get_related_records_count']
    list_filter = ['file_type', 'status', 'upload_time']
    search_fields = ['file_name', 'file_hash']
    readonly_fields = ['id', 'file_hash', 'upload_time', 'file_size', 'get_related_records_count']
    ordering = ['-upload_time']
    actions = ['delete_with_related_records']
    def has_module_permission(self, request):
        perms = [
            'app.view_fileuploadrecord', 'app.add_fileuploadrecord', 'app.change_fileuploadrecord', 'app.delete_fileuploadrecord'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)
    
    def get_related_records_count(self, obj):
        """獲取相關記錄數量"""
        from django.utils.html import format_html
        relations = UploadRecordRelation.objects.filter(upload_record=obj)
        count = relations.count()
        if count > 0:
            return format_html(
                '<span style="color: #007cba; font-weight: bold;">{} 筆相關記錄</span>',
                count
            )
        return format_html('<span style="color: #6c757d;">無相關記錄</span>')
    
    get_related_records_count.short_description = '關聯記錄'
    get_related_records_count.admin_order_field = 'id'
    
    def delete_with_related_records(self, request, queryset):
        """批量刪除上傳記錄及其相關資料"""
        from django.db import transaction
        from app.utils.activity_logger import log_user_activity
        
        deleted_uploads = 0
        deleted_records = 0
        deleted_relations = 0
        
        with transaction.atomic():
            for upload_record in queryset:
                record_deleted_count = 0
                relation_deleted_count = 0
                deleted_record_ids = []
                
                # 通過 UploadRecordRelation 查找並刪除相關記錄
                relations = UploadRecordRelation.objects.filter(upload_record=upload_record)
                
                for relation in relations:
                    try:
                        if relation.content_type == 'green_bean':
                            record = GreenBeanInboundRecord.objects.get(id=relation.object_id)
                            deleted_record_ids.append(str(record.id))
                            record.delete()
                            record_deleted_count += 1
                    except GreenBeanInboundRecord.DoesNotExist:
                        pass
                
                # 刪除關聯記錄
                relation_deleted_count = relations.count()
                relations.delete()
                
                # 如果還有 created_record_ids 中的記錄，也一併刪除
                if upload_record.created_record_ids:
                    for record_id in upload_record.created_record_ids:
                        if str(record_id) not in deleted_record_ids:  # 避免重複刪除
                            try:
                                record = GreenBeanInboundRecord.objects.get(id=record_id)
                                record.delete()
                                record_deleted_count += 1
                                deleted_record_ids.append(str(record_id))
                            except GreenBeanInboundRecord.DoesNotExist:
                                pass
                
                # 清理可能存在的其他孤立關聯
                other_relations = UploadRecordRelation.objects.filter(
                    content_type='green_bean',
                    object_id__in=deleted_record_ids
                ).exclude(upload_record=upload_record)
                
                if other_relations.exists():
                    other_relations.delete()
                
                # 記錄活動
                log_user_activity(
                    request.user,
                    'admin_delete_upload_record',
                    f'在 Admin 中刪除上傳記錄: {upload_record.file_name}，刪除了 {record_deleted_count} 筆相關記錄',
                    request=request,
                    details={
                        'upload_id': str(upload_record.id),
                        'deleted_records': deleted_record_ids,
                        'deleted_count': record_deleted_count,
                        'relation_count': relation_deleted_count
                    }
                )
                
                deleted_uploads += 1
                deleted_records += record_deleted_count
                deleted_relations += relation_deleted_count
        
        # 刪除上傳記錄
        queryset.delete()
        
        # 檢查是否還有其他上傳記錄，如果沒有則清理所有孤立記錄
        remaining_upload_count = FileUploadRecord.objects.count()
        if remaining_upload_count == 0:
            # 沒有上傳記錄了，清理所有可能的孤立記錄
            orphaned_records = GreenBeanInboundRecord.objects.all()
            additional_deleted = orphaned_records.count()
            if additional_deleted > 0:
                orphaned_records.delete()
                deleted_records += additional_deleted
                
            # 清理所有關聯記錄
            all_relations = UploadRecordRelation.objects.filter(content_type='green_bean')
            additional_relations = all_relations.count()
            if additional_relations > 0:
                all_relations.delete()
                deleted_relations += additional_relations
        
        self.message_user(
            request,
            f'成功刪除 {deleted_uploads} 筆上傳記錄、{deleted_records} 筆生豆記錄和 {deleted_relations} 筆關聯記錄'
        )
    
    delete_with_related_records.short_description = '刪除選中的上傳記錄及相關資料'
    
    def delete_model(self, request, obj):
        """單個刪除時也刪除相關記錄"""
        from django.db import transaction
        from app.utils.activity_logger import log_user_activity
        
        deleted_records = 0
        deleted_relations = 0
        deleted_record_ids = []
        
        with transaction.atomic():
            # 刪除相關的生豆入庫記錄
            relations = UploadRecordRelation.objects.filter(upload_record=obj)
            
            for relation in relations:
                try:
                    if relation.content_type == 'green_bean':
                        record = GreenBeanInboundRecord.objects.get(id=relation.object_id)
                        deleted_record_ids.append(str(record.id))
                        record.delete()
                        deleted_records += 1
                except GreenBeanInboundRecord.DoesNotExist:
                    pass
            
            # 刪除關聯記錄
            deleted_relations = relations.count()
            relations.delete()
            
            # 如果還有 created_record_ids 中的記錄，也一併刪除
            if obj.created_record_ids:
                for record_id in obj.created_record_ids:
                    if str(record_id) not in deleted_record_ids:  # 避免重複刪除
                        try:
                            record = GreenBeanInboundRecord.objects.get(id=record_id)
                            record.delete()
                            deleted_records += 1
                            deleted_record_ids.append(str(record_id))
                        except GreenBeanInboundRecord.DoesNotExist:
                            pass
            
            # 清理可能存在的其他孤立關聯
            other_relations = UploadRecordRelation.objects.filter(
                content_type='green_bean',
                object_id__in=deleted_record_ids
            ).exclude(upload_record=obj)
            
            if other_relations.exists():
                other_relations.delete()
            
            # 檢查是否為最後一個上傳記錄，如果是則清理所有孤立記錄
            remaining_upload_count = FileUploadRecord.objects.exclude(id=obj.id).count()
            if remaining_upload_count == 0:
                # 這是最後一個上傳記錄，清理所有可能的孤立記錄
                orphaned_records = GreenBeanInboundRecord.objects.all()
                additional_deleted = orphaned_records.count()
                if additional_deleted > 0:
                    orphaned_records.delete()
                    deleted_records += additional_deleted
                    
                # 清理所有關聯記錄
                all_relations = UploadRecordRelation.objects.filter(content_type='green_bean')
                additional_relations = all_relations.count()
                if additional_relations > 0:
                    all_relations.delete()
                    deleted_relations += additional_relations
            
            # 記錄活動
            log_user_activity(
                request.user,
                'admin_delete_upload_record',
                f'在 Admin 中刪除上傳記錄: {obj.file_name}，刪除了 {deleted_records} 筆生豆記錄，清理了 {deleted_relations} 筆關聯記錄',
                request=request,
                details={
                    'upload_id': str(obj.id),
                    'deleted_records': deleted_record_ids,
                    'deleted_count': deleted_records,
                    'relation_count': deleted_relations,
                    'is_last_upload': remaining_upload_count == 0
                }
            )
            
            # 刪除上傳記錄
            super().delete_model(request, obj)
    
    fieldsets = (
        ('檔案資訊', {
            'fields': ('file_name', 'file_type', 'file_size', 'file_hash')
        }),
        ('上傳資訊', {
            'fields': ('upload_time', 'uploaded_by', 'records_count', 'get_related_records_count')
        }),
        ('處理狀態', {
            'fields': ('status', 'error_message')
        }),
        ('系統資訊', {
            'fields': ('id',),
        }),
    )
    
    def has_add_permission(self, request):
        # 不允許手動添加，只能通過上傳功能創建
        return False


@admin.register(UploadRecordRelation)
class UploadRecordRelationAdmin(admin.ModelAdmin):
    '''上傳記錄關聯管理'''
    list_display = ['upload_record', 'content_type', 'object_id', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['upload_record__file_name', 'object_id']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('upload_record', 'content_type', 'object_id')
        }),
        ('系統資訊', {
            'fields': ('id', 'created_at'),
        }),
    )
    def has_module_permission(self, request):
        perms = [
            'app.view_uploadrecordrelation', 'app.add_uploadrecordrelation', 'app.change_uploadrecordrelation', 'app.delete_uploadrecordrelation'
        ]
        return request.user.is_superuser or all(request.user.has_perm(p) for p in perms)


# Django 預設權限管理系統

# 取消註冊預設的Group admin（如果已經註冊）
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# 只註冊原始的Group模型，不使用代理模型以避免衝突
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    """群組管理介面"""
    list_display = ['name', 'get_permissions_count', 'get_users_count']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    def has_module_permission(self, request):
        # 只有 superuser 才能看到群組管理模組
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        # 只有 superuser 才能查看群組
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        # 只有 superuser 才能新增群組
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # 只有 superuser 才能修改群組
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        # 只有 superuser 才能刪除群組
        return request.user.is_superuser
    
    def get_permissions_count(self, obj):
        """顯示權限數量"""
        return obj.permissions.count()
    get_permissions_count.short_description = '權限數量'
    
    def get_users_count(self, obj):
        """顯示群組內使用者數量"""
        return obj.user_set.count()
    get_users_count.short_description = '使用者數量'
    
    def changelist_view(self, request, extra_context=None):
        """自定義群組列表頁面，添加ERP權限管理中心的連結"""
        extra_context = extra_context or {}
        extra_context['erp_permissions_url'] = '/admin/erp/permissions/'
        extra_context['show_erp_link'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    class Media:
        css = {
            'all': ('admin/css/custom_group_admin.css',)
        }
        js = ('admin/js/custom_group_admin.js',)
    fieldsets = (
        ('基本資訊', {
            'fields': ('name',)
        }),
        ('權限設定', {
            'fields': ('permissions',),
            'description': '選擇此群組應該擁有的權限。使用右側的箭頭按鈕或按住 Ctrl 多選。'
        }),
    )
    



@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """原始權限管理介面"""
    list_display = ['name', 'content_type', 'codename', 'get_groups_count', 'get_users_count']
    list_filter = ['content_type__app_label', 'content_type']
    search_fields = ['name', 'codename', 'content_type__model']
    ordering = ['content_type__app_label', 'content_type__model', 'codename']
    readonly_fields = ['content_type', 'codename']
    def has_module_permission(self, request):
        # 只有 superuser 才能看到權限管理模組
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        # 只有 superuser 才能查看權限
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        # 只有 superuser 才能修改權限
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_groups_count(self, obj):
        """顯示使用此權限的群組數量"""
        return obj.group_set.count()
    get_groups_count.short_description = '群組數量'
    
    def get_users_count(self, obj):
        """顯示直接擁有此權限的使用者數量"""
        return obj.user_set.count()
    get_users_count.short_description = '使用者數量'
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'content_type', 'codename')
        }),
    )
    
