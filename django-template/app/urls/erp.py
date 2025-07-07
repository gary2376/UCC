#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path
from app.views.erp_views import (
    ERPDashboardView,
    ERPCleanDashboardView,
    green_bean_records_api,
    raw_material_records_api,
    inventory_statistics_api,
    production_statistics_api,
    green_bean_records_view,
    green_bean_upload_file,
    add_green_bean_record,
    delete_green_bean_record,
    batch_delete_green_bean_records,
    delete_upload_record,
    get_upload_records,
    activity_log_view,
    add_activity_record
)
from app.views.permission_views import (
    permission_management_view,
    user_permissions_view,
    update_user_permissions,
    batch_update_permissions,
    get_user_permissions_api
)

app_name = 'erp'

urlpatterns = [
    # ERP 儀表板
    path('', ERPDashboardView.as_view(), name='dashboard'),
    path('dashboard/', ERPDashboardView.as_view(), name='dashboard_alt'),
    path('clean/', ERPCleanDashboardView.as_view(), name='clean_dashboard'),

    # 資料 API
    path('api/green-bean-records/', green_bean_records_api, name='green_bean_records_api'),
    path('api/raw-material-records/', raw_material_records_api, name='raw_material_records_api'),
    path('api/inventory-statistics/', inventory_statistics_api, name='inventory_statistics_api'),
    path('api/production-statistics/', production_statistics_api, name='production_statistics_api'),
    
    # 生豆入庫記錄頁面
    path('green-bean-records/', green_bean_records_view, name='green_bean_records'),
    path('green-bean-records/add/', add_green_bean_record, name='add_green_bean_record'),
    path('green-bean-records/upload/', green_bean_upload_file, name='green_bean_upload_file'),
    path('green-bean-records/delete/<uuid:record_id>/', delete_green_bean_record, name='delete_green_bean_record'),
    path('green-bean-records/batch-delete/', batch_delete_green_bean_records, name='batch_delete_green_bean_records'),
    path('green-bean-records/upload/delete/<uuid:upload_id>/', delete_upload_record, name='delete_upload_record'),
    path('green-bean-records/uploads/', get_upload_records, name='get_upload_records'),
    path('activity-log/', activity_log_view, name='activity_log'),
    path('activity-log/add/', add_activity_record, name='add_activity_record'),
    
    # 權限管理功能
    path('permissions/', permission_management_view, name='permission_management'),
    path('permissions/user/<uuid:user_id>/', user_permissions_view, name='user_permissions'),
    path('permissions/user/<uuid:user_id>/update/', update_user_permissions, name='update_user_permissions'),
    path('permissions/user/<uuid:user_id>/api/', get_user_permissions_api, name='get_user_permissions_api'),
    path('permissions/batch-update/', batch_update_permissions, name='batch_update_permissions'),
]
