from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import permission_required


@permission_required('auth.view_permission', raise_exception=True)
def permissions_redirect_view(request):
    """重定向到Django admin的權限管理頁面"""
    return HttpResponseRedirect('/admin/auth/permission/')


@permission_required('auth.view_group', raise_exception=True)
def groups_redirect_view(request):
    """重定向到Django admin的群組管理頁面"""
    return HttpResponseRedirect('/admin/auth/group/')
