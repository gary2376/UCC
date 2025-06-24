from django.contrib.auth import views
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.urls.rf_router import router
from app.views.home_views import home_view, health_check

app_name = 'app'

urlpatterns = [
    # 根路徑重定向到ERP儀表板
    path('', home_view, name='home'),
    # 健康檢查
    path('health/', health_check, name='health_check'),
    # API
    path('api/', include(router.urls)),
    # path('api/s3/', include('app.urls.s3_api')),
    re_path('api/login/?$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path('api/logout/?$', views.LogoutView.as_view()),
    re_path('api/token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    # 後台自訂頁面
    # path('', include('app.urls.custom')),
]
