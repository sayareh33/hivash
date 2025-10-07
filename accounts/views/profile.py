# accounts/views.py
from .services.phone_change_service import PhoneChangeService
from .services.sms_service import SMSService

# accounts/services/phone_change_service.py
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class PhoneChangeService:
    @staticmethod
    def request_phone_change(user, new_phone):
        """درخواست تغییر شماره تلفن"""
        try:
            # اعتبارسنجی شماره جدید
            from .validators import validate_iranian_mobile
            validated_phone = validate_iranian_mobile(new_phone)

            # بررسی اینکه شماره جدید با شماره فعلی متفاوت است
            if validated_phone == user.phone:
                return False, "شماره جدید نمی‌تواند با شماره فعلی یکسان باشد"

            # بررسی اینکه شماره جدید قبلاً استفاده نشده باشد
            from .models import User
            if User.objects.filter(phone=validated_phone).exclude(pk=user.pk).exists():
                return False, "این شماره قبلاً توسط کاربر دیگری ثبت شده است"

            # تولید OTP
            otp_code = f"{random.randint(0, 999999):06d}"

            # ذخیره اطلاعات تغییر
            user.new_phone = validated_phone
            user.phone_change_otp = otp_code
            user.phone_change_otp_created = timezone.now()
            user.phone_change_otp_attempts = 0
            user.save()

            # ارسال OTP به شماره جدید
            from .services.otp_service import send_sms_via_asanak
            success = send_sms_via_asanak(validated_phone, otp_code)

            if success:
                # ثبت در تاریخچه
                PhoneChangeHistory.objects.create(
                    user=user,
                    old_phone=user.phone,
                    new_phone=validated_phone,
                    status='pending'
                )
                return True, "کد تأیید به شماره جدید ارسال شد"
            else:
                # بازنشانی در صورت شکست در ارسال
                user.new_phone = None
                user.phone_change_otp = None
                user.phone_change_otp_created = None
                user.save()
                return False, "خطا در ارسال کد تأیید"

        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Phone change request failed for user {user.pk}: {str(e)}")
            return False, "خطا در پردازش درخواست"

    @staticmethod
    def verify_phone_change(user, otp_code):
        """تأیید تغییر شماره تلفن با OTP"""
        try:
            # بررسی وجود درخواست تغییر
            if not user.new_phone or not user.phone_change_otp:
                return False, "درخواست تغییر شماره یافت نشد"

            # بررسی انقضای OTP
            if timezone.now() > user.phone_change_otp_created + timedelta(minutes=10):
                return False, "کد تأیید منقضی شده است"

            # بررسی تطابق OTP
            if str(otp_code).strip() != str(user.phone_change_otp).strip():
                user.phone_change_otp_attempts += 1

                # بررسی تعداد تلاش‌های ناموفق
                if user.phone_change_otp_attempts >= 3:
                    user.new_phone = None
                    user.phone_change_otp = None
                    user.phone_change_otp_created = None
                    user.save()
                    return False, "تعداد تلاش‌های شما بیش از حد مجاز است"

                user.save()
                return False, "کد تأیید نامعتبر است"

            # تغییر شماره تلفن
            old_phone = user.phone
            user.phone = user.new_phone
            user.new_phone = None
            user.phone_change_otp = None
            user.phone_change_otp_created = None
            user.phone_change_otp_attempts = 0
            user.is_phone_verified = True
            user.save()

            # به‌روزرسانی تاریخچه
            change_history = PhoneChangeHistory.objects.filter(
                user=user,
                new_phone=user.phone,
                status='pending'
            ).latest('created_at')
            change_history.status = 'verified'
            change_history.verified_at = timezone.now()
            change_history.save()

            return True, "شماره تلفن با موفقیت تغییر کرد"

        except Exception as e:
            logger.error(f"Phone change verification failed for user {user.pk}: {str(e)}")
            return False, "خطا در تأیید تغییر شماره"



@login_required
def request_phone_change(request):
    if request.method == 'POST':
        new_phone = request.POST.get('new_phone')

        success, message = PhoneChangeService.request_phone_change(request.user, new_phone)

        if success:
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'message': message}, status=400)

@login_required
def verify_phone_change(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')

        success, message = PhoneChangeService.verify_phone_change(request.user, otp_code)

        if success:
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'message': message}, status=400)