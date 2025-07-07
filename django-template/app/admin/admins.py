from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from datetime import datetime

from app.models import AdminUser, User, GreenBeanInboundRecord, RawMaterialWarehouseRecord, RawMaterialMonthlySummary, FileUploadRecord, UploadRecordRelation
from app.utils.activity_logger import log_user_activity


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
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'date_joined', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('個人資訊'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('狀態'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        (_('重要日期'), {
            'fields': ('last_login', 'date_joined'),
        }),
        (_('系統資訊'), {
            'fields': ('id',),
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
    )
    
    # 移除權限管理相關功能


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    pass


# ERP 系統管理介面

@admin.register(GreenBeanInboundRecord)
class GreenBeanInboundRecordAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'green_bean_name', 'green_bean_code', 
        'required_weight_kg', 'measured_weight_kg', 'record_time', 'is_abnormal'
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
    
    # 隱藏新增按鈕
    def has_add_permission(self, request):
        """禁用新增功能"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """重定向列表頁面到自定義頁面"""
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/erp/green-bean-records/')
    
    def has_module_permission(self, request):
        """隱藏admin模組"""
        return False
    
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
    
    def response_change(self, request, obj):
        """自定義編輯後的返回行為"""
        # 如果來自我們的自定義頁面，直接返回
        if 'from_green_bean_records' in request.GET:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/erp/green-bean-records/')
        
        return super().response_change(request, obj)
    
    def response_add(self, request, obj, post_url_continue=None):
        """自定義新增後的返回行為"""
        # 如果來自我們的自定義頁面，直接返回
        if 'from_green_bean_records' in request.GET:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/erp/green-bean-records/')
        
        return super().response_add(request, obj, post_url_continue)
    
    def response_delete(self, request, obj_display, obj_id):
        """自定義刪除後的返回行為"""
        # 如果來自我們的自定義頁面，直接返回
        if 'from_green_bean_records' in request.GET:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/erp/green-bean-records/')
        
        return super().response_delete(request, obj_display, obj_id)
    
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
    list_display = ['file_name', 'file_type', 'upload_time', 'uploaded_by', 'records_count', 'status']
    list_filter = ['file_type', 'status', 'upload_time']
    search_fields = ['file_name', 'file_hash']
    readonly_fields = ['id', 'file_hash', 'upload_time', 'file_size']
    ordering = ['-upload_time']
    
    fieldsets = (
        ('檔案資訊', {
            'fields': ('file_name', 'file_type', 'file_size', 'file_hash')
        }),
        ('上傳資訊', {
            'fields': ('upload_time', 'uploaded_by', 'records_count')
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


# 權限管理已完全移除