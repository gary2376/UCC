from rest_framework.routers import DefaultRouter

from app.views.user_view import UserViewSet


class OptionalSlashRouter(DefaultRouter):
    """Make all trailing slashes optional in the URLs used by the viewsets
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'


router = OptionalSlashRouter()
router.register(r'user', UserViewSet)
