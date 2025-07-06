#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta
import json
import hashlib
import pandas as pd
import os

from app.models.models import GreenBeanInboundRecord, RawMaterialWarehouseRecord, RawMaterialMonthlySummary, UserActivityLog, FileUploadRecord, UploadRecordRelation
from app.serializers.user_serializer import (
    GreenBeanInboundRecordSerializer,
    RawMaterialWarehouseRecordSerializer,
    RawMaterialMonthlySummarySerializer
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from app.utils.activity_logger import log_user_activity, get_recent_user_activities, get_important_user_activities
from django.db import transaction
from django.core.files.storage import default_storage


class ERPDashboardView(LoginRequiredMixin, View):
    """ERP 系統儀表板 - 只需要登入"""
    template_name = 'erp/dashboard.html'
    
    def get(self, request):
        # 統計數據
        stats = {
            'total_green_bean_records': GreenBeanInboundRecord.objects.count(),
            'total_raw_material_records': RawMaterialWarehouseRecord.objects.count(),
            'recent_abnormal_records': GreenBeanInboundRecord.objects.filter(is_abnormal=True).count(),
            'current_month_records': GreenBeanInboundRecord.objects.filter(
                record_time__month=datetime.now().month,
                record_time__year=datetime.now().year
            ).count()
        }
        
        # 最近的入庫記錄
        recent_records = GreenBeanInboundRecord.objects.order_by('-record_time')[:10]
        
        # 庫存警示（低庫存商品）
        low_inventory_threshold = 100  # 可以設定為設置項
        low_inventory_items = RawMaterialWarehouseRecord.objects.filter(
            current_inventory__lt=low_inventory_threshold,
            current_inventory__gt=0
        ).order_by('current_inventory')[:10]
        
        context = {
            'stats': stats,
            'recent_records': recent_records,
            'low_inventory_items': low_inventory_items,
        }
        
        return render(request, self.template_name, context)


class ERPCleanDashboardView(LoginRequiredMixin, View):
    """ERP 純淨儀表板 (無側邊選單) - 只需要登入"""
    template_name = 'erp/dashboard_clean.html'
    
    def get(self, request):
        # 不記錄查看儀表板的活動，因為用戶不想看到 view 操作
        
        # 統計數據
        stats = {
            'total_green_bean_records': GreenBeanInboundRecord.objects.count(),
            'total_raw_material_records': RawMaterialWarehouseRecord.objects.count(),
            'recent_abnormal_records': GreenBeanInboundRecord.objects.filter(is_abnormal=True).count(),
            'current_month_records': GreenBeanInboundRecord.objects.filter(
                record_time__month=datetime.now().month,
                record_time__year=datetime.now().year
            ).count()
        }
        
        # 最近的入庫記錄（顯示所有記錄，按時間排序）
        recent_records = GreenBeanInboundRecord.objects.order_by('-record_time')[:50]
        
        # 庫存警示（低庫存商品）
        low_inventory_threshold = 100  # 可以設定為設置項
        low_inventory_items = RawMaterialWarehouseRecord.objects.filter(
            current_inventory__lt=low_inventory_threshold,
            current_inventory__gt=0
        ).order_by('current_inventory')[:10]
        
        # 最近的重要用戶活動記錄（只顯示新增、更新、上傳等重要操作）
        recent_activities = get_important_user_activities(limit=20)
        
        # 獲取本週記錄統計
        from app.utils.activity_logger import get_weekly_records_comparison
        weekly_comparison = get_weekly_records_comparison()
        
        context = {
            'stats': stats,
            'recent_records': recent_records,
            'low_inventory_items': low_inventory_items,
            'recent_activities': recent_activities,
            'weekly_comparison': weekly_comparison,
        }
        
        return render(request, self.template_name, context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def green_bean_records_api(request):
    """生豆入庫記錄 API - 需要ERP查看權限"""
    try:
        # 查詢參數
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        search = request.GET.get('search', '')
        order_number = request.GET.get('order_number', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        is_abnormal = request.GET.get('is_abnormal', '')
        
        # 基本查詢
        queryset = GreenBeanInboundRecord.objects.all()
        
        # 應用過濾條件
        if search:
            queryset = queryset.filter(
                Q(green_bean_name__icontains=search) |
                Q(green_bean_code__icontains=search) |
                Q(order_number__icontains=search)
            )
        
        if order_number:
            queryset = queryset.filter(order_number__icontains=order_number)
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(record_time__gte=start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(record_time__lt=end_datetime)
        
        if is_abnormal:
            queryset = queryset.filter(is_abnormal=(is_abnormal.lower() == 'true'))
        
        # 排序
        queryset = queryset.order_by('-record_time')
        
        # 分頁
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化數據
        serializer = GreenBeanInboundRecordSerializer(page_obj.object_list, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def raw_material_records_api(request):
    """原料倉記錄 API - 需要ERP查看權限"""
    try:
        # 查詢參數
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        search = request.GET.get('search', '')
        product_code = request.GET.get('product_code', '')
        low_inventory = request.GET.get('low_inventory', '')
        
        # 基本查詢
        queryset = RawMaterialWarehouseRecord.objects.all()
        
        # 應用過濾條件
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(product_code__icontains=search) |
                Q(factory_batch_number__icontains=search)
            )
        
        if product_code:
            queryset = queryset.filter(product_code__icontains=product_code)
        
        if low_inventory:
            threshold = int(low_inventory)
            queryset = queryset.filter(
                current_inventory__lt=threshold,
                current_inventory__gt=0
            )
        
        # 排序
        queryset = queryset.order_by('-created_at')
        
        # 分頁
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化數據
        serializer = RawMaterialWarehouseRecordSerializer(page_obj.object_list, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_statistics_api(request):
    """庫存統計 API - 需要ERP查看權限"""
    try:
        # 總庫存統計
        total_stats = RawMaterialWarehouseRecord.objects.aggregate(
            total_inventory=Sum('current_inventory'),
            total_incoming=Sum('incoming_stock'),
            total_outgoing=Sum('outgoing_stock'),
            avg_inventory=Avg('current_inventory')
        )
        
        # 低庫存商品
        low_inventory_threshold = int(request.GET.get('threshold', 100))
        low_inventory_items = RawMaterialWarehouseRecord.objects.filter(
            current_inventory__lt=low_inventory_threshold,
            current_inventory__gt=0
        ).values('product_code', 'product_name', 'current_inventory').order_by('current_inventory')[:20]
        
        # 按產品類別統計
        product_stats = RawMaterialWarehouseRecord.objects.values('product_name').annotate(
            item_count=Count('id'),
            total_inventory=Sum('current_inventory'),
            avg_inventory=Avg('current_inventory')
        ).order_by('-total_inventory')[:10]
        
        return Response({
            'success': True,
            'data': {
                'total_stats': total_stats,
                'low_inventory_items': list(low_inventory_items),
                'product_stats': list(product_stats)
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def production_statistics_api(request):
    """生產統計 API - 需要ERP查看權限"""
    try:
        # 時間範圍
        days = int(request.GET.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        # 生產統計
        production_stats = GreenBeanInboundRecord.objects.filter(
            record_time__gte=start_date
        ).aggregate(
            total_records=Count('id'),
            total_weight=Sum('measured_weight_kg'),
            avg_weight=Avg('measured_weight_kg'),
            abnormal_count=Count('id', filter=Q(is_abnormal=True))
        )
        
        # 每日生產量
        daily_production = GreenBeanInboundRecord.objects.filter(
            record_time__gte=start_date
        ).extra(
            select={'day': 'DATE(record_time)'}
        ).values('day').annotate(
            daily_weight=Sum('measured_weight_kg'),
            daily_count=Count('id')
        ).order_by('day')
        
        # 按生豆類型統計
        bean_type_stats = GreenBeanInboundRecord.objects.filter(
            record_time__gte=start_date
        ).values('green_bean_name').annotate(
            total_weight=Sum('measured_weight_kg'),
            record_count=Count('id')
        ).order_by('-total_weight')[:10]
        
        return Response({
            'success': True,
            'data': {
                'production_stats': production_stats,
                'daily_production': list(daily_production),
                'bean_type_stats': list(bean_type_stats)
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@login_required
def green_bean_records_view(request):
    """生豆入庫記錄頁面視圖"""
    # 獲取所有記錄
    records = GreenBeanInboundRecord.objects.all().order_by('-record_time')
    
    # 分頁處理
    paginator = Paginator(records, 20)  # 每頁20條記錄
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 統計資料
    total_records = records.count()
    abnormal_records = records.filter(is_abnormal=True).count()
    current_month_records = records.filter(
        record_time__month=datetime.now().month,
        record_time__year=datetime.now().year
    ).count()
    
    # 最近上傳記錄
    recent_uploads = FileUploadRecord.objects.filter(
        file_type='green_bean'
    ).order_by('-upload_time')[:5]
    
    # 活動記錄統計
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # 活動記錄相關數據
    user_activities = UserActivityLog.objects.filter(
        content_type__model='greenbeaninboundrecord'
    ).select_related('user').order_by('-created_at')[:10]
    
    total_activities = UserActivityLog.objects.filter(
        content_type__model='greenbeaninboundrecord'
    ).count()
    
    # 活動統計
    activity_stats = {
        'creates': UserActivityLog.objects.filter(
            content_type__model='greenbeaninboundrecord', 
            action='create'
        ).count(),
        'updates': UserActivityLog.objects.filter(
            content_type__model='greenbeaninboundrecord', 
            action='update'
        ).count(),
        'deletes': UserActivityLog.objects.filter(
            content_type__model='greenbeaninboundrecord', 
            action='delete'
        ).count(),
        'uploads': UserActivityLog.objects.filter(
            content_type__model='greenbeaninboundrecord', 
            action='upload'
        ).count(),
    }
    
    # 獲取所有有活動記錄的使用者
    activity_users = User.objects.filter(
        id__in=UserActivityLog.objects.filter(
            content_type__model='greenbeaninboundrecord'
        ).values_list('user_id', flat=True).distinct()
    )
    
    context = {
        'page_obj': page_obj,
        'total_records': total_records,
        'abnormal_records': abnormal_records,
        'current_month_records': current_month_records,
        'recent_uploads': recent_uploads,
        'total_activities': total_activities,
        'user_activities': user_activities,
        'activity_stats': activity_stats,
        'activity_users': activity_users,
    }
    
    return render(request, 'erp/green_bean_records.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def green_bean_upload_file(request):
    """生豆入庫記錄檔案上傳處理"""
    try:
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            return JsonResponse({'success': False, 'message': '請選擇要上傳的檔案'})
        
        # 檢查檔案格式
        if not uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
            return JsonResponse({'success': False, 'message': '只支援 .xlsx 和 .xls 格式的檔案'})
        
        # 計算檔案雜湊值
        file_hash = calculate_file_hash(uploaded_file)
        
        # 檢查是否為重複檔案
        existing_file = FileUploadRecord.objects.filter(file_hash=file_hash).first()
        if existing_file:
            return JsonResponse({
                'success': False, 
                'message': f'此檔案已於 {existing_file.upload_time.strftime("%Y-%m-%d %H:%M")} 上傳過',
                'duplicate': True
            })
        
        # 使用事務處理檔案上傳
        with transaction.atomic():
            # 創建上傳記錄
            upload_record = FileUploadRecord.objects.create(
                file_name=uploaded_file.name,
                file_hash=file_hash,
                file_size=uploaded_file.size,
                uploaded_by=request.user,
                file_type='green_bean',
                status='pending'
            )
            
            try:
                # 處理Excel文件
                df = pd.read_excel(uploaded_file)
                
                print(f"原始欄位名稱: {df.columns.tolist()}")
                
                # 清理欄位名稱：移除換行符和空格
                df.columns = df.columns.str.replace('\n', '').str.strip()
                
                print(f"清理後欄位名稱: {df.columns.tolist()}")
                
                # 清理數據：移除完全空白的行
                df = df.dropna(how='all')
                
                # 清理數據：移除關鍵欄位都是空的行
                key_columns = ['單號', '生豆名稱', '生豆料號']
                df = df.dropna(subset=key_columns, how='all')
                
                print(f"清理後剩餘 {len(df)} 行數據")
                
                # 檢查必要欄位 - 根據實際Excel檔案調整
                required_columns = ['單號', '生豆名稱', '生豆料號']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    upload_record.status = 'failed'
                    upload_record.error_message = f'缺少必要欄位: {", ".join(missing_columns)}'
                    upload_record.save()
                    return JsonResponse({
                        'success': False, 
                        'message': f'檔案格式錯誤，缺少必要欄位: {", ".join(missing_columns)}'
                    })
                
                # 定義helper函數
                def safe_numeric(value, default=None):
                    if pd.isna(value) or str(value).strip() in ['', 'nan', 'None']:
                        return default
                    try:
                        result = pd.to_numeric(value, errors='coerce')
                        if pd.isna(result):
                            return default
                        return float(result)  # 確保返回數值類型
                    except:
                        return default
                
                def safe_string(value, default=''):
                    if pd.isna(value) or str(value).strip() in ['nan', 'None']:
                        return default
                    return str(value).strip()
                
                def safe_string_from_numeric(value, default=''):
                    """處理可能是數字的字符串欄位"""
                    if pd.isna(value) or str(value).strip() in ['nan', 'None']:
                        return default
                    # 如果是數字，轉換為整數字符串（去掉小數點）
                    try:
                        if isinstance(value, (int, float)):
                            return str(int(value))
                        return str(value).strip()
                    except:
                        return str(value).strip()
                
                def safe_integer(value, default=None):
                    """安全轉換為整數"""
                    if pd.isna(value) or str(value).strip() in ['', 'nan', 'None']:
                        return default
                    try:
                        result = pd.to_numeric(value, errors='coerce')
                        if pd.isna(result):
                            return default
                        return int(result)
                    except:
                        return default
                
                # 處理資料 - 根據實際Excel欄位對應
                created_records = []
                skipped_rows = 0
                
                for index, row in df.iterrows():
                    try:
                        # 檢查必要欄位是否為空或nan
                        order_number = str(row.get('單號', '')).strip()
                        green_bean_name = str(row.get('生豆名稱', '')).strip()
                        green_bean_code = safe_string_from_numeric(row.get('生豆料號', ''))
                        
                        print(f"處理第 {index + 1} 行: 單號='{order_number}', 生豆名稱='{green_bean_name}', 料號='{green_bean_code}'")
                        
                        # 跳過空行或nan資料
                        if (order_number in ['', 'nan', 'None'] or 
                            green_bean_name in ['', 'nan', 'None'] or 
                            green_bean_code in ['', 'nan', 'None']):
                            print(f"跳過第 {index + 1} 行：空白或無效資料")
                            skipped_rows += 1
                            continue
                        
                        # 處理日期時間欄位
                        record_time = None
                        if pd.notna(row.get('記錄時間')):
                            try:
                                record_time = pd.to_datetime(row.get('記錄時間'))
                            except:
                                record_time = datetime.now()
                        else:
                            record_time = datetime.now()
                        
                        work_start_time = None
                        if pd.notna(row.get('作業開始時間')):
                            try:
                                work_start_time = pd.to_datetime(row.get('作業開始時間'))
                            except:
                                work_start_time = None
                        
                        work_end_time = None
                        if pd.notna(row.get('作業結束時間')):
                            try:
                                work_end_time = pd.to_datetime(row.get('作業結束時間'))
                            except:
                                work_end_time = None
                        
                        # 建立記錄
                        record = GreenBeanInboundRecord.objects.create(
                            # 基本資訊
                            order_number=order_number,
                            roasted_item_sequence=safe_integer(row.get('炒豆項次')),
                            green_bean_item_sequence=safe_integer(row.get('生豆項次')),
                            batch_sequence=safe_integer(row.get('波次')),
                            execution_status=safe_string(row.get('執行狀態')),
                            
                            # 生豆資訊
                            green_bean_code=safe_string_from_numeric(row.get('生豆料號')),
                            green_bean_name=green_bean_name,
                            green_bean_batch_number=safe_string_from_numeric(row.get('生豆批號')),
                            green_bean_storage_silo=safe_string(row.get('生豆入庫筒倉')),
                            
                            # 重量和數量
                            bag_weight_kg=safe_numeric(row.get('一袋重量(kg)')),
                            input_bag_count=safe_integer(row.get('投入袋數')),
                            required_weight_kg=safe_numeric(row.get('需求重量(kg)')),
                            measured_weight_kg=safe_numeric(row.get('生豆量測重量(kg)')),
                            manual_input_weight_kg=safe_numeric(row.get('手動投入重量(kg)')),
                            
                            # 時間資訊
                            record_time=record_time,
                            work_start_time=work_start_time,
                            work_end_time=work_end_time,
                            work_duration=safe_string(row.get('作業時間')),
                            
                            # 其他
                            ico_code=safe_string(row.get('ICO')),
                            remark=safe_string(row.get('備註')),
                            is_abnormal=bool(row.get('異常') == 'Y') if pd.notna(row.get('異常')) else False
                        )
                        created_records.append(record)
                        print(f"成功創建記錄: {record.order_number} - {record.green_bean_name}")
                        
                        # 創建關聯記錄
                        UploadRecordRelation.objects.create(
                            upload_record=upload_record,
                            content_type='green_bean',
                            object_id=record.id
                        )
                        
                    except Exception as e:
                        print(f"處理第 {index + 1} 行時發生錯誤: {str(e)}")
                        continue
                
                print(f"總共處理了 {len(df)} 行，跳過了 {skipped_rows} 行，成功創建了 {len(created_records)} 筆記錄")
                
                # 更新上傳記錄狀態和創建的記錄ID
                upload_record.status = 'success'
                upload_record.records_count = len(created_records)
                upload_record.created_record_ids = [str(record.id) for record in created_records]
                upload_record.save()
                
                # 記錄用戶活動
                log_user_activity(
                    request.user,
                    'upload',
                    f'上傳生豆入庫記錄檔案: {uploaded_file.name}',
                    details={'records_count': len(created_records)}
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'檔案上傳成功！共處理了 {len(created_records)} 筆記錄',
                    'records_count': len(created_records)
                })
                
            except Exception as e:
                upload_record.status = 'failed'
                upload_record.error_message = str(e)
                upload_record.save()
                return JsonResponse({
                    'success': False,
                    'message': f'檔案處理失敗: {str(e)}'
                })
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'上傳過程中發生錯誤: {str(e)}'
        })


def calculate_file_hash(file):
    """計算檔案的MD5雜湊值"""
    hash_md5 = hashlib.md5()
    current_position = file.tell()
    file.seek(0)
    
    for chunk in file.chunks():
        hash_md5.update(chunk)
    
    file.seek(current_position)
    return hash_md5.hexdigest()


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def delete_green_bean_record(request, record_id):
    """刪除生豆入庫記錄"""
    try:
        record = get_object_or_404(GreenBeanInboundRecord, id=record_id)
        
        # 記錄刪除活動
        log_user_activity(
            request.user,
            'delete',
            f'刪除生豆入庫記錄: {record.order_number} - {record.green_bean_name}',
            details={'record_id': str(record_id)}
        )
        
        # 刪除記錄
        record.delete()
        
        return JsonResponse({
            'success': True,
            'message': '記錄已成功刪除'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'刪除記錄時發生錯誤: {str(e)}'
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def batch_delete_green_bean_records(request):
    """批量刪除生豆入庫記錄"""
    try:
        data = json.loads(request.body)
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return JsonResponse({
                'success': False,
                'message': '請選擇要刪除的記錄'
            })
        
        # 獲取要刪除的記錄
        records = GreenBeanInboundRecord.objects.filter(id__in=record_ids)
        deleted_count = records.count()
        
        # 記錄批量刪除活動
        log_user_activity(
            request.user,
            'delete',
            f'批量刪除生豆入庫記錄: {deleted_count} 筆',
            details={'record_ids': record_ids}
        )
        
        # 刪除記錄
        records.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'已成功刪除 {deleted_count} 筆記錄'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'批量刪除記錄時發生錯誤: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def delete_upload_record(request, upload_id):
    """刪除上傳記錄及相關的資料庫記錄"""
    try:
        # 獲取上傳記錄
        upload_record = get_object_or_404(FileUploadRecord, id=upload_id)
        
        # 檢查權限（可選：只有上傳者或管理員可以刪除）
        if upload_record.uploaded_by != request.user and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': '您沒有權限刪除此上傳記錄'
            }, status=403)
        
        # 使用事務確保資料一致性
        with transaction.atomic():
            # 刪除相關的生豆入庫記錄
            if upload_record.created_record_ids:
                deleted_count = 0
                for record_id in upload_record.created_record_ids:
                    try:
                        record = GreenBeanInboundRecord.objects.get(id=record_id)
                        record.delete()
                        deleted_count += 1
                    except GreenBeanInboundRecord.DoesNotExist:
                        # 記錄可能已經被刪除了，繼續處理
                        pass
                
                # 記錄用戶活動
                log_user_activity(
                    request.user,
                    'delete_upload_record',
                    f'刪除上傳記錄 {upload_record.file_name}，同時刪除了 {deleted_count} 筆相關記錄'
                )
            
            # 刪除上傳記錄
            file_name = upload_record.file_name
            upload_record.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'成功刪除上傳記錄 "{file_name}" 及相關資料'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'刪除上傳記錄時發生錯誤: {str(e)}'
        }, status=500)


@login_required
def get_upload_records(request):
    """獲取上傳記錄列表（用於AJAX刷新）"""
    try:
        recent_uploads = FileUploadRecord.objects.filter(
            file_type='green_bean'
        ).order_by('-upload_time')[:10]  # 只顯示最近10筆
        
        upload_data = []
        for upload in recent_uploads:
            upload_data.append({
                'id': str(upload.id),
                'file_name': upload.file_name,
                'upload_time': upload.upload_time.strftime('%Y-%m-%d %H:%M'),
                'records_count': upload.records_count,
                'status': upload.status,
                'status_display': upload.get_status_display(),
                'can_delete': upload.uploaded_by == request.user or request.user.is_superuser
            })
        
        return JsonResponse({
            'success': True,
            'uploads': upload_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'獲取上傳記錄時發生錯誤: {str(e)}'
        }, status=500)


@login_required
def test_return_view(request):
    """測試返回頁面"""
    return JsonResponse({
        'success': True,
        'message': '返回功能正常',
        'referer': request.META.get('HTTP_REFERER', ''),
        'get_params': dict(request.GET)
    })


@login_required
@require_http_methods(["GET"])
def get_user_activities(request):
    """獲取使用者活動記錄（AJAX）"""
    try:
        # 獲取篩選參數
        user_id = request.GET.get('user')
        action_type = request.GET.get('type')
        date_range = request.GET.get('date')
        page = int(request.GET.get('page', 1))
        
        # 基礎查詢
        activities = UserActivityLog.objects.filter(
            content_type__model='greenbeaninboundrecord'
        ).select_related('user')
        
        # 應用篩選
        if user_id:
            activities = activities.filter(user_id=user_id)
        
        if action_type:
            activities = activities.filter(action=action_type)
        
        if date_range:
            now = datetime.now()
            if date_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                activities = activities.filter(created_at__gte=start_date)
            elif date_range == 'week':
                start_date = now - timedelta(days=7)
                activities = activities.filter(created_at__gte=start_date)
            elif date_range == 'month':
                start_date = now - timedelta(days=30)
                activities = activities.filter(created_at__gte=start_date)
        
        # 排序和分頁
        activities = activities.order_by('-created_at')
        paginator = Paginator(activities, 10)
        page_obj = paginator.get_page(page)
        
        # 生成HTML
        activities_html = []
        for activity in page_obj:
            icon_map = {
                'create': 'fa-plus',
                'update': 'fa-edit', 
                'delete': 'fa-trash',
                'upload': 'fa-upload'
            }
            
            title_map = {
                'create': '新增記錄',
                'update': '編輯記錄',
                'delete': '刪除記錄', 
                'upload': '上傳檔案'
            }
            
            icon = icon_map.get(activity.action, 'fa-info')
            title = title_map.get(activity.action, activity.action.title())
            
            activity_html = f'''
            <div class="activity-card {activity.action}">
                <div class="d-flex">
                    <div class="activity-icon {activity.action}">
                        <i class="fas {icon}"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">{title}</div>
                        <div class="activity-description">{activity.description or "執行了相關操作"}</div>
                        <div class="activity-meta">
                            <i class="fas fa-user me-1"></i>
                            {activity.user.get_full_name() or activity.user.username}
                            <i class="fas fa-clock ms-3 me-1"></i>
                            {activity.created_at.strftime("%Y-%m-%d %H:%M:%S")}
                            {f'<i class="fas fa-globe ms-3 me-1"></i>{activity.ip_address}' if activity.ip_address else ''}
                        </div>
                    </div>
                </div>
            </div>
            '''
            activities_html.append(activity_html)
        
        if not activities_html:
            activities_html = ['''
                <div class="text-center py-5">
                    <i class="fas fa-clock fa-3x text-muted mb-3"></i>
                    <p class="text-muted">沒有找到符合條件的活動記錄</p>
                </div>
            ''']
        
        return JsonResponse({
            'success': True,
            'html': ''.join(activities_html),
            'has_more': page_obj.has_next(),
            'current_page': page,
            'total_pages': paginator.num_pages
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'載入活動記錄時發生錯誤: {str(e)}'
        })