#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import hashlib
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from app.models.models import (
    FileUploadRecord, 
    GreenBeanInboundRecord, 
    RawMaterialWarehouseRecord, 
    RawMaterialMonthlySummary,
    UploadRecordRelation
)


def calculate_file_hash(file):
    """計算檔案的MD5雜湊值"""
    hash_md5 = hashlib.md5()
    # 保存當前檔案指針位置
    current_position = file.tell()
    # 重置檔案指針到開頭
    file.seek(0)
    
    for chunk in file.chunks():
        hash_md5.update(chunk)
    
    # 恢復檔案指針到原來的位置（通常是開頭）
    file.seek(current_position)
    return hash_md5.hexdigest()


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def file_upload_view(request):
    """檔案上傳頁面和處理（純淨模式，無左側選單）- 只需要登入"""
    if request.method == 'GET':
        # 獲取最近的上傳記錄
        recent_uploads = FileUploadRecord.objects.all()[:10]
        context = {
            'recent_uploads': recent_uploads,
        }
        return render(request, 'erp/file_upload_clean.html', context)
    
    elif request.method == 'POST':
        return handle_file_upload(request)


def handle_file_upload(request):
    """處理檔案上傳"""
    try:
        print("=== 開始處理檔案上傳 ===")
        uploaded_file = request.FILES.get('file')
        file_type = request.POST.get('file_type')
        
        print(f"上傳檔案: {uploaded_file.name if uploaded_file else 'None'}")
        print(f"檔案類型: {file_type}")
        
        if not uploaded_file:
            print("錯誤: 沒有檔案")
            return JsonResponse({'success': False, 'message': '請選擇要上傳的檔案'})
        
        if not file_type:
            print("錯誤: 沒有檔案類型")
            return JsonResponse({'success': False, 'message': '請選擇檔案類型'})
        
        # 檢查檔案格式
        if not uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
            print("錯誤: 檔案格式不支援")
            return JsonResponse({'success': False, 'message': '只支援 .xlsx 和 .xls 格式的檔案'})
        
        print("開始計算檔案雜湊值...")
        # 計算檔案雜湊值
        file_hash = calculate_file_hash(uploaded_file)
        print(f"檔案雜湊值: {file_hash}")
        
        # 檢查是否為重複檔案
        existing_file = FileUploadRecord.objects.filter(file_hash=file_hash).first()
        if existing_file:
            print(f"發現重複檔案: {existing_file.file_name}")
            return JsonResponse({
                'success': False, 
                'message': f'此檔案已於 {existing_file.upload_time.strftime("%Y-%m-%d %H:%M")} 上傳過',
                'duplicate': True,
                'existing_file': {
                    'name': existing_file.file_name,
                    'upload_time': existing_file.upload_time.strftime("%Y-%m-%d %H:%M"),
                    'records_count': existing_file.records_count
                }
            })
        
        print("創建檔案上傳記錄...")
        # 創建檔案上傳記錄
        upload_record = FileUploadRecord.objects.create(
            file_name=uploaded_file.name,
            file_hash=file_hash,
            file_size=uploaded_file.size,
            file_type=file_type,
            uploaded_by=request.user if request.user.is_authenticated else None,
            status='pending'
        )
        print(f"上傳記錄ID: {upload_record.id}")
        
        print("開始處理檔案內容...")
        # 處理檔案內容
        success, message, records_count = process_uploaded_file(uploaded_file, file_type, upload_record)
        print(f"處理結果: success={success}, message={message}, records_count={records_count}")
        
        # 更新上傳記錄
        if success:
            upload_record.status = 'success'
            upload_record.records_count = records_count
        else:
            upload_record.status = 'failed'
            upload_record.error_message = message
        
        upload_record.save()
        print("=== 檔案上傳處理完成 ===")
        
        return JsonResponse({
            'success': success,
            'message': message,
            'records_count': records_count if success else 0,
            'upload_id': str(upload_record.id)
        })
        
    except Exception as e:
        print(f"檔案上傳異常: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'上傳失敗：{str(e)}'})


def process_uploaded_file(uploaded_file, file_type, upload_record):
    """處理上傳的Excel檔案"""
    try:
        print(f"--- 處理檔案: {uploaded_file.name}, 類型: {file_type} ---")
        # 確保檔案指針在開頭
        uploaded_file.seek(0)
        print(f"檔案指針位置重置到: {uploaded_file.tell()}")
        
        # 讀取Excel檔案
        df = pd.read_excel(uploaded_file)
        print(f"成功讀取Excel，資料形狀: {df.shape}")
        
        if df.empty:
            return False, "檔案內容為空", 0
        
        # 調試：顯示檔案資訊
        total_rows = len(df)
        print(f"檔案總行數: {total_rows}")
        print(f"檔案欄位: {list(df.columns)}")
        
        records_count = 0
        
        with transaction.atomic():
            if file_type == 'green_bean':
                records_count = process_green_bean_records(df, upload_record)
            elif file_type == 'raw_material':
                records_count = process_raw_material_records(df, upload_record)
            elif file_type == 'monthly_summary':
                records_count = process_monthly_summary_records(df, upload_record)
            else:
                return False, "不支援的檔案類型", 0
        
        # 調試：顯示處理結果
        print(f"成功處理 {records_count} 筆記錄，總共 {total_rows} 行")
        
        return True, f"成功處理 {records_count} 筆記錄（共 {total_rows} 行資料）", records_count
        
    except Exception as e:
        print(f"檔案處理錯誤: {str(e)}")
        return False, f"檔案處理錯誤：{str(e)}", 0


def process_green_bean_records(df, upload_record):
    """處理生豆入庫記錄"""
    records_count = 0
    error_count = 0
    skip_count = 0
    
    print(f"開始處理生豆入庫記錄，共 {len(df)} 行")
    print(f"檔案欄位: {list(df.columns)}")
    
    # 定義欄位映射（根據您的實際Excel欄位調整）
    column_mapping = {
        '記錄時間': 'record_time',
        '記錄日期': 'record_time',
        '時間': 'record_time',
        '日期': 'record_time',
        '單號': 'order_number',
        '訂單號': 'order_number',
        '生豆名稱': 'green_bean_name',
        '咖啡豆名稱': 'green_bean_name',
        '測量重量': 'measured_weight_kg',
        '重量': 'measured_weight_kg',
        '重量(kg)': 'measured_weight_kg',
        '是否異常': 'is_abnormal',
        '異常': 'is_abnormal',
    }
    
    for index, row in df.iterrows():
        try:
            # 準備資料
            record_data = {}
            
            # 處理記錄時間
            time_found = False
            for time_col in ['記錄時間', '記錄日期', '時間', '日期']:
                if time_col in df.columns:
                    time_value = row[time_col]
                    if pd.notna(time_value):
                        try:
                            if isinstance(time_value, str):
                                record_data['record_time'] = pd.to_datetime(time_value)
                            else:
                                record_data['record_time'] = time_value
                            time_found = True
                            break
                        except:
                            continue
            
            # 如果沒有找到時間欄位，使用當前時間
            if not time_found:
                from datetime import datetime
                record_data['record_time'] = datetime.now()
            
            # 處理其他欄位
            for excel_col, model_field in column_mapping.items():
                if excel_col in df.columns and model_field != 'record_time':
                    value = row[excel_col]
                    if pd.notna(value):
                        if model_field == 'is_abnormal':
                            # 處理布林值
                            record_data[model_field] = str(value).lower() in ['true', '是', '異常', '1', 'yes']
                        elif model_field == 'measured_weight_kg':
                            # 處理數值
                            try:
                                record_data[model_field] = float(value)
                            except:
                                record_data[model_field] = None
                        else:
                            record_data[model_field] = str(value).strip()
            
            # 檢查是否有任何有用的資料
            has_useful_data = False
            for key, value in record_data.items():
                if key != 'record_time' and value is not None and str(value).strip():
                    has_useful_data = True
                    break
            
            if not has_useful_data:
                skip_count += 1
                print(f"第 {index + 1} 行: 跳過空行或無有效資料")
                continue
            
            # 創建新記錄並記錄關聯
            try:
                # 直接創建新記錄，不檢查重複
                new_record = GreenBeanInboundRecord.objects.create(**record_data)
                
                # 創建關聯記錄
                UploadRecordRelation.objects.create(
                    upload_record=upload_record,
                    content_type='green_bean',
                    object_id=new_record.id
                )
                
                print(f"第 {index + 1} 行: 創建新記錄 - {record_data.get('order_number', '無訂單號')} / {record_data.get('green_bean_name', '無名稱')}")
                records_count += 1
                
            except Exception as create_error:
                error_count += 1
                print(f"第 {index + 1} 行創建記錄失敗: {create_error}")
                print(f"資料內容: {record_data}")
                
        except Exception as e:
            error_count += 1
            print(f"處理第 {index + 1} 行時發生錯誤: {e}")
            continue
    
    print(f"處理完成: 成功 {records_count} 筆，錯誤 {error_count} 筆，跳過 {skip_count} 筆")
    return records_count


def process_raw_material_records(df, upload_record):
    """處理原料倉管理記錄"""
    records_count = 0
    error_count = 0
    skip_count = 0
    
    print(f"開始處理原料倉管理記錄，共 {len(df)} 行")
    print(f"檔案原始欄位: {list(df.columns)}")
    
    # 根據Excel截圖，直接使用欄位位置來處理資料
    # A欄: 工廠批號, B欄: 國際批號, C欄: 公斤(標準重), D欄: 9月庫存, E欄: 進貨, F欄: 領用...
    
    for index, row in df.iterrows():
        try:
            record_data = {}
            
            # 設定記錄日期為今天
            from datetime import date
            record_data['record_date'] = date.today()
            
            print(f"\n第 {index + 1} 行原始資料:")
            for i, (col_name, value) in enumerate(row.items()):
                if i < 10:  # 只顯示前10個欄位
                    print(f"  欄位{i} '{col_name}': {value}")
            
            # 根據欄位位置提取資料（基於Excel截圖）
            row_values = row.values
            
            # A欄 (index 0): 工廠批號 - 作為product_code和product_name
            if len(row_values) > 0 and pd.notna(row_values[0]) and str(row_values[0]).strip():
                product_code = str(row_values[0]).strip()
                record_data['product_code'] = product_code
                record_data['product_name'] = product_code  # 暫時用工廠批號作為品名
                print(f"  設定品號/品名: {product_code}")
            
            # B欄 (index 1): 國際批號
            if len(row_values) > 1 and pd.notna(row_values[1]) and str(row_values[1]).strip():
                record_data['international_batch_number'] = str(row_values[1]).strip()
                print(f"  設定國際批號: {record_data['international_batch_number']}")
            
            # C欄 (index 2): 公斤(標準重)
            if len(row_values) > 2 and pd.notna(row_values[2]):
                try:
                    weight = float(row_values[2])
                    record_data['standard_weight_kg'] = weight
                    print(f"  設定標準重: {weight} kg")
                except:
                    print(f"  標準重轉換失敗: {row_values[2]}")
            
            # D欄 (index 3): 9月庫存 - 可作為上月庫存
            if len(row_values) > 3 and pd.notna(row_values[3]):
                try:
                    prev_inventory = float(row_values[3])
                    record_data['previous_month_inventory'] = prev_inventory
                    print(f"  設定上月庫存: {prev_inventory}")
                except:
                    print(f"  上月庫存轉換失敗: {row_values[3]}")
            
            # E欄 (index 4): 進貨
            if len(row_values) > 4 and pd.notna(row_values[4]):
                try:
                    incoming = float(row_values[4])
                    record_data['incoming_stock'] = incoming
                    print(f"  設定進貨: {incoming}")
                except:
                    print(f"  進貨轉換失敗: {row_values[4]}")
            
            # F欄 (index 5): 領用
            if len(row_values) > 5 and pd.notna(row_values[5]):
                try:
                    outgoing = float(row_values[5])
                    record_data['outgoing_stock'] = outgoing
                    print(f"  設定領用: {outgoing}")
                except:
                    print(f"  領用轉換失敗: {row_values[5]}")
            
            # G欄 (index 6): 7月*日庫存 - 可作為當前庫存
            if len(row_values) > 6 and pd.notna(row_values[6]):
                try:
                    current = float(row_values[6])
                    record_data['current_inventory'] = current
                    print(f"  設定當前庫存: {current}")
                except:
                    print(f"  當前庫存轉換失敗: {row_values[6]}")
            
            # 檢查是否有任何有用的資料
            has_useful_data = False
            for key, value in record_data.items():
                if key != 'record_date' and value is not None and str(value).strip() != '' and str(value) != '0.0':
                    has_useful_data = True
                    break
            
            if not has_useful_data:
                skip_count += 1
                print(f"第 {index + 1} 行: 跳過空行或無有效資料")
                continue
            
            # 創建新記錄並記錄關聯
            try:
                print(f"第 {index + 1} 行: 準備創建記錄，最終資料: {record_data}")
                
                # 直接創建新記錄，不檢查重複
                new_record = RawMaterialWarehouseRecord.objects.create(**record_data)
                
                # 創建關聯記錄
                UploadRecordRelation.objects.create(
                    upload_record=upload_record,
                    content_type='raw_material',
                    object_id=new_record.id
                )
                
                print(f"第 {index + 1} 行: ✅ 創建成功 - {record_data.get('product_name', '無品名')} (ID: {new_record.id})")
                records_count += 1
                
            except Exception as create_error:
                error_count += 1
                print(f"第 {index + 1} 行: ❌ 創建記錄失敗: {create_error}")
                print(f"資料內容: {record_data}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            error_count += 1
            print(f"第 {index + 1} 行: ❌ 處理時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n原料倉處理完成: ✅成功 {records_count} 筆，❌錯誤 {error_count} 筆，⏭️跳過 {skip_count} 筆")
    return records_count


def process_monthly_summary_records(df, upload_record):
    """處理月度統計記錄"""
    records_count = 0
    
    # 定義欄位映射
    column_mapping = {
        '年月': 'year_month',
        '統計月份': 'year_month',
        '品名': 'product_name',
        '商品名稱': 'product_name',
        '總進貨': 'total_incoming',
        '進貨總計': 'total_incoming',
        '總出貨': 'total_outgoing',
        '出貨總計': 'total_outgoing',
        '期末庫存': 'ending_inventory',
        '月末庫存': 'ending_inventory',
    }
    
    for index, row in df.iterrows():
        try:
            record_data = {}
            
            # 處理其他欄位
            for excel_col, model_field in column_mapping.items():
                if excel_col in df.columns:
                    value = row[excel_col]
                    if pd.notna(value):
                        if model_field in ['total_incoming', 'total_outgoing', 'ending_inventory']:
                            try:
                                record_data[model_field] = float(value)
                            except:
                                record_data[model_field] = 0.0
                        else:
                            record_data[model_field] = str(value)
            
            # 檢查必要欄位
            if 'product_name' in record_data and 'year_month' in record_data:
                # 直接創建新記錄，不檢查重複
                new_record = RawMaterialMonthlySummary.objects.create(**record_data)
                
                # 創建關聯記錄
                UploadRecordRelation.objects.create(
                    upload_record=upload_record,
                    content_type='monthly_summary',
                    object_id=new_record.id
                )
                
                records_count += 1
                
        except Exception as e:
            print(f"處理第 {index + 1} 行時發生錯誤: {e}")
            continue
    
    return records_count


@login_required
@require_http_methods(["GET"])
def upload_history_view(request):
    """上傳歷史記錄頁面（純淨模式，無左側選單）- 只需要登入"""
    uploads = FileUploadRecord.objects.all().order_by('-upload_time')
    
    context = {
        'uploads': uploads,
    }
    return render(request, 'erp/upload_history_clean.html', context)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_upload_record(request, upload_id):
    """刪除單個上傳記錄並還原相關業務資料 - 只需要登入"""
    try:
        upload_record = FileUploadRecord.objects.get(id=upload_id)
        file_name = upload_record.file_name
        
        # 獲取所有相關的業務記錄
        relations = UploadRecordRelation.objects.filter(upload_record=upload_record)
        deleted_count = 0
        
        with transaction.atomic():
            # 根據不同類型刪除相關記錄
            for relation in relations:
                try:
                    if relation.content_type == 'green_bean':
                        GreenBeanInboundRecord.objects.filter(id=relation.object_id).delete()
                        deleted_count += 1
                    elif relation.content_type == 'raw_material':
                        RawMaterialWarehouseRecord.objects.filter(id=relation.object_id).delete()
                        deleted_count += 1
                    elif relation.content_type == 'monthly_summary':
                        RawMaterialMonthlySummary.objects.filter(id=relation.object_id).delete()
                        deleted_count += 1
                except Exception as e:
                    print(f"刪除關聯記錄失敗: {e}")
            
            # 刪除關聯記錄
            relations.delete()
            
            # 刪除上傳記錄
            upload_record.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'已刪除上傳記錄「{file_name}」及相關的 {deleted_count} 筆業務資料'
        })
        
    except FileUploadRecord.DoesNotExist:
        return JsonResponse({'success': False, 'message': '記錄不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'刪除失敗：{str(e)}'})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def batch_delete_upload_records(request):
    """批量刪除上傳記錄並還原相關業務資料 - 只需要登入"""
    try:
        import json
        data = json.loads(request.body)
        upload_ids = data.get('upload_ids', [])
        
        if not upload_ids:
            return JsonResponse({'success': False, 'message': '請選擇要刪除的記錄'})
        
        # 檢查記錄是否存在
        existing_records = FileUploadRecord.objects.filter(id__in=upload_ids)
        if not existing_records.exists():
            return JsonResponse({'success': False, 'message': '沒有找到要刪除的記錄'})
        
        total_business_deleted = 0
        upload_deleted_count = 0
        
        with transaction.atomic():
            for upload_record in existing_records:
                # 獲取所有相關的業務記錄
                relations = UploadRecordRelation.objects.filter(upload_record=upload_record)
                
                # 根據不同類型刪除相關記錄
                for relation in relations:
                    try:
                        if relation.content_type == 'green_bean':
                            GreenBeanInboundRecord.objects.filter(id=relation.object_id).delete()
                            total_business_deleted += 1
                        elif relation.content_type == 'raw_material':
                            RawMaterialWarehouseRecord.objects.filter(id=relation.object_id).delete()
                            total_business_deleted += 1
                        elif relation.content_type == 'monthly_summary':
                            RawMaterialMonthlySummary.objects.filter(id=relation.object_id).delete()
                            total_business_deleted += 1
                    except Exception as e:
                        print(f"刪除關聯記錄失敗: {e}")
                
                # 刪除關聯記錄
                relations.delete()
                upload_deleted_count += 1
            
            # 刪除上傳記錄
            existing_records.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'成功刪除 {upload_deleted_count} 筆上傳記錄及相關的 {total_business_deleted} 筆業務資料',
            'deleted_count': upload_deleted_count,
            'business_deleted': total_business_deleted
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '請求格式錯誤'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'批量刪除失敗：{str(e)}'})


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def clear_all_upload_records(request):
    """清空所有上傳記錄並還原相關業務資料 - 需要ERP用戶權限"""
    try:
        all_records = FileUploadRecord.objects.all()
        total_business_deleted = 0
        upload_deleted_count = all_records.count()
        
        with transaction.atomic():
            for upload_record in all_records:
                # 獲取所有相關的業務記錄
                relations = UploadRecordRelation.objects.filter(upload_record=upload_record)
                
                # 根據不同類型刪除相關記錄
                for relation in relations:
                    try:
                        if relation.content_type == 'green_bean':
                            GreenBeanInboundRecord.objects.filter(id=relation.object_id).delete()
                            total_business_deleted += 1
                        elif relation.content_type == 'raw_material':
                            RawMaterialWarehouseRecord.objects.filter(id=relation.object_id).delete()
                            total_business_deleted += 1
                        elif relation.content_type == 'monthly_summary':
                            RawMaterialMonthlySummary.objects.filter(id=relation.object_id).delete()
                            total_business_deleted += 1
                    except Exception as e:
                        print(f"刪除關聯記錄失敗: {e}")
            
            # 刪除所有關聯記錄
            UploadRecordRelation.objects.all().delete()
            
            # 刪除所有上傳記錄
            all_records.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'成功清空所有記錄：{upload_deleted_count} 筆上傳記錄及相關的 {total_business_deleted} 筆業務資料',
            'deleted_count': upload_deleted_count,
            'business_deleted': total_business_deleted
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'清空記錄失敗：{str(e)}'})


@csrf_exempt
@require_http_methods(["POST"])
def analyze_uploaded_file(request):
    """分析上傳檔案的結構（調試用）"""
    try:
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'success': False, 'message': '請選擇要分析的檔案'})
        
        # 讀取Excel檔案
        df = pd.read_excel(uploaded_file)
        
        # 分析檔案結構
        analysis = {
            'file_name': uploaded_file.name,
            'file_size': uploaded_file.size,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'data_types': {col: str(df[col].dtype) for col in df.columns},
            'null_counts': {col: int(df[col].isnull().sum()) for col in df.columns},
            'sample_data': df.head(5).to_dict('records'),
            'non_empty_rows': len(df.dropna(how='all'))
        }
        
        # 檢查每列的樣本值
        column_samples = {}
        for col in df.columns:
            non_null_data = df[col].dropna()
            if len(non_null_data) > 0:
                column_samples[col] = non_null_data.head(3).tolist()
            else:
                column_samples[col] = []
        
        analysis['column_samples'] = column_samples
        
        return JsonResponse({'success': True, 'analysis': analysis})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'分析失敗：{str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
def debug_raw_material_upload(request):
    """調試原料倉上傳 - 詳細分析每個步驟"""
    try:
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'success': False, 'message': '請選擇要分析的檔案'})
        
        print("=== 調試原料倉上傳 ===")
        print(f"檔案名稱: {uploaded_file.name}")
        print(f"檔案大小: {uploaded_file.size}")
        
        # 確保檔案指針在開頭
        uploaded_file.seek(0)
        
        # 讀取Excel檔案
        df = pd.read_excel(uploaded_file)
        print(f"讀取Excel成功，資料形狀: {df.shape}")
        print(f"欄位列表: {list(df.columns)}")
        
        # 顯示前幾行資料
        print("前3行資料:")
        for i, row in df.head(3).iterrows():
            print(f"第{i+1}行: {dict(row)}")
        
        # 檢查是否有非空資料
        non_empty_df = df.dropna(how='all')
        print(f"非空行數: {len(non_empty_df)}")
        
        # 分析欄位映射匹配情況
        column_mapping = {
            '品號': 'product_code',
            '品名': 'product_name',
            '工廠批號': 'factory_batch_number',
            '國際批號': 'international_batch_number',
            '標準重(kg)': 'standard_weight_kg',
            '上月庫存': 'previous_month_inventory',
            '進貨': 'incoming_stock',
            '領用': 'outgoing_stock',
            '當前庫存': 'current_inventory',
            '待處理': 'pending_processing',
            '開袋+品管+外賣剩下': 'opened_quality_external_remaining',
            '外賣': 'external_sales',
            '記錄日期': 'record_date',
        }
        
        matched_columns = []
        unmatched_columns = []
        
        for excel_col in df.columns:
            if excel_col in column_mapping:
                matched_columns.append(excel_col)
            else:
                unmatched_columns.append(excel_col)
        
        print(f"匹配的欄位: {matched_columns}")
        print(f"未匹配的欄位: {unmatched_columns}")
        
        # 嘗試處理第一行資料
        if len(df) > 0:
            first_row = df.iloc[0]
            print("處理第一行資料:")
            record_data = {}
            
            # 處理記錄日期
            from datetime import date
            record_data['record_date'] = date.today()
            
            # 處理其他欄位
            for excel_col, model_field in column_mapping.items():
                if excel_col in df.columns:
                    value = first_row[excel_col]
                    print(f"  {excel_col} -> {model_field}: {value} (類型: {type(value)})")
                    if pd.notna(value):
                        if model_field in [
                            'standard_weight_kg', 'previous_month_inventory', 
                            'incoming_stock', 'outgoing_stock', 'current_inventory',
                            'pending_processing', 'opened_quality_external_remaining', 'external_sales'
                        ]:
                            try:
                                record_data[model_field] = float(value)
                                print(f"    轉換為數值: {record_data[model_field]}")
                            except:
                                record_data[model_field] = 0.0
                                print(f"    轉換失敗，設為 0.0")
                        else:
                            record_data[model_field] = str(value).strip()
                            print(f"    轉換為文字: '{record_data[model_field]}'")
            
            print(f"最終處理的資料: {record_data}")
            
            # 檢查是否有有用資料
            has_useful_data = False
            for key, value in record_data.items():
                if key != 'record_date' and value is not None and str(value).strip() != '' and str(value).strip() != '0.0':
                    has_useful_data = True
                    print(f"找到有用資料: {key} = {value}")
                    break
            
            print(f"是否有有用資料: {has_useful_data}")
        
        return JsonResponse({
            'success': True,
            'debug_info': {
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'total_rows': len(df),
                'non_empty_rows': len(non_empty_df),
                'columns': list(df.columns),
                'matched_columns': matched_columns,
                'unmatched_columns': unmatched_columns,
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
            }
        })
        
    except Exception as e:
        print(f"調試原料倉上傳失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'調試失敗：{str(e)}'})
