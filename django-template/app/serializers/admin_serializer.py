from rest_framework import serializers

from app.models import AdminUser
from app.serializers.user_serializer import CreateUserSerializer


class FullAdminUserSerializer(serializers.ModelSerializer):
    user = CreateUserSerializer(many=False)

    class Meta:
        model = AdminUser
        fields = '__all__'
