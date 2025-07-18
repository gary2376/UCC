from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.contrib.auth.decorators import permission_required


@permission_required('auth.view_permission', raise_exception=True)
def erp_permissions_hub(request):
    """ERP權限管理中心 - 主要入口"""
    groups = Group.objects.prefetch_related('permissions', 'user_set').all()
    permissions = Permission.objects.select_related('content_type').all()
    
    # 處理快速創建群組
    if request.method == 'POST' and 'create_group' in request.POST:
        group_name = request.POST.get('group_name')
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                messages.success(request, f'群組 "{group_name}" 已創建成功！')
                return redirect('admin:auth_group_change', group.id)
            else:
                messages.warning(request, f'群組 "{group_name}" 已存在')
        else:
            messages.error(request, '群組名稱不能為空')
    
    context = {
        'groups': groups,
        'permissions': permissions,
        'title': 'ERP 權限管理中心',
        'has_add_permission': True,
        'has_change_permission': True,
    }
    
    return render(request, 'admin/erp_permissions_hub.html', context)


@permission_required('auth.view_group', raise_exception=True)
def erp_group_quick_edit(request, group_id):
    """ERP群組快速編輯"""
    group = get_object_or_404(Group, id=group_id)
    all_permissions = Permission.objects.select_related('content_type').all()
    
    if request.method == 'POST':
        # 更新群組權限
        permission_ids = request.POST.getlist('permissions')
        group.permissions.set(permission_ids)
        messages.success(request, f'群組 "{group.name}" 的權限已更新')
        return redirect('admin_erp:erp_permissions_hub')
    
    context = {
        'group': group,
        'all_permissions': all_permissions,
        'group_permissions': group.permissions.all(),
        'title': f'編輯群組: {group.name}',
    }
    
    return render(request, 'admin/erp_group_edit.html', context)


@permission_required('auth.change_group', raise_exception=True)
@require_POST
def ajax_group_permissions(request):
    """AJAX更新群組權限"""
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        permission_ids = data.get('permission_ids', [])
        
        group = Group.objects.get(id=group_id)
        group.permissions.set(permission_ids)
        
        return JsonResponse({
            'success': True,
            'message': f'群組 "{group.name}" 權限已更新',
            'permission_count': group.permissions.count()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@permission_required('auth.delete_group', raise_exception=True)
def ajax_delete_group(request, group_id):
    """AJAX刪除群組"""
    if request.method == 'POST':
        try:
            group = Group.objects.get(id=group_id)
            if group.user_set.count() > 0:
                return JsonResponse({
                    'success': False, 
                    'error': f'無法刪除群組 "{group.name}"，因為還有 {group.user_set.count()} 個使用者屬於此群組'
                })
            
            group_name = group.name
            group.delete()
            return JsonResponse({
                'success': True,
                'message': f'群組 "{group_name}" 已刪除'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': '僅支持POST方法'})
