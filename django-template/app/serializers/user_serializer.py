#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from app.models import User
from app.models.models import AdminUser, GreenBeanInboundRecord, RawMaterialWarehouseRecord, RawMaterialMonthlySummary


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'email', 'password']
        extra_kwargs = {
            'email': {
                'validators': [
                    UniqueValidator(queryset=User.objects.all())
                ]
            }
        }


class FullUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'email']


class ChangePasswordSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ['old_password', 'new_password']

    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class GreenBeanInboundRecordSerializer(serializers.ModelSerializer):
    """生豆入庫記錄序列化器"""
    class Meta:
        model = GreenBeanInboundRecord
        fields = [
            'id', 'is_abnormal', 'record_time', 'order_number',
            'roasted_item_sequence', 'green_bean_item_sequence', 'batch_sequence',
            'execution_status', 'green_bean_batch_number', 'green_bean_code',
            'green_bean_name', 'green_bean_storage_silo', 'bag_weight_kg',
            'input_bag_count', 'required_weight_kg', 'measured_weight_kg',
            'manual_input_weight_kg', 'work_start_time', 'work_end_time',
            'work_duration', 'ico_code', 'remark', 'created_at', 'updated_at'
        ]


class RawMaterialWarehouseRecordSerializer(serializers.ModelSerializer):
    """原料倉進出記錄序列化器"""
    class Meta:
        model = RawMaterialWarehouseRecord
        fields = [
            'id', 'product_code', 'product_name', 'factory_batch_number',
            'international_batch_number', 'standard_weight_kg',
            'previous_month_inventory', 'incoming_stock', 'outgoing_stock',
            'current_inventory', 'pending_processing',
            'opened_quality_external_remaining', 'external_sales',
            'record_date', 'created_at', 'updated_at'
        ]


class RawMaterialMonthlySummarySerializer(serializers.ModelSerializer):
    """原料月度統計序列化器"""
    class Meta:
        model = RawMaterialMonthlySummary
        fields = [
            'id', 'year', 'month', 'total_inventory_value',
            'total_incoming_stock', 'total_outgoing_stock',
            'total_current_inventory', 'created_at', 'updated_at'
        ]
