from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.response import Response

from accounts.permissions import IsAdmin
from classes.models import Class

from .models import Notification, NotificationTemplate
from .serializers import NotificationSerializer, NotificationTemplateSerializer


User = get_user_model()


class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdmin]


class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(
                message__icontains=search
            )

        week_ago = timezone.now() - timedelta(days=7)
        return queryset.filter(created_at__gte=week_ago).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        user = request.user
        template_id = request.data.get("template_id")
        recipient_ids = request.data.get("recipient_ids")
        send_to_all = request.data.get("send_to_all", False)
        notification_type = request.data.get("notification_type", "GENERAL")

        if not template_id:
            raise serializers.ValidationError({"template_id": "This field is required."})

        try:
            template = NotificationTemplate.objects.get(
                id=template_id,
                is_active=True,
            )
        except NotificationTemplate.DoesNotExist:
            raise serializers.ValidationError(
                {"template_id": "Invalid or inactive template."}
            )

        if user.role not in template.allowed_roles:
            raise serializers.ValidationError(
                {"template_id": "You are not allowed to use this template."}
            )

        if user.role == User.Role.ADMIN:
            if send_to_all:
                recipients = User.objects.filter(is_active=True)
            else:
                if not recipient_ids or not isinstance(recipient_ids, list):
                    raise serializers.ValidationError(
                        {"recipient_ids": "Provide a list of recipient IDs."}
                    )
                recipients = User.objects.filter(
                    id__in=recipient_ids,
                    is_active=True,
                )

        elif user.role == User.Role.TEACHER:
            assigned_classes = Class.objects.filter(teachers=user)
            student_ids = assigned_classes.values_list("students__id", flat=True).distinct()
            students = User.objects.filter(
                id__in=student_ids,
                role=User.Role.STUDENT,
                is_active=True,
            )

            if send_to_all:
                recipients = students
            else:
                if not recipient_ids or not isinstance(recipient_ids, list):
                    raise serializers.ValidationError(
                        {"recipient_ids": "Provide a list of student IDs."}
                    )
                recipients = students.filter(id__in=recipient_ids)

            requested_ids = set(recipient_ids or [])
            allowed_ids = set(recipients.values_list("id", flat=True))
            if not send_to_all and requested_ids != allowed_ids:
                raise serializers.ValidationError(
                    {"recipient_ids": "You can only notify students in your assigned classes."}
                )

        elif user.role == User.Role.STUDENT:
            if send_to_all:
                raise serializers.ValidationError(
                    {"send_to_all": "Students cannot send notifications to all students."}
                )

            if not recipient_ids or not isinstance(recipient_ids, list) or len(recipient_ids) != 1:
                raise serializers.ValidationError(
                    {"recipient_ids": "Students must select exactly one student."}
                )

            if recipient_ids[0] == user.id:
                raise serializers.ValidationError(
                    {"recipient_ids": "Students cannot notify themselves."}
                )

            own_class_ids = Class.objects.filter(students=user).values_list("id", flat=True)
            recipients = User.objects.filter(
                id=recipient_ids[0],
                role=User.Role.STUDENT,
                is_active=True,
                enrolled_classes__id__in=own_class_ids,
            ).distinct()

            if not recipients.exists():
                raise serializers.ValidationError(
                    {"recipient_ids": "You can only notify one student from your own class."}
                )

            one_hour_ago = timezone.now() - timedelta(hours=1)
            recent_count = Notification.objects.filter(
                sender=user,
                created_at__gte=one_hour_ago,
            ).count()
            if recent_count >= 1:
                raise serializers.ValidationError(
                    {"recipient_ids": "Students can send only one notification per hour."}
                )

        else:
            raise serializers.ValidationError({"role": "Unsupported user role."})

        if not recipients.exists():
            raise serializers.ValidationError({"recipient_ids": "No valid recipients found."})

        notifications = [
            Notification(
                recipient=recipient,
                sender=user,
                title=template.title,
                message=template.message,
                notification_type=notification_type,
            )
            for recipient in recipients
        ]
        Notification.objects.bulk_create(notifications)

        return Response(
            NotificationSerializer(notifications, many=True).data,
            status=201,
        )
