from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import TelegramOTP


User = get_user_model()


class TelegramOTPTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="student1",
            password="TestPassword123!",
            role=User.Role.STUDENT,
            telegram_chat_id="123456789",
        )

    @patch("accounts.views._send_telegram_message")
    def test_request_otp_sends_telegram_message(self, send_message):
        response = self.client.post(
            reverse("telegram_request_otp"),
            {"username": "student1", "password": "TestPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["detail"],
            "OTP sent to your linked Telegram chat.",
        )
        send_message.assert_called_once()
        self.assertEqual(TelegramOTP.objects.filter(user=self.user).count(), 1)

    @patch("accounts.views._send_telegram_message")
    def test_request_otp_requires_linked_telegram_chat(self, send_message):
        self.user.telegram_chat_id = None
        self.user.save(update_fields=["telegram_chat_id"])
        response = self.client.post(
            reverse("telegram_request_otp"),
            {"username": "student1", "password": "TestPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        send_message.assert_not_called()

    @patch("accounts.views._send_telegram_message")
    def test_verify_otp_returns_jwt(self, send_message):
        response = self.client.post(
            reverse("telegram_request_otp"),
            {"username": "student1", "password": "TestPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        message = send_message.call_args.args[1]
        code = message.split("OTP is: ")[1].split("\n")[0]
        otp = TelegramOTP.objects.get(user=self.user)
        verify_response = self.client.post(
            reverse("telegram_verify_otp"),
            {"username": "student1", "otp": code},
            format="json",
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertIn("access", verify_response.data)
        self.assertIn("refresh", verify_response.data)
        self.assertEqual(verify_response.data["user"]["role"], "STUDENT")
        otp.refresh_from_db()
        self.assertIsNotNone(otp.used_at)

    @patch("accounts.views._send_telegram_message")
    def test_used_otp_cannot_be_reused(self, send_message):
        self.client.post(
            reverse("telegram_request_otp"),
            {"username": "student1", "password": "TestPassword123!"},
            format="json",
        )
        message = send_message.call_args.args[1]
        code = message.split("OTP is: ")[1].split("\n")[0]
        first = self.client.post(
            reverse("telegram_verify_otp"),
            {"username": "student1", "otp": code},
            format="json",
        )
        second = self.client.post(
            reverse("telegram_verify_otp"),
            {"username": "student1", "otp": code},
            format="json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)

    @patch("accounts.views._send_telegram_message")
    def test_request_otp_has_resend_cooldown(self, send_message):
        first = self.client.post(
            reverse("telegram_request_otp"),
            {"username": "student1", "password": "TestPassword123!"},
            format="json",
        )
        second = self.client.post(
            reverse("telegram_request_otp"),
            {"username": "student1", "password": "TestPassword123!"},
            format="json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        send_message.assert_called_once()
