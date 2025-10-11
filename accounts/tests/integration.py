import pytest
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from accounts.models import CustomUser


class TestFullRegistrationFlow(TestCase):
    """تست جریان کامل ثبت‌نام و تأیید OTP"""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('accounts:signup')
        self.verify_url = reverse('accounts:verify_otp')
        self.valid_data = {
            'phone': '09123456789',
            'password': 'TestPass123!',
            'email': 'test@example.com'
        }

    @patch('accounts.models.CustomUser.send_otp')
    @patch('accounts.models.CustomUser.verify_otp')
    def test_complete_registration_flow(self, mock_verify_otp, mock_send_otp):
        """تست کامل فرآیند ثبت‌نام از ابتدا تا انتها"""
        # مرحله ۱: ثبت‌نام
        mock_send_otp.return_value = True
        response = self.client.post(self.signup_url, self.valid_data)

        self.assertRedirects(response, self.verify_url)

        user = CustomUser.objects.get(phone='09123456789')
        self.assertFalse(user.is_active)

        # مرحله ۲: تأیید OTP
        mock_verify_otp.return_value = (True, "تأیید موفق")
        response = self.client.post(self.verify_url, {'otp_code': '123456'})

        self.assertRedirects(response, reverse('pages:home'))

        # کاربر نهایی باید فعال و لاگین شده باشد
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_phone_verified)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    @patch('accounts.models.CustomUser.send_otp')
    def test_registration_cleanup_on_failure(self, mock_send_otp):
        """تست پاک‌سازی در صورت شکست فرآیند"""
        mock_send_otp.side_effect = Exception("SMS failure")

        response = self.client.post(self.signup_url, self.valid_data)

        # کاربر موقت باید حذف شده باشد
        self.assertEqual(CustomUser.objects.filter(phone='09123456789').count(), 0)