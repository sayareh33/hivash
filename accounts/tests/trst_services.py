import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from django.core.exceptions import ValidationError
from accounts.services.otp_service import OTPService, send_sms_via_asanak


class TestOTPService:
    """تست‌های سرویس OTP"""

    def setup_method(self):
        cache.clear()

    def test_generate_otp(self):
        """تست تولید کد OTP"""
        otp = OTPService.generate_otp()

        # بررسی طول و عددی بودن
        assert len(str(otp)) == OTPService.OTP_LENGTH
        assert isinstance(otp, int)

    def test_store_and_retrieve_otp(self):
        """تست ذخیره و بازیابی OTP از کش"""
        phone = '09123456789'
        otp = 123456

        OTPService.store_otp(phone, otp)

        cache_key = f"otp_{phone}"
        cached_data = cache.get(cache_key)

        assert cached_data['code'] == otp
        assert cached_data['attempts'] == 0
        assert 'created_at' in cached_data

    def test_verify_otp_success(self):
        """تست تأیید موفق OTP"""
        phone = '09123456789'
        otp = 123456

        OTPService.store_otp(phone, otp)
        result = OTPService.verify_otp(phone, '123456')

        assert result == True
        # باید از کش پاک شده باشد
        assert cache.get(f"otp_{phone}") is None

    def test_verify_otp_wrong_code(self):
        """تست تأیید کد نادرست"""
        phone = '09123456789'
        otp = 123456

        OTPService.store_otp(phone, otp)

        with pytest.raises(ValidationError, match='کد تأیید نامعتبر است'):
            OTPService.verify_otp(phone, '000000')

        # بررسی افزایش شمارنده تلاش‌ها
        cached_data = cache.get(f"otp_{phone}")
        assert cached_data['attempts'] == 1

    def test_verify_otp_max_attempts(self):
        """تست بیشینه تلاش‌های ناموفق"""
        phone = '09123456789'
        otp = 123456

        OTPService.store_otp(phone, otp)

        # تلاش‌های متعدد
        for i in range(OTPService.MAX_ATTEMPTS):
            try:
                OTPService.verify_otp(phone, '000000')
            except ValidationError as e:
                if i < OTPService.MAX_ATTEMPTS - 1:
                    assert 'تلاش باقی مانده' in str(e)
                else:
                    assert 'تعداد تلاش‌های شما بیش از حد' in str(e)

        # باید از کش پاک شده باشد
        assert cache.get(f"otp_{phone}") is None

    def test_verify_otp_expired(self):
        """تست انقضای OTP"""
        phone = '09123456789'

        with pytest.raises(ValidationError, match='کد تأیید منقضی شده'):
            OTPService.verify_otp(phone, '123456')


class TestSmsService:
    """تست‌های سرویس ارسال پیامک"""

    @patch('accounts.services.otp_service.requests.post')
    def test_send_sms_success(self, mock_post):
        """تست ارسال موفق پیامک"""
        # شبیه‌سازی پاسخ موفق آسانک
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "0", "message": "success"}'
        mock_post.return_value = mock_response

        result = send_sms_via_asanak('09123456789', '123456')

        assert result is True
        mock_post.assert_called_once()

    @patch('accounts.services.otp_service.requests.post')
    def test_send_sms_failure(self, mock_post):
        """تست ارسال ناموفق پیامک"""
        # شبیه‌سازی خطای آسانک
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "1", "message": "error"}'
        mock_post.return_value = mock_response

        result = send_sms_via_asanak('09123456789', '123456')

        assert result is False

    @patch('accounts.services.otp_service.requests.post')
    def test_send_sms_network_error(self, mock_post):
        """تست خطای شبکه در ارسال پیامک"""
        mock_post.side_effect = Exception("Network error")

        result = send_sms_via_asanak('09123456789', '123456')

        assert result is False