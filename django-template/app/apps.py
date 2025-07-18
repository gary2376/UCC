from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'ERP 系統'

    def ready(self):
        # Makes sure all signal handlers are connected
        from app import handler  # noqa
        from app import signals  # noqa
        # 確保 admin 模組被正確導入和註冊
        from app import admin  # noqa
