from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Class


User = get_user_model()


class ClassSerializer(serializers.ModelSerializer):
    teachers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role=User.Role.TEACHER),
        required=False,
    )

    students = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role=User.Role.STUDENT),
        required=False,
    )

    class Meta:
        model = Class
        fields = ["id", "name", "teachers", "students"]
        read_only_fields = ["id"]