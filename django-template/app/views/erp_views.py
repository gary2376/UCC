#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
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

from app.models.models import GreenBeanInboundRecord, RawMaterialWarehouseRecord, RawMaterialMonthlySummary
from app.serializers.user_serializer import (
    GreenBeanInboundRecordSerializer,
    RawMaterialWarehouseRecordSerializer,
    RawMaterialMonthlySummarySerializer
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


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
        
        context = {
            'stats': stats,
            'recent_records': recent_records,
            'low_inventory_items': low_inventory_items,
        }
        
        print(f"Debug: 查詢到 {len(recent_records)} 筆生豆入庫記錄")
        print(f"Debug: 總共有 {stats['total_green_bean_records']} 筆記錄")
        
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