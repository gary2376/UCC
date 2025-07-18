from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.urls import reverse


class ERPAdminSite(admin.AdminSite):
    """ERP 專用 Admin 網站"""
    site_header = 'ERP 權限管理系統'
    site_title = 'ERP Admin'
    index_title = '權限管理'

    def get_urls(self):
        """自定義URL模式"""
        urls = super().get_urls()
        
        # 添加權限管理的URL
        custom_urls = [
            path('permissions/', self.admin_view(self.permissions_view), name='permissions'),
        ]
        
        return custom_urls + urls
    
    def permissions_view(self, request):
        """權限管理視圖，重定向到主admin的權限頁面"""
        return HttpResponseRedirect('/admin/auth/permission/')


# 創建ERP admin站點實例
erp_admin_site = ERPAdminSite(name='erp_admin')

# 註冊模型到ERP admin
erp_admin_site.register(Group)
erp_admin_site.register(Permission)
