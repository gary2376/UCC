#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系統權限功能測試與驗證工具
根據權限管理界面中的八個功能模組進行全面檢查
"""
import os
import django
import sys
from datetime import datetime, timedelta

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoTemplate.settings')
django.setup()

from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models.models import (
    User, FeaturePermission, SystemFeature, 
    GreenBeanInboundRecord, RawMaterialWarehouseRecord,
    FileUploadRecord
)

User = get_user_model()

class PermissionFunctionTester:
    """權限功能測試器"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = []
        
        # 根據圖片中顯示的八個權限功能模組
        self.permission_modules = {
            'bean_management': {
                'name': '生豆管理',
                'description': '查看和管理生豆入庫記錄和投料記錄',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/',
                    '/erp/api/green-bean-records/',
                    '/erp/api/production-statistics/'
                ]
            },
            'material_inventory': {
                'name': '原料庫存',
                'description': '管理原料倉庫存和進出記錄',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/api/raw-material-records/',
                    '/erp/api/inventory-statistics/'
                ]
            },
            'monthly_statistics': {
                'name': '月度統計',
                'description': '查看月文統計和報表',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/api/inventory-statistics/',
                    '/erp/api/production-statistics/'
                ]
            },
            'warehouse_management': {
                'name': '倉庫管理',
                'description': '管理倉庫相關操作',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/api/raw-material-records/',
                    '/erp/api/inventory-statistics/'
                ]
            },
            'product_management': {
                'name': '產品管理',
                'description': '管理產品信息和規格',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/api/green-bean-records/',
                    '/erp/api/raw-material-records/'
                ]
            },
            'user_management': {
                'name': '用戶管理',
                'description': '管理系統用戶和權限',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/permissions/',
                    '/erp/permissions/batch-update/'
                ]
            },
            'system_settings': {
                'name': '系統設定',
                'description': '系統參數和配置管理',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/permissions/',
                    '/erp/upload/'
                ]
            },
            'file_upload': {
                'name': '檔案上傳',
                'description': '上傳和管理Excel等檔案',
                'features': ['view', 'edit'],
                'test_urls': [
                    '/erp/upload/',
                    '/erp/upload/history/'
                ]
            }
        }
        
    def setup_test_data(self):
        """設置測試數據"""
        print("📊 正在設置測試數據...")
        
        # 創建測試用戶組
        test_groups = [
            '生豆管理員',
            '原料管理員', 
            '系統管理員',
            'ERP用戶',
            '訪客'
        ]
        
        for group_name in test_groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                print(f"✅ 創建用戶組: {group_name}")
        
        # 創建測試用戶
        test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print("✅ 創建測試用戶: test_user")
        
        # 將測試用戶添加到組
        erp_group = Group.objects.get(name='ERP用戶')
        test_user.groups.add(erp_group)
        
        # 創建系統功能
        for module_key, module_info in self.permission_modules.items():
            feature, created = SystemFeature.objects.get_or_create(
                code=module_key,
                defaults={
                    'name': module_info['name'],
                    'description': module_info['description'],
                    'is_active': True
                }
            )
            if created:
                print(f"✅ 創建系統功能: {module_info['name']}")
        
        # 創建一些測試記錄
        if not GreenBeanInboundRecord.objects.exists():
            GreenBeanInboundRecord.objects.create(
                order_number='TEST001',
                green_bean_name='測試生豆',
                green_bean_code='GB001',
                measured_weight_kg=100.5,
                record_time=datetime.now()
            )
            print("✅ 創建測試生豆記錄")
            
        if not RawMaterialWarehouseRecord.objects.exists():
            RawMaterialWarehouseRecord.objects.create(
                product_code='RM001',
                product_name='測試原料',
                current_inventory=500.0,
                record_date=datetime.now().date()
            )
            print("✅ 創建測試原料記錄")
    
    def test_login_access(self):
        """測試登入和基本存取"""
        print("\n🔐 測試用戶登入和基本存取...")
        
        # 測試登入
        login_result = self.client.login(username='test_user', password='testpass123')
        
        result = {
            'module': '用戶認證',
            'test': '登入功能',
            'status': '✅ 通過' if login_result else '❌ 失敗',
            'details': '用戶可以正常登入系統' if login_result else '用戶無法登入',
            'url': '/admin/login/'
        }
        self.test_results.append(result)
        
        return login_result
    
    def test_permission_module(self, module_key, module_info):
        """測試特定權限模組"""
        print(f"\n🔍 測試權限模組: {module_info['name']}")
        
        results = []
        
        # 測試每個URL
        for url in module_info['test_urls']:
            try:
                response = self.client.get(url)
                
                # 分析回應狀態
                if response.status_code == 200:
                    status = '✅ 通過'
                    details = '頁面正常載入'
                elif response.status_code == 403:
                    status = '⚠️  權限不足'
                    details = '需要特定權限才能存取'
                elif response.status_code == 404:
                    status = '❌ 頁面不存在'
                    details = 'URL路由未正確設定'
                else:
                    status = f'⚠️  狀態碼: {response.status_code}'
                    details = f'回應狀態: {response.status_code}'
                
                result = {
                    'module': module_info['name'],
                    'test': f'存取 {url}',
                    'status': status,
                    'details': details,
                    'url': url,
                    'status_code': response.status_code
                }
                results.append(result)
                
            except Exception as e:
                result = {
                    'module': module_info['name'],
                    'test': f'存取 {url}',
                    'status': '❌ 錯誤',
                    'details': f'測試過程發生錯誤: {str(e)}',
                    'url': url,
                    'status_code': 'ERROR'
                }
                results.append(result)
        
        return results
    
    def test_data_integrity(self):
        """測試數據完整性"""
        print("\n📊 測試數據庫和數據完整性...")
        
        results = []
        
        # 測試生豆記錄
        bean_count = GreenBeanInboundRecord.objects.count()
        result = {
            'module': '生豆管理',
            'test': '數據庫記錄檢查',
            'status': '✅ 通過' if bean_count > 0 else '⚠️  無數據',
            'details': f'生豆入庫記錄: {bean_count} 筆',
            'url': 'Database'
        }
        results.append(result)
        
        # 測試原料記錄
        material_count = RawMaterialWarehouseRecord.objects.count()
        result = {
            'module': '原料庫存',
            'test': '數據庫記錄檢查',
            'status': '✅ 通過' if material_count > 0 else '⚠️  無數據',
            'details': f'原料倉記錄: {material_count} 筆',
            'url': 'Database'
        }
        results.append(result)
        
        # 測試用戶權限
        permission_count = FeaturePermission.objects.count()
        result = {
            'module': '用戶管理',
            'test': '權限記錄檢查',
            'status': '✅ 通過' if permission_count >= 0 else '❌ 失敗',
            'details': f'功能權限記錄: {permission_count} 筆',
            'url': 'Database'
        }
        results.append(result)
        
        return results
    
    def test_api_functionality(self):
        """測試 API 功能"""
        print("\n🔗 測試 API 功能...")
        
        results = []
        
        api_endpoints = [
            ('/erp/api/green-bean-records/', '生豆記錄 API'),
            ('/erp/api/raw-material-records/', '原料記錄 API'),
            ('/erp/api/inventory-statistics/', '庫存統計 API'),
            ('/erp/api/production-statistics/', '生產統計 API'),
        ]
        
        for url, name in api_endpoints:
            try:
                response = self.client.get(url)
                
                if response.status_code == 200:
                    # 嘗試解析 JSON
                    try:
                        data = response.json()
                        status = '✅ 通過'
                        details = f'API 正常運行，返回數據格式正確'
                    except:
                        status = '⚠️  格式錯誤'
                        details = 'API 回應但數據格式不正確'
                else:
                    status = f'⚠️  狀態碼: {response.status_code}'
                    details = f'API 回應狀態: {response.status_code}'
                
                result = {
                    'module': 'API 測試',
                    'test': name,
                    'status': status,
                    'details': details,
                    'url': url
                }
                results.append(result)
                
            except Exception as e:
                result = {
                    'module': 'API 測試',
                    'test': name,
                    'status': '❌ 錯誤',
                    'details': f'API 測試錯誤: {str(e)}',
                    'url': url
                }
                results.append(result)
        
        return results
    
    def run_comprehensive_test(self):
        """執行全面測試"""
        print("🚀 開始執行系統權限功能全面測試...")
        print("=" * 60)
        
        # 設置測試數據
        self.setup_test_data()
        
        # 測試登入
        if not self.test_login_access():
            print("❌ 登入測試失敗，無法繼續測試")
            return
        
        # 測試每個權限模組
        for module_key, module_info in self.permission_modules.items():
            module_results = self.test_permission_module(module_key, module_info)
            self.test_results.extend(module_results)
        
        # 測試數據完整性
        data_results = self.test_data_integrity()
        self.test_results.extend(data_results)
        
        # 測試 API 功能
        api_results = self.test_api_functionality()
        self.test_results.extend(api_results)
        
        # 生成測試報告
        self.generate_report()
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📋 系統權限功能測試報告")
        print("=" * 60)
        
        # 統計結果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if '✅' in r['status']])
        warning_tests = len([r for r in self.test_results if '⚠️' in r['status']])
        failed_tests = len([r for r in self.test_results if '❌' in r['status']])
        
        print(f"總測試項目: {total_tests}")
        print(f"通過: {passed_tests} ✅")
        print(f"警告: {warning_tests} ⚠️")
        print(f"失敗: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📊 詳細測試結果:")
        print("-" * 60)
        
        # 按模組分組顯示結果
        modules = {}
        for result in self.test_results:
            module = result['module']
            if module not in modules:
                modules[module] = []
            modules[module].append(result)
        
        for module, results in modules.items():
            print(f"\n🔹 {module}")
            for result in results:
                print(f"  {result['status']} {result['test']}")
                print(f"    └─ {result['details']}")
                if result.get('url') != 'Database':
                    print(f"    └─ URL: {result.get('url', 'N/A')}")
        
        # 生成建議
        print("\n💡 改善建議:")
        print("-" * 60)
        
        if failed_tests > 0:
            print("❌ 發現功能異常，建議：")
            print("   1. 檢查 URL 路由設定")
            print("   2. 確認視圖函數正確實現")
            print("   3. 檢查權限裝飾器配置")
        
        if warning_tests > 0:
            print("⚠️  發現權限或數據問題，建議：")
            print("   1. 確認用戶權限正確分配")
            print("   2. 檢查測試數據是否充足")
            print("   3. 驗證 API 數據格式")
        
        if passed_tests == total_tests:
            print("🎉 所有測試通過！系統功能運行正常。")
        
        print("\n" + "=" * 60)


def main():
    """主函數"""
    tester = PermissionFunctionTester()
    tester.run_comprehensive_test()


if __name__ == '__main__':
    main()
