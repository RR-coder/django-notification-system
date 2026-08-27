from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    CustomTokenObtainPairView,
    MeView,
    TelegramOTPRequestView,
    TelegramOTPVerifyView,
)
from classes.views import ClassListCreateView, ClassDetailView
from notifications.views import (
    NotificationTemplateListCreateView,
    NotificationListCreateView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/auth/token/",
        CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/auth/telegram/request-otp/",
        TelegramOTPRequestView.as_view(),
        name="telegram_request_otp",
    ),
    path(
        "api/auth/telegram/verify-otp/",
        TelegramOTPVerifyView.as_view(),
        name="telegram_verify_otp",
    ),
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/me/",
        MeView.as_view(),
        name="me",
    ),
    path(
        "api/classes/",
        ClassListCreateView.as_view(),
        name="class-list-create",
    ),
    path(
        "api/classes/<int:pk>/",
        ClassDetailView.as_view(),
        name="class-detail",
    ),
    path(
        "api/notification-templates/",
        NotificationTemplateListCreateView.as_view(),
        name="notification-template-list-create",
    ),
    path(
        "api/notifications/",
        NotificationListCreateView.as_view(),
        name="notification-list-create",
    ),
]