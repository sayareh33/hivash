# accounts/services/otp_service.py
import secrets
import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
import logging

from config.settings import ASANAK_USERNAME, ASANAK_PASSWORD, ASANAK_SOURCE

logger = logging.getLogger(__name__)
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

# def send_sms_via_asanak(phone, otp_code):
#     url = "https://sms.asanak.ir/webservice/v2rest/sendsms"
#     headers = {"Content-Type": "hivashop/x-www-form-2658f80dffb2ebe813528bd487570be2c548af948007512e30a2d92359a7664a"}
#     payload = {
#         "username": 'hivashop',
#         "password": 'YaZahra79$',
#         "template_id": '1685',
#         "source": "۹۸۲۱۷۰۰۰۰۹۳۳۲۱۴۷۲۶",
#         "destination": f"98{phone}",
#         "message": "کد تایید شما {{otp_code}} آزمایش هیوا",
#     }
#
#     response = requests.request("POST", url, data=payload, timeout=5)
#     print(response.text.encode('utf8'))


def send_sms_via_asanak(phone, otp_code):
    # در بالای فایل services/otp_service.py

    """
    سرویس ارسال پیامک از طریق آسانک

    مستندات API آسانک:
    - URL: https://sms.asanak.ir/webservice/v2rest/sendsms
    - Method: POST
    - Content-Type: application/x-www-form-urlencoded
    - پارامترهای ضروری:
      * username: نام کاربری
      * password: رمز عبور
      * source: شماره فرستنده
      * destination: شماره مقصد (با 98 شروع شود)
      * message: متن پیام

    نکات مهم:
    1. شماره مقصد باید بدون صفر ابتدایی و با پیشوند 98 ارسال شود
    2. متن پیام باید حاوی کد تأیید باشد
    3. timeout ارتباط 10 ثانیه در نظر گرفته شده
    4. خطاها به طور کامل لاگ می‌شوند
    """
    url = "https://sms.asanak.ir/webservice/v2rest/sendsms"

    # هدر صحیح
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    payload = {
        "username": ASANAK_USERNAME,  # بهتر است از settings استفاده شود
        "password": ASANAK_PASSWORD,  # بسیار خطرناک - از متغیر محیطی استفاده شود
        "template_id": '1685',
        "source": ASANAK_SOURCE,  # فقط اعداد
        "destination": f"98{phone}",
        "message": f"کد تایید شما {otp_code} آزمایش هیوا",
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()  # بررسی خطای HTTP
        print(response.text.encode('utf8'))

        # بررسی پاسخ آسانک
        response_data = response.text
        logger.info(f"Asanak response for {phone}: {response_data}")

        # بررسی پاسخ آسانک
        if response.json().get('status') != '0':
            logger.error(f"Asanak API error: {response.text}")
            return False

        logger.info(f"SMS sent to {phone} successfully")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"SMS sending failed for {phone}: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error in SMS sending for {phone}: {str(e)}")
        return False

