from django.contrib import admin

admin.site.site_header = ''
admin.site.site_title = ''
admin.site.index_title = '控制台'
admin.site.empty_value_display = '(無)'

# 導入所有的 admin 類別以確保它們被正確註冊
from . import admins  # noqa
