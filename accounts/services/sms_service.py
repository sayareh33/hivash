# accounts/services/sms_service.py
import requests
from django.conf import settings
from django.utils import timezone
from ..models import SMSLog, SMSProvider
import logging

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self.provider = self._get_active_provider()

    def _get_active_provider(self):
        """دریافت سرویس‌دهنده فعال"""
        try:
            return SMSProvider.objects.filter(is_active=True).order_by('priority').first()
        except SMSProvider.DoesNotExist:
            logger.error("No active SMS provider found")
            return None

    def send_verification_code(self, phone, code, message_type='verification', request=None):
        """ارسال کد تأیید"""
        if not self.provider:
            logger.error("Cannot send SMS: No active provider")
            return False

        # ایجاد لاگ
        sms_log = SMSLog.objects.create(
            provider=self.provider,
            phone=phone,
            message=f"کد تأیید شما: {code}",
            message_type=message_type,
            otp_code=code,
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
        )

        try:
            # ارسال واقعی پیامک
            if not settings.DEBUG:
                success, response = self._send_via_provider(phone, code)
            else:
                # در حالت توسعه
                logger.info(f"[DEBUG] SMS to {phone}: {code}")
                success, response = True, {"status": "debug_mode"}

            if success:
                sms_log.mark_as_sent(
                    message_id=response.get('message_id'),
                    cost=self.provider.cost_per_sms,
                    response=response
                )
                return True
            else:
                sms_log.mark_as_failed(response.get('error', 'Unknown error'))
                return False

        except Exception as e:
            logger.error(f"SMS sending failed for {phone}: {str(e)}")
            sms_log.mark_as_failed(str(e))
            return False

    def _send_via_provider(self, phone, code):
        """ارسال از طریق سرویس‌دهنده"""
        try:
            # اینجا باید با API سرویس‌دهنده ارتباط برقرار کنید
            # مثال برای آسانک:
            payload = {
                'username': self.provider.api_key,
                'password': getattr(settings, 'ASANAK_PASSWORD', ''),
                'source': getattr(settings, 'SMS_SENDER_NUMBER', ''),
                'destination': phone,
                'message': f'کد تأیید شما: {code}'
            }

            response = requests.post(self.provider.api_url, data=payload)
            response_data = response.json()

            if response_data.get('status') == '200':
                return True, response_data
            else:
                return False, response_data

        except Exception as e:
            logger.error(f"Provider SMS failed: {str(e)}")
            return False, {'error': str(e)}

    def _get_client_ip(self, request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip