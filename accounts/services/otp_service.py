# accounts/services/otp_service.py
import secrets

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError
import json

class OTPService:
    """سرویس مدیریت امن OTP"""

    OTP_LENGTH = 6
    OTP_EXPIRY = 300  # 5 دقیقه
    MAX_ATTEMPTS = 3

    @classmethod
    def generate_otp(cls):
        """تولید کد OTP امن"""
        return secrets.randbelow(10 ** cls.OTP_LENGTH)

    @classmethod
    def store_otp(cls, phone, otp):
        """ذخیره امن OTP در کش"""
        cache_key = f"otp_{phone}"
        cache_data = {
            'code': otp,
            'created_at': timezone.now().isoformat(),
            'attempts': 0
        }
        cache.set(cache_key, cache_data, cls.OTP_EXPIRY)

    @classmethod
    def verify_otp(cls, phone, submitted_otp):
        """اعتبارسنجی OTP با مدیریت تلاش‌های ناموفق"""
        cache_key = f"otp_{phone}"
        otp_data = cache.get(cache_key)

        if not otp_data:
            raise ValidationError('کد تأیید منقضی شده یا وجود ندارد.')

        # بررسی تعداد تلاش‌ها
        if otp_data['attempts'] >= cls.MAX_ATTEMPTS:
            cache.delete(cache_key)
            raise ValidationError('تعداد تلاش‌های شما بیش از حد مجاز است. لطفاً کد جدیدی دریافت کنید.')

        # بررسی تطابق کد
        if str(otp_data['code']) != str(submitted_otp):
            # افزایش شمارنده تلاش‌های ناموفق
            otp_data['attempts'] += 1
            cache.set(cache_key, otp_data, cls.OTP_EXPIRY)

            remaining_attempts = cls.MAX_ATTEMPTS - otp_data['attempts']
            raise ValidationError(f'کد تأیید نامعتبر است. شما {remaining_attempts} تلاش باقی مانده دارید.')

        # حذف OTP پس از تأیید موفق
        cache.delete(cache_key)
        return True

def send_sms_via_asanak(phone, otp_code):
    url = "https://sms.asanak.ir/webservice/v2rest/sendsms"
    headers = {"Content-Type": "hivashop/x-www-form-2658f80dffb2ebe813528bd487570be2c548af948007512e30a2d92359a7664a"}
    payload = {
        "username": 'hivashop',
        "password": 'YaZahra79$',
        "template_id": '1685',
        "source": "۹۸۲۱۷۰۰۰۰۹۳۳۲۱۴۷۲۶",
        "destination": f"98{phone}",
        "message": "کد تایید شما {{otp_code}} آزمایش هیوا",
    }

    response = requests.request("POST", url, data=payload, timeout=5)
    print(response.text.encode('utf8'))

