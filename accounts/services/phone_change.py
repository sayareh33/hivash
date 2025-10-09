# accounts/services/phone_change.py
import random

from django.utils import timezone
from datetime import timedelta

from environs import ValidationError

from accounts.services.otp_service import send_sms_via_asanak


class PhoneChangeService:
    @staticmethod
    def request_phone_change(user, new_phone):
        """درخواست تغییر شماره تلفن"""
        from accounts.validators import validate_iranian_mobile

        try:
            # اعتبارسنجی شماره جدید
            validated_phone = validate_iranian_mobile(new_phone)

            # بررسی اینکه شماره جدید با شماره فعلی متفاوت است
            if validated_phone == user.phone:
                return False, "شماره جدید با شماره فعلی یکسان است"

            # بررسی اینکه شماره جدید قبلاً استفاده نشده باشد
            from accounts.models import CustomUser
            if CustomUser.objects.filter(phone=validated_phone).exists():
                return False, "این شماره قبلاً توسط کاربر دیگری ثبت شده است"

            # ذخیره شماره جدید و تولید OTP
            user.new_phone = validated_phone
            user.phone_change_otp = str(random.randint(100000, 999999))
            user.phone_change_otp_created = timezone.now()
            user.phone_change_otp_attempts = 0
            user.save()

            # ارسال OTP
            success, message = send_sms_via_asanak(validated_phone, user.phone_change_otp)

            if success:
                return True, "کد تأیید به شماره جدید ارسال شد"
            else:
                # در صورت شکست در ارسال پیامک، اطلاعات را پاک کنید
                user.new_phone = None
                user.phone_change_otp = None
                user.phone_change_otp_created = None
                user.save()
                return False, f"خطا در ارسال پیامک: {message}"

        except ValidationError as e:
            return False, str(e)

    @staticmethod
    def verify_phone_change(user, otp_code):
        """تأیید تغییر شماره تلفن"""
        # بررسی انقضای OTP
        if user.phone_change_otp_created < timezone.now() - timedelta(minutes=10):
            return False, "کد تأیید منقضی شده است"

        # بررسی تعداد تلاش‌های ناموفق
        if user.phone_change_otp_attempts >= 3:
            return False, "تعداد تلاش‌های شما بیش از حد مجاز است"

        # بررسی تطابق OTP
        if user.phone_change_otp != otp_code:
            user.phone_change_otp_attempts += 1
            user.save()
            return False, "کد تأیید نامعتبر است"

        # تغییر شماره تلفن
        old_phone = user.phone
        user.phone = user.new_phone
        user.new_phone = None
        user.phone_change_otp = None
        user.phone_change_otp_created = None
        user.phone_change_otp_attempts = 0
        user.save()

        # ثبت در تاریخچه تغییرات
        from accounts.models import PhoneChangeHistory
        PhoneChangeHistory.objects.create(
            user=user,
            old_phone=old_phone,
            new_phone=user.phone,
            verified=True
        )

        return True, "شماره تلفن با موفقیت تغییر کرد"