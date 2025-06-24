#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path
from app.views.erp_views import (
    ERPDashboardView,
    ERPCleanDashboardView,
    green_bean_records_api,
    raw_material_records_api,
    inventory_statistics_api,
    production_statistics_api
)
from app.views.file_upload_views import (
    file_upload_view,
    upload_history_view,
    delete_upload_record,
    batch_delete_upload_records,
    clear_all_upload_records
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

    # 檔案上傳功能
    path('upload/', file_upload_view, name='file_upload'),
    path('upload/history/', upload_history_view, name='upload_history'),
    path('upload/delete/<uuid:upload_id>/', delete_upload_record, name='delete_upload_record'),
    path('upload/batch-delete/', batch_delete_upload_records, name='batch_delete_upload_records'),
    path('upload/clear-all/', clear_all_upload_records, name='clear_all_upload_records'),
    
    # 權限管理功能
    path('permissions/', permission_management_view, name='permission_management'),
    path('permissions/user/<uuid:user_id>/', user_permissions_view, name='user_permissions'),
    path('permissions/user/<uuid:user_id>/update/', update_user_permissions, name='update_user_permissions'),
    path('permissions/user/<uuid:user_id>/api/', get_user_permissions_api, name='get_user_permissions_api'),
    path('permissions/batch-update/', batch_update_permissions, name='batch_update_permissions'),
]
