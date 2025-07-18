"""DjangoTemplate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
                  path('__debug__/', include(debug_toolbar.urls)),
              ] \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
              + [
                  # 忘記密碼
                  path('password_reset/', auth_views.PasswordResetView.as_view(), name='admin_password_reset'),
                  path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(),
                       name='password_reset_done'),
                  path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
                       name='password_reset_confirm'),
                  path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
                  # 專案路由
                  path('', include('app.urls')),
                  # ERP 系統
                  path('erp/', include('app.urls.erp')),
                  # ERP 權限管理 (在admin下的自定義路徑)
                  path('admin/erp/', include('app.urls.admin_erp')),
                  # 後台
                  path('admin/', admin.site.urls),
              ]
