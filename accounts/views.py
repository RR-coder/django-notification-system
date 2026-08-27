import secrets
import urllib.parse
import urllib.request
import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import TelegramOTP
from .serializers import CustomTokenObtainPairSerializer


User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "role": request.user.role,
        })


def _send_telegram_message(chat_id, text):
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": str(chat_id),
        "text": text,
    }).encode()
    request = urllib.request.Request(url, data=payload, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode()
            if response.status != 200:
                raise RuntimeError(f"Telegram API HTTP {response.status}: {body}")
            return body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            data = json.loads(body)
            description = data.get("description", body)
        except json.JSONDecodeError:
            description = body
        raise RuntimeError(
            f"Telegram API HTTP {exc.code}: {description}"
        ) from exc


class TelegramOTPRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request=request, username=username, password=password)
        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.telegram_chat_id:
            return Response(
                {"detail": "No Telegram chat is linked to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        if TelegramOTP.objects.filter(
            user=user,
            created_at__gte=now - timedelta(seconds=60),
            used_at__isnull=True,
        ).exists():
            return Response(
                {"detail": "Please wait before requesting another OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        otp = TelegramOTP.objects.create(
            user=user,
            code_hash=make_password(code),
            expires_at=now + timedelta(minutes=5),
        )

        try:
            _send_telegram_message(
                user.telegram_chat_id,
                f"Your Django Notification System login OTP is: {code}\n\nThis code expires in 5 minutes.",
            )
        except Exception as exc:
            otp.delete()
            print(f"Telegram API error: {exc!r}")
            return Response(
                {"detail": "Unable to send the OTP through Telegram."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"detail": "OTP sent to your linked Telegram chat."},
            status=status.HTTP_200_OK,
        )


class TelegramOTPVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username")
        code = request.data.get("otp")

        if not username or not code:
            return Response(
                {"detail": "username and otp are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = (
            TelegramOTP.objects.filter(user=user, used_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        now = timezone.now()

        if otp is None or otp.expires_at <= now or otp.attempts >= 5:
            return Response(
                {"detail": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password(str(code), otp.code_hash):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            return Response(
                {"detail": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp.used_at = now
        otp.save(update_fields=["used_at"])

        token = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            "refresh": str(token),
            "access": str(token.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            },
        })