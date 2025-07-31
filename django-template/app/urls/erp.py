#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import path, include
from django.contrib import admin
from app.views.erp_views import (
    ERPDashboardView,
    ERPCleanDashboardView,
    green_bean_records_api,
    green_bean_names_api,
    raw_material_records_api,
    inventory_statistics_api,
    production_statistics_api,
    green_bean_records_view,
    green_bean_upload_page,
    green_bean_upload_file,
    add_green_bean_record,
    delete_green_bean_record,
    batch_delete_green_bean_records,
    delete_upload_record,
    get_upload_records,
    activity_log_view,
    add_activity_record,
    raw_material_upload_page,
    raw_material_upload_file,
    get_raw_material_upload_records,
    delete_raw_material_upload_record
)
from app.views.permission_views import permissions_redirect_view


app_name = 'erp'

urlpatterns = [
    # ERP 儀表板
    path('', ERPDashboardView.as_view(), name='dashboard'),
    path('dashboard/', ERPDashboardView.as_view(), name='dashboard_alt'),
    path('clean/', ERPCleanDashboardView.as_view(), name='clean_dashboard'),
    
    # 權限管理
    path('permissions/', permissions_redirect_view, name='permissions'),

    # 資料 API
    path('api/green-bean-records/', green_bean_records_api, name='green_bean_records_api'),
    path('api/green-bean-names/', green_bean_names_api, name='green_bean_names_api'),
    path('api/raw-material-records/', raw_material_records_api, name='raw_material_records_api'),
    path('api/inventory-statistics/', inventory_statistics_api, name='inventory_statistics_api'),
    path('api/production-statistics/', production_statistics_api, name='production_statistics_api'),
    
    # 生豆入庫記錄頁面
    path('green-bean-records/', green_bean_records_view, name='green_bean_records'),
    path('green-bean-records/add/', add_green_bean_record, name='add_green_bean_record'),
    path('green-bean-records/upload/', green_bean_upload_page, name='green_bean_upload_page'),
    path('green-bean-records/upload-file/', green_bean_upload_file, name='green_bean_upload_file'),
    path('green-bean-records/delete/<uuid:record_id>/', delete_green_bean_record, name='delete_green_bean_record'),
    path('green-bean-records/batch-delete/', batch_delete_green_bean_records, name='batch_delete_green_bean_records'),
    path('green-bean-records/upload/delete/<uuid:upload_id>/', delete_upload_record, name='delete_upload_record'),
    path('green-bean-records/uploads/', get_upload_records, name='get_upload_records'),
    
    # 原料倉管理頁面
    path('raw-material-records/upload/', raw_material_upload_page, name='raw_material_upload_page'),
    path('raw-material-records/upload-file/', raw_material_upload_file, name='raw_material_upload_file'),
    path('raw-material-records/uploads/', get_raw_material_upload_records, name='get_raw_material_upload_records'),
    path('raw-material-records/upload/delete/<uuid:upload_id>/', delete_raw_material_upload_record, name='delete_raw_material_upload_record'),
    
    path('activity-log/', activity_log_view, name='activity_log'),
    path('activity-log/add/', add_activity_record, name='add_activity_record'),
]
