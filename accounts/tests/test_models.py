import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from accounts.models import CustomUser, UserManager, validate_iranian_mobile


class TestCustomUserModel:
    """تست‌های جامع برای مدل CustomUser"""

    @pytest.fixture
    def user_data(self):
        return {
            'phone': '09123456789',
            'password': 'TestPass123!'
        }

    def test_create_user_success(self, user_data):
        """تست ایجاد کاربر عادی"""
        user = CustomUser.objects.create_user(**user_data)

        assert user.phone == '09123456789'
        assert user.check_password('TestPass123!')
        assert user.is_active == True
        assert user.is_staff == False
        assert user.is_superuser == False
        assert user.is_phone_verified == False

    def test_create_user_without_phone(self):
        """تست ایجاد کاربر بدون شماره تلفن"""
        with pytest.raises(ValueError, match='شماره همراه الزامی است'):
            CustomUser.objects.create_user(phone=None, password='test123')

    def test_create_user_without_password(self):
        """تست ایجاد کاربر بدون رمز عبور"""
        with pytest.raises(ValueError, match='رمز عبور الزامی است'):
            CustomUser.objects.create_user(phone='09123456789', password=None)

    def test_create_superuser(self):
        """تست ایجاد سوپر کاربر"""
        superuser = CustomUser.objects.create_superuser(
            phone='09123456789',
            password='admin123'
        )

        assert superuser.is_superuser == True
        assert superuser.is_staff == True
        assert superuser.is_active == True
        assert superuser.is_phone_verified == True

    def test_phone_validation(self):
        """تست اعتبارسنجی شماره تلفن"""
        # شماره معتبر
        valid_phones = ['09123456789', '+989123456789', '۹۱۲۳۴۵۶۷۸۹']
        for phone in valid_phones:
            assert validate_iranian_mobile(phone) == '9123456789'

        # شماره نامعتبر
        invalid_phones = ['123456789', '0912345678', '091234567890', 'test']
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                validate_iranian_mobile(phone)

    def test_clean_method(self):
        """تست متد clean برای اعتبارسنجی"""
        user = CustomUser(phone='09123456789')
        user.clean()  # باید بدون خطا اجرا شود

        user.phone = 'invalid'
        with pytest.raises(ValidationError):
            user.clean()

    @patch('accounts.models.timezone.now')
    def test_generate_otp(self, mock_now, user_data):
        """تست تولید کد OTP"""
        mock_now.return_value = timezone.datetime(2023, 1, 1, 12, 0, 0)
        user = CustomUser.objects.create_user(**user_data)

        otp = user.generate_otp()

        assert len(otp) == 5
        assert otp.isdigit()
        assert user.otp_code == otp
        assert user.otp_created_at == mock_now.return_value
        assert user.otp_attempts == 0

    @patch('accounts.models.timezone.now')
    def test_verify_otp_success(self, mock_now, user_data):
        """تست تأیید موفق OTP"""
        mock_now.return_value = timezone.datetime(2023, 1, 1, 12, 0, 0)
        user = CustomUser.objects.create_user(**user_data)
        user.generate_otp()

        is_verified, message = user.verify_otp(user.otp_code)

        assert is_verified == True
        assert "موفق" in message
        assert user.is_phone_verified == True
        assert user.otp_code is None

    def test_verify_otp_wrong_code(self, user_data):
        """تست تأیید کد OTP نادرست"""
        user = CustomUser.objects.create_user(**user_data)
        user.generate_otp()

        is_verified, message = user.verify_otp('00000')

        assert is_verified == False
        assert "نامعتبر" in message
        assert user.otp_attempts == 1

    def test_verify_otp_max_attempts(self, user_data):
        """تست قفل شدن حساب پس از تلاش‌های زیاد"""
        user = CustomUser.objects.create_user(**user_data)
        user.generate_otp()

        # تلاش‌های متعدد با کد اشتباه
        for _ in range(3):
            user.verify_otp('00000')

        assert user.is_locked == True
        assert user.locked_until is not None

    @patch('accounts.models.timezone.now')
    def test_is_otp_expired(self, mock_now, user_data):
        """تست انقضای کد OTP"""
        mock_now.return_value = timezone.datetime(2023, 1, 1, 12, 0, 0)
        user = CustomUser.objects.create_user(**user_data)
        user.generate_otp()

        # شبیه‌سازی گذشت زمان بیش از 5 دقیقه
        mock_now.return_value = timezone.datetime(2023, 1, 1, 12, 6, 0)

        assert user.is_otp_expired() == True

    def test_account_lock_unlock(self, user_data):
        """تست قفل و باز شدن حساب"""
        user = CustomUser.objects.create_user(**user_data)

        user.lock_account(minutes=30)
        assert user.is_locked == True

        user.unlock_account()
        assert user.is_locked == False
        assert user.otp_attempts == 0
        assert user.login_attempts == 0

    def test_string_representation(self, user_data):
        """تست نمایش رشته‌ای مدل"""
        user = CustomUser.objects.create_user(**user_data)
        assert str(user) == '09123456789'

    def test_get_full_name_with_profile(self, user_data):
        """تست نام کامل کاربر با پروفایل"""
        user = CustomUser.objects.create_user(**user_data)

        # شبیه‌سازی وجود پروفایل
        class MockProfile:
            def get_full_name(self):
                return "John Doe"

        user.profile = MockProfile()
        assert user.get_full_name() == "John Doe"

        # بدون پروفایل
        user.profile = None
        assert user.get_full_name() == user.phone