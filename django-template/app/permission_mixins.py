# -*- coding: utf-8 -*-
"""
權限混合類
用於基於類的視圖的權限檢查
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from app.permission_utils import has_view_permission, has_edit_permission


class ViewPermissionMixin(UserPassesTestMixin):
    """需要查看權限的視圖混合類"""
    def test_func(self):
        return has_view_permission(self.request.user)


class EditPermissionMixin(UserPassesTestMixin):
    """需要編輯權限的視圖混合類"""
    def test_func(self):
        return has_edit_permission(self.request.user)
