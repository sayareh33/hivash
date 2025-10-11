import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
from accounts.models import CustomUser


class TestSignUpView(TestCase):
    """تست‌های ویو ثبت‌نام"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:signup')
        self.valid_data = {
            'phone': '09123456789',
            'password': 'TestPass123!',
            'email': 'test@example.com'
        }

    def test_signup_get_request(self):
        """تست درخواست GET به صفحه ثبت‌نام"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')
        self.assertContains(response, 'form')

    @patch('accounts.models.CustomUser.send_otp')
    def test_signup_success(self, mock_send_otp):
        """تست ثبت‌نام موفق"""
        mock_send_otp.return_value = True

        response = self.client.post(self.url, self.valid_data)

        # باید به صفحه تأیید OTP ریدایرکت شود
        self.assertRedirects(response, reverse('accounts:verify_otp'))

        # کاربر باید ایجاد شده باشد
        user = CustomUser.objects.get(phone='09123456789')
        self.assertFalse(user.is_active)  # تا تأیید OTP غیرفعال

        # باید در session ذخیره شده باشد
        self.assertEqual(self.client.session['pending_user_id'], user.id)

        # پیام موفقیت باید نمایش داده شود
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('کد تأیید ارسال شد' in str(message) for message in messages))

    def test_signup_existing_active_user(self):
        """تست ثبت‌نام با شماره تلفن تکراری"""
        # ایجاد کاربر فعال
        CustomUser.objects.create_user(
            phone='09123456789',
            password='TestPass123!'
        )

        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'phone', 'این شماره تلفن قبلاً ثبت شده است.')

    @patch('accounts.models.CustomUser.send_otp')
    def test_signup_otp_send_failure(self, mock_send_otp):
        """تست شکست در ارسال OTP"""
        mock_send_otp.side_effect = Exception("SMS sending failed")

        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'ارسال کد تأیید با خطا مواجه شد.')

        # کاربر موقت باید حذف شده باشد
        self.assertEqual(CustomUser.objects.filter(phone='09123456789').count(), 0)

    def test_signup_invalid_data(self):
        """تست ثبت‌نام با داده‌های نامعتبر"""
        invalid_data = {
            'phone': 'invalid',
            'password': '123'
        }

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


class TestVerifyOTPView(TestCase):
    """تست‌های ویو تأیید OTP"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:verify_otp')

        # ایجاد کاربر موقت
        self.temp_user = CustomUser.objects.create_user(
            phone='09123456789',
            password='TestPass123!',
            is_active=False
        )

        # تنظیم session
        session = self.client.session
        session['pending_user_id'] = self.temp_user.id
        session.save()

    def test_verify_otp_get_request(self):
        """تست درخواست GET به صفحه تأیید OTP"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/verify_otp.html')

    def test_verify_otp_get_without_session(self):
        """تست درخواست GET بدون session معتبر"""
        client = Client()  # کلینت بدون session
        response = client.get(self.url)

        self.assertRedirects(response, reverse('accounts:signup'))

    @patch('accounts.models.CustomUser.verify_otp')
    def test_verify_otp_success(self, mock_verify_otp):
        """تست تأیید موفق OTP"""
        mock_verify_otp.return_value = (True, "تأیید موفق")

        response = self.client.post(self.url, {'otp_code': '123456'})

        # باید به صفحه اصلی ریدایرکت شود
        self.assertRedirects(response, reverse('pages:home'))

        # کاربر باید لاگین شده باشد
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # session باید پاک شده باشد
        self.assertNotIn('pending_user_id', self.client.session)

        # کاربر باید فعال شده باشد
        self.temp_user.refresh_from_db()
        self.assertTrue(self.temp_user.is_active)

    @patch('accounts.models.CustomUser.verify_otp')
    def test_verify_otp_wrong_code(self, mock_verify_otp):
        """تست تأیید کد نادرست"""
        mock_verify_otp.return_value = (False, "کد OTP نامعتبر است")

        response = self.client.post(self.url, {'otp_code': '000000'})

        self.assertRedirects(response, reverse('accounts:verify_otp'))

        # پیام خطا باید نمایش داده شود
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('نامعتبر' in str(message) for message in messages))

    @patch('accounts.models.CustomUser.verify_otp')
    def test_verify_otp_account_locked(self, mock_verify_otp):
        """تست قفل شدن حساب پس از تلاش‌های زیاد"""
        mock_verify_otp.return_value = (False, "حساب قفل شده است")

        response = self.client.post(self.url, {'otp_code': '000000'})

        self.assertRedirects(response, reverse('accounts:signup'))

        # session باید پاک شده باشد
        self.assertNotIn('pending_user_id', self.client.session)

    def test_verify_otp_invalid_code_length(self):
        """تست کد OTP با طول نامعتبر"""
        response = self.client.post(self.url, {'otp_code': '123'})

        self.assertRedirects(response, reverse('accounts:verify_otp'))

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('۶ رقمی' in str(message) for message in messages))

    def test_verify_otp_user_not_found(self):
        """تست زمانی که کاربر در session وجود ندارد"""
        # پاک کردن کاربر از دیتابیس
        self.temp_user.delete()

        response = self.client.post(self.url, {'otp_code': '123456'})

        self.assertRedirects(response, reverse('accounts:signup'))

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('کاربر یافت نشد' in str(message) for message in messages))