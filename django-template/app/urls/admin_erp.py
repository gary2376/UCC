from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from app.views.erp_views import ERPCleanDashboardView
from app.views.permission_management_views import (
    permission_management_view,
    group_detail_view,
    user_permissions_view,
    quick_assign_permission,
    create_group_view
)
from app.views.erp_permissions_views import (
    erp_permissions_hub,
    erp_group_quick_edit,
    ajax_group_permissions,
    ajax_delete_group
)


def permissions_redirect(request):
    """重定向到ERP權限管理中心"""
    return HttpResponseRedirect('/admin/erp/permissions-hub/')


app_name = 'admin_erp'

urlpatterns = [
    path('clean/', ERPCleanDashboardView.as_view(), name='clean_dashboard'),
    path('permissions/', erp_permissions_hub, name='permissions'),
    
    # ERP專用權限管理
    path('permissions-hub/', erp_permissions_hub, name='erp_permissions_hub'),
    path('group-edit/<int:group_id>/', erp_group_quick_edit, name='erp_group_edit'),
    path('ajax/group-permissions/', ajax_group_permissions, name='ajax_group_permissions'),
    path('ajax/delete-group/<int:group_id>/', ajax_delete_group, name='ajax_delete_group'),
    
    # 原有的權限管理視圖
    path('permission-center/', permission_management_view, name='permission_center'),
    path('group/<int:group_id>/', group_detail_view, name='group_detail'),
    path('user/<uuid:user_id>/permissions/', user_permissions_view, name='user_permissions'),
    path('quick-assign/', quick_assign_permission, name='quick_assign'),
    path('create-group/', create_group_view, name='create_group'),
]
