from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import permission_required


@permission_required('auth.view_permission', raise_exception=True)
def permission_management_view(request):
    """權限管理總覽頁面"""
    groups = Group.objects.prefetch_related('permissions', 'user_set').all()
    permissions = Permission.objects.select_related('content_type').all()
    users = User.objects.prefetch_related('groups', 'user_permissions').all()
    content_types = ContentType.objects.all()
    
    context = {
        'groups': groups,
        'permissions': permissions,
        'users': users,
        'content_types': content_types,
        'title': '權限管理中心'
    }
    
    return render(request, 'admin/permission_management.html', context)


@permission_required('auth.view_group', raise_exception=True)
def group_detail_view(request, group_id):
    """群組詳細資訊和權限編輯"""
    group = get_object_or_404(Group, id=group_id)
    all_permissions = Permission.objects.select_related('content_type').all()
    group_permissions = group.permissions.all()
    users_in_group = group.user_set.all()
    
    if request.method == 'POST':
        # 更新群組權限
        permission_ids = request.POST.getlist('permissions')
        group.permissions.set(permission_ids)
        messages.success(request, f'群組 "{group.name}" 的權限已更新')
        return redirect('admin:group_detail', group_id=group.id)
    
    context = {
        'group': group,
        'all_permissions': all_permissions,
        'group_permissions': group_permissions,
        'users_in_group': users_in_group,
        'title': f'群組管理: {group.name}'
    }
    
    return render(request, 'admin/group_detail.html', context)


@permission_required('auth.view_permission', raise_exception=True)
def user_permissions_view(request, user_id):
    """使用者權限編輯"""
    user = get_object_or_404(User, id=user_id)
    all_groups = Group.objects.all()
    all_permissions = Permission.objects.select_related('content_type').all()
    
    if request.method == 'POST':
        # 更新使用者群組
        group_ids = request.POST.getlist('groups')
        user.groups.set(group_ids)
        
        # 更新使用者個別權限
        permission_ids = request.POST.getlist('user_permissions')
        user.user_permissions.set(permission_ids)
        
        messages.success(request, f'使用者 "{user.username}" 的權限已更新')
        return redirect('admin:user_permissions', user_id=user.id)
    
    context = {
        'user': user,
        'all_groups': all_groups,
        'all_permissions': all_permissions,
        'user_groups': user.groups.all(),
        'user_permissions': user.user_permissions.all(),
        'title': f'使用者權限: {user.username}'
    }
    
    return render(request, 'admin/user_permissions.html', context)


@permission_required('auth.change_user', raise_exception=True)
@require_POST
def quick_assign_permission(request):
    """快速分配權限的AJAX端點"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        group_id = data.get('group_id')
        action = data.get('action')  # 'add' or 'remove'
        
        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)
        
        if action == 'add':
            user.groups.add(group)
            message = f'已將使用者 {user.username} 加入群組 {group.name}'
        elif action == 'remove':
            user.groups.remove(group)
            message = f'已將使用者 {user.username} 從群組 {group.name} 移除'
        else:
            return JsonResponse({'success': False, 'error': '無效的操作'})
        
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})





@permission_required('auth.add_group', raise_exception=True)
def create_group_view(request):
    """創建新群組"""
    if request.method == 'POST':
        group_name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                group.permissions.set(permission_ids)
                messages.success(request, f'群組 "{group_name}" 已成功創建')
                return redirect('admin:auth_group_change', group.id)
            else:
                messages.warning(request, f'群組 "{group_name}" 已存在')
                return redirect('admin:auth_group_change', group.id)
        else:
            messages.error(request, '群組名稱不能為空')
        
        return redirect('admin:auth_group_changelist')
    
    permissions = Permission.objects.select_related('content_type').all()
    context = {
        'permissions': permissions,
        'title': '創建新群組'
    }
    
    return render(request, 'admin/create_group.html', context)
