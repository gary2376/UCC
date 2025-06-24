from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from app.models import User, AdminUser
from app.serializers.admin_serializer import FullAdminUserSerializer
from app.serializers.user_serializer import FullUserSerializer, ChangePasswordSerializer
from app.views.general import FlatternJSONRenderer


class UserViewSet(mixins.UpdateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = FullUserSerializer
    permission_classes = [DjangoModelPermissions]
    renderer_classes = [FlatternJSONRenderer]

    def get_object(self):
        return self.request.user

    @action(methods=['GET'], detail=False, serializer_class=FullUserSerializer)
    def info(self, request):
        user = self.get_object()
        role = ""
        serializer = None
        consent_signed = None
        try:
            item = user.adminuser
            serializer = FullAdminUserSerializer(item)
            role = "adminuser"
        except AdminUser.DoesNotExist:
            pass
        data = {}
        if serializer is not None:
            data = serializer.data
            data['role'] = role
        return Response(data)

    @action(detail=False, methods=['post'], serializer_class=ChangePasswordSerializer, permission_classes=[IsAuthenticated])
    def change_password(self, request):
        obj = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            old_password = serializer.data.get("old_password")
            if not obj.check_password(old_password):
                return Response({"old_password": ["密碼錯誤"]},
                                status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            obj.set_password(serializer.data.get("new_password"))
            obj.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
