#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.models.models import GreenBeanInboundRecord, RawMaterialWarehouseRecord, RawMaterialMonthlySummary


class Command(BaseCommand):
    help = '從 Excel 檔案導入 ERP 數據'

    def add_arguments(self, parser):
        parser.add_argument(
            '--green-bean-file',
            type=str,
            help='生豆入庫記錄 Excel 檔案路徑'
        )
        parser.add_argument(
            '--raw-material-file',
            type=str,
            help='原料倉進出 Excel 檔案路徑'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='清除現有數據後再導入'
        )

    def handle(self, *args, **options):
        try:
            if options['clear_existing']:
                self.stdout.write('清除現有數據...')
                try:
                    GreenBeanInboundRecord.objects.all().delete()
                    RawMaterialWarehouseRecord.objects.all().delete()
                    RawMaterialMonthlySummary.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('現有數據已清除'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'清除數據時出現警告: {str(e)}'))

            if options['green_bean_file']:
                self.import_green_bean_records(options['green_bean_file'])

            if options['raw_material_file']:
                self.import_raw_material_records(options['raw_material_file'])

        except Exception as e:
            raise CommandError(f'導入過程中發生錯誤: {str(e)}')

    def import_green_bean_records(self, file_path):
        """導入生豆入庫記錄"""
        self.stdout.write(f'開始導入生豆入庫記錄: {file_path}')
        
        if not os.path.exists(file_path):
            raise CommandError(f'檔案不存在: {file_path}')

        try:
            df = pd.read_excel(file_path)
            self.stdout.write(f'找到 {len(df)} 筆記錄')

            with transaction.atomic():
                records_created = 0
                for index, row in df.iterrows():
                    try:
                        # 處理時間欄位
                        record_time = self.parse_datetime(row.get('記錄時間'))
                        work_start_time = self.parse_datetime(row.get('作業開始時間'))
                        work_end_time = self.parse_datetime(row.get('作業結束時間'))

                        record = GreenBeanInboundRecord(
                            is_abnormal=(row.get('異常') == 'Y'),
                            record_time=record_time,
                            order_number=str(row.get('單號', '')),
                            roasted_item_sequence=self.safe_int(row.get('炒豆\n項次')),
                            green_bean_item_sequence=self.safe_int(row.get('生豆\n項次')),
                            batch_sequence=self.safe_int(row.get('波次')),
                            execution_status=str(row.get('執行\n狀態', '')),
                            green_bean_batch_number=str(row.get('生豆\n批號', '')),
                            green_bean_code=str(row.get('生豆料號', '')),
                            green_bean_name=str(row.get('生豆名稱', '')),
                            green_bean_storage_silo=str(row.get('生豆入庫\n筒倉', '')),
                            bag_weight_kg=self.safe_decimal(row.get('一袋\n重量(kg)')),
                            input_bag_count=self.safe_int(row.get('投入\n袋數')),
                            required_weight_kg=self.safe_decimal(row.get('需求\n重量(kg)')),
                            measured_weight_kg=self.safe_decimal(row.get('生豆量測\n重量(kg)')),
                            manual_input_weight_kg=self.safe_decimal(row.get('手動投入\n重量(kg)')),
                            work_start_time=work_start_time,
                            work_end_time=work_end_time,
                            work_duration=str(row.get('作業時間', '')),
                            ico_code=str(row.get('ICO', '')),
                            remark=str(row.get('備註', ''))
                        )
                        record.save()
                        records_created += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'跳過第 {index + 1} 行 (錯誤: {str(e)})')
                        )
                        continue

                self.stdout.write(
                    self.style.SUCCESS(f'成功導入 {records_created} 筆生豆入庫記錄')
                )

        except Exception as e:
            raise CommandError(f'導入生豆入庫記錄時發生錯誤: {str(e)}')

    def import_raw_material_records(self, file_path):
        """導入原料倉進出記錄"""
        self.stdout.write(f'開始導入原料倉進出記錄: {file_path}')
        
        if not os.path.exists(file_path):
            raise CommandError(f'檔案不存在: {file_path}')

        try:
            df = pd.read_excel(file_path)
            self.stdout.write(f'找到 {len(df)} 筆記錄')

            # 找到有效的數據行（排除標題行和空行）
            valid_rows = []
            for index, row in df.iterrows():
                # 檢查是否有品號和品名
                product_code = str(row.iloc[1]) if len(row) > 1 else ''
                product_name = str(row.iloc[2]) if len(row) > 2 else ''
                
                if (product_code and product_code not in ['nan', 'NaN', ''] and 
                    product_name and product_name not in ['nan', 'NaN', '']):
                    valid_rows.append((index, row))

            self.stdout.write(f'找到 {len(valid_rows)} 筆有效記錄')

            with transaction.atomic():
                records_created = 0
                for index, row in valid_rows:
                    try:
                        record = RawMaterialWarehouseRecord(
                            product_code=str(row.iloc[1]) if len(row) > 1 else '',
                            product_name=str(row.iloc[2]) if len(row) > 2 else '',
                            factory_batch_number=str(row.iloc[3]) if len(row) > 3 else '',
                            international_batch_number=str(row.iloc[4]) if len(row) > 4 else '',
                            standard_weight_kg=self.safe_decimal(row.iloc[5]) if len(row) > 5 else None,
                            previous_month_inventory=self.safe_decimal(row.iloc[6]) if len(row) > 6 else None,
                            incoming_stock=self.safe_decimal(row.iloc[7]) if len(row) > 7 else None,
                            outgoing_stock=self.safe_decimal(row.iloc[8]) if len(row) > 8 else None,
                            current_inventory=self.safe_decimal(row.iloc[9]) if len(row) > 9 else None,
                            pending_processing=self.safe_decimal(row.iloc[10]) if len(row) > 10 else None,
                            opened_quality_external_remaining=self.safe_decimal(row.iloc[12]) if len(row) > 12 else None,
                            external_sales=self.safe_decimal(row.iloc[16]) if len(row) > 16 else None,
                        )
                        record.save()
                        records_created += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'跳過第 {index + 1} 行 (錯誤: {str(e)})')
                        )
                        continue

                self.stdout.write(
                    self.style.SUCCESS(f'成功導入 {records_created} 筆原料倉記錄')
                )

        except Exception as e:
            raise CommandError(f'導入原料倉記錄時發生錯誤: {str(e)}')

    def parse_datetime(self, value):
        """解析日期時間"""
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        try:
            # 嘗試不同的日期格式
            date_formats = [
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d',
                '%Y-%m-%d'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(value), fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None

    def safe_int(self, value):
        """安全轉換為整數"""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def safe_decimal(self, value):
        """安全轉換為小數"""
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
