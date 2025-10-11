from django.db import models
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django.conf import settings
from datetime import timedelta
import random
import logging

from accounts.validators import validate_iranian_mobile
from accounts.services.otp_service import send_sms_via_asanak

logger = logging.getLogger(__name__)

# ØªÙ†Ø¸ÛŒÙ…Ø§Øª
OTP_EXPIRE_MINUTES = getattr(settings, 'OTP_EXPIRE_MINUTES', 5)
OTP_MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
LOGIN_MAX_ATTEMPTS = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Ø´Ù…Ø§Ø±Ù‡ Ù‡Ù…Ø±Ø§Ù‡ Ø§Ù„Ø²Ø§Ù…ÛŒ Ø§Ø³Øª')

        if not password:
            raise ValueError('Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø§Ù„Ø²Ø§Ù…ÛŒ Ø§Ø³Øª')

        user = self.model(
            phone=phone,
            is_staff=extra_fields.pop('is_staff', False),
            is_active=extra_fields.pop('is_active', True),
            is_superuser=extra_fields.pop('is_superuser', False),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(
        max_length=15,
        unique=True,
        verbose_name=_('Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†'),
        validators=[validate_iranian_mobile]
    )

    # ÙÛŒÙ„Ø¯Ù‡Ø§ÛŒ Ø§ØµÙ„ÛŒ
    password = models.CharField(_('Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±'), max_length=128, blank=False, null=False)
    email = models.EmailField(_('Ø§ÛŒÙ…ÛŒÙ„'), blank=True, null=True)
    is_active = models.BooleanField(_('ÙØ¹Ø§Ù„'), default=True)
    is_staff = models.BooleanField(_('Ú©Ø§Ø±Ù…Ù†Ø¯'), default=False)
    is_superuser = models.BooleanField(_('Ú©Ø§Ø±Ø¨Ø± Ø¨Ø±ØªØ±'), default=False)

    date_joined = models.DateTimeField(_('ØªØ§Ø±ÛŒØ® Ø¹Ø¶ÙˆÛŒØª'), auto_now_add=True)

    # ÙÛŒÙ„Ø¯Ù‡Ø§ÛŒ ØªØ£ÛŒÛŒØ¯
    is_phone_verified = models.BooleanField(_('ØªÙ„ÙÙ† ØªØ£ÛŒÛŒØ¯ Ø´Ø¯Ù‡'), default=False)

    # ÙÛŒÙ„Ø¯Ù‡Ø§ÛŒ Ø§Ù…Ù†ÛŒØªÛŒ
    otp_code = models.CharField(max_length=5, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveIntegerField(default=0)
    login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)


#______________change phone_________
    new_phone = models.CharField(
        max_length=15, unique=True, null=True, blank=True, validators=[validate_iranian_mobile],
        verbose_name=_('Ø´Ù…Ø§Ø±Ù‡ Ø¬Ø¯ÛŒØ¯ (Ø¯Ø± Ø§Ù†ØªØ¸Ø§Ø± ØªØ£ÛŒÛŒØ¯)'))

    # OTP Ø¨Ø±Ø§ÛŒ ØªØ£ÛŒÛŒØ¯ Ø´Ù…Ø§Ø±Ù‡ Ø¬Ø¯ÛŒØ¯
    phone_change_otp = models.CharField(max_length=6, null=True, blank=True)
    phone_change_otp_created = models.DateTimeField(null=True, blank=True)
    phone_change_otp_attempts = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['password']

    class Meta:
        verbose_name = _('Ú©Ø§Ø±Ø¨Ø±')
        verbose_name_plural = _('Ú©Ø§Ø±Ø¨Ø±Ø§Ù†')
        db_table = 'accounts_customuser'

    def __str__(self):
        return self.phone

    def clean(self):
        """Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ù…Ø¯Ù„ Ù‚Ø¨Ù„ Ø§Ø² Ø°Ø®ÛŒØ±Ù‡"""
        super().clean()

        # Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
        try:
            self.phone = validate_iranian_mobile(self.phone)
        except ValidationError as e:
            raise ValidationError({'phone': e.messages})

    def save(self, *args, **kwargs):
        """Ø°Ø®ÛŒØ±Ù‡ Ú©Ø§Ø±Ø¨Ø± Ø¨Ø§ Ø§Ø¹Ù…Ø§Ù„ Ù…Ù†Ø·Ù‚ Ù…ÙˆØ±Ø¯ Ù†ÛŒØ§Ø²"""
        self.clean()

        # Ø§Ú¯Ø± Ú©Ø§Ø±Ø¨Ø± Ø³ÙˆÙ¾Ø±ÛŒÙˆØ²Ø± Ø§Ø³ØªØŒ ØªØ£ÛŒÛŒØ¯ ØªÙ„ÙÙ† Ø±Ø§ ØªÙ†Ø¸ÛŒÙ… Ú©Ù†
        if self.is_superuser:
            self.is_phone_verified = True
            self.bypass_phone_verification = True

        super().save(*args, **kwargs)

    def get_full_name(self):
        if hasattr(self, 'profile'):
            return self.profile.get_full_name()
        return self.phone

    def get_short_name(self):
        if hasattr(self, 'profile') and self.profile.first_name:
            return self.profile.first_name
        return self.phone

    # Ù…ØªØ¯Ù‡Ø§ÛŒ OTP
    def generate_otp(self):
        """ØªÙˆÙ„ÛŒØ¯ Ùˆ Ø°Ø®ÛŒØ±Ù‡ Ú©Ø¯ OTP Ø¨Ø§ Ù…Ø¯ÛŒØ±ÛŒØª Ø®Ø·Ø§"""
        try:
            # ØªÙˆÙ„ÛŒØ¯ Ú©Ø¯ Û¶ Ø±Ù‚Ù…ÛŒ
            otp_code = f"{random.randint(0, 99999):05d}"

            # Ø¨Ù‡â€ŒØ±ÙˆØ²Ø±Ø³Ø§Ù†ÛŒ ÙÛŒÙ„Ø¯Ù‡Ø§
            self.otp_code = otp_code
            self.otp_created_at = timezone.now()
            self.otp_attempts = 0

            # Ø°Ø®ÛŒØ±Ù‡ Ø¯Ø± Ø¯ÛŒØªØ§Ø¨ÛŒØ³
            if self.pk:  # Ú©Ø§Ø±Ø¨Ø± Ø§Ø² Ù‚Ø¨Ù„ Ø¯Ø± Ø¯ÛŒØªØ§Ø¨ÛŒØ³ ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø±Ø¯
                self.save(update_fields=['otp_code', 'otp_created_at', 'otp_attempts'])
            else:  # Ú©Ø§Ø±Ø¨Ø± Ø¬Ø¯ÛŒØ¯
                self.save()  # Ø°Ø®ÛŒØ±Ù‡ Ø§ÙˆÙ„ÛŒÙ‡

            logger.info(f"OTP generated for user {self.phone}")
            return otp_code

        except Exception as e:
            logger.error(f"Failed to generate OTP for {self.phone}: {str(e)}")
            raise

    def send_otp(self):
        try:
            otp_code = self.generate_otp()
            success = send_sms_via_asanak(self.phone, otp_code)

            if not success:
                # راه‌حل جایگزین برای ارسال پیامک
                logger.error(f"Failed to send OTP to {self.phone}")
                return False

            return True

        except Exception as e:
            logger.error(f"OTP sending exception for {self.phone}: {str(e)}")
            return False

    def verify_otp(self, code):
        """ØªØ£ÛŒÛŒØ¯ OTP"""
        if self.is_locked:
            return False, "Ø­Ø³Ø§Ø¨ Ù‚ÙÙ„ Ø´Ø¯Ù‡ Ø§Ø³Øª"

        if not self.otp_code or not self.otp_created_at:
            return False, "Ú©Ø¯ OTP ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø±Ø¯"

        if self.is_otp_expired():
            return False, "Ú©Ø¯ OTP Ù…Ù†Ù‚Ø¶ÛŒ Ø´Ø¯Ù‡ Ø§Ø³Øª"

        if str(code).strip() == str(self.otp_code).strip():
            self.otp_code = None
            self.otp_created_at = None
            self.otp_attempts = 0
            self.is_phone_verified = True
            self.save()
            return True, "ØªØ£ÛŒÛŒØ¯ Ù…ÙˆÙÙ‚"
        else:
            self.otp_attempts += 1
            if self.otp_attempts >= OTP_MAX_ATTEMPTS:
                self.lock_account()
            self.save()
            return False, "Ú©Ø¯ OTP Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª"

    def is_otp_expired(self):
        """Ø¨Ø±Ø±Ø³ÛŒ Ø§Ù†Ù‚Ø¶Ø§ÛŒ OTP"""
        if not self.otp_created_at:
            return True
        return timezone.now() > self.otp_created_at + timedelta(minutes=OTP_EXPIRE_MINUTES)

    @property
    def is_locked(self):
        """Ø¨Ø±Ø±Ø³ÛŒ Ù‚ÙÙ„ Ø¨ÙˆØ¯Ù† Ø­Ø³Ø§Ø¨"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        elif self.locked_until and timezone.now() >= self.locked_until:
            self.unlock_account()
            return False
        return False

    def lock_account(self, minutes=30):
        """Ù‚ÙÙ„ Ú©Ø±Ø¯Ù† Ø­Ø³Ø§Ø¨"""
        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save()

    def unlock_account(self):
        """Ø¨Ø§Ø² Ú©Ø±Ø¯Ù† Ù‚ÙÙ„ Ø­Ø³Ø§Ø¨"""
        self.locked_until = None
        self.otp_attempts = 0
        self.login_attempts = 0
        self.save()

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField( User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('Ú©Ø§Ø±Ø¨Ø±'))

    # Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ø´Ø®ØµÛŒ
    first_name = models.CharField(_('Ù†Ø§Ù…'), max_length=100, blank=True)
    last_name = models.CharField(_('Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ'), max_length=100, blank=True)
    national_code = models.CharField(_('Ú©Ø¯ Ù…Ù„ÛŒ'), max_length=10, blank=True)
    birth_date = models.DateField(_('ØªØ§Ø±ÛŒØ® ØªÙˆÙ„Ø¯'), null=True, blank=True)

    # Ø§Ø·Ù„Ø§Ø¹Ø§Øª ØªÙ…Ø§Ø³
    email = models.EmailField(_('Ø§ÛŒÙ…ÛŒÙ„'), blank=True, null=True)
    phone = models.CharField(_('ØªÙ„ÙÙ† Ø«Ø§Ø¨Øª'), max_length=15, blank=True, validators=[validate_iranian_mobile])
    emergency_contact = models.CharField(_('Emergency contact'), max_length=20, blank=True, null=True)

    # Ø¢Ø¯Ø±Ø³
    country = CountryField(_('Country'), blank=True, null=True)
    province = models.CharField(_('Ø§Ø³ØªØ§Ù†'), max_length=100, blank=True)
    city = models.CharField(_('Ø´Ù‡Ø±'), max_length=100, blank=True)
    address = models.TextField(_('Ø¢Ø¯Ø±Ø³'), blank=True)
    postal_code = models.CharField(_('Ú©Ø¯ Ù¾Ø³ØªÛŒ'), max_length=10, blank=True)

    # ØªÙ†Ø¸ÛŒÙ…Ø§Øª
    email_notifications = models.BooleanField(_('Ø§Ø¹Ù„Ø§Ù† Ø§ÛŒÙ…ÛŒÙ„ÛŒ'), default=True)
    sms_notifications = models.BooleanField(_('Ø§Ø¹Ù„Ø§Ù† Ù¾ÛŒØ§Ù…Ú©ÛŒ'), default=True)

    created_at = models.DateTimeField(_('ØªØ§Ø±ÛŒØ® Ø§ÛŒØ¬Ø§Ø¯'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ø¢Ø®Ø±ÛŒÙ† Ø¨Ø±ÙˆØ²Ø±Ø³Ø§Ù†ÛŒ'), auto_now=True)

    class Meta:
        verbose_name = _('Ù¾Ø±ÙˆÙØ§ÛŒÙ„ Ú©Ø§Ø±Ø¨Ø±')
        verbose_name_plural = _('Ù¾Ø±ÙˆÙØ§ÛŒÙ„ Ú©Ø§Ø±Ø¨Ø±Ø§Ù†')

    def __str__(self):
        return f"{self.user.phone} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_complete(self):
        """Ø¨Ø±Ø±Ø³ÛŒ Ú©Ø§Ù…Ù„ Ø¨ÙˆØ¯Ù† Ù¾Ø±ÙˆÙØ§ÛŒÙ„ Ø¨Ø±Ø§ÛŒ Ø®Ø±ÛŒØ¯"""
        required_fields = ['first_name', 'last_name', 'province', 'city', 'address', 'postal_code']
        return all(bool(getattr(self, field)) for field in required_fields)

    class Address(models.Model):
        """Ù…Ø¯Ù„ Ø¢Ø¯Ø±Ø³ Ø¨Ø±Ø§ÛŒ Ú©Ø§Ø±Ø¨Ø±Ø§Ù† (Ø§Ú¯Ø± Ù†ÛŒØ§Ø² Ø¨Ù‡ Ú†Ù†Ø¯ Ø¢Ø¯Ø±Ø³ Ø¯Ø§Ø±ÛŒØ¯)"""
        user = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='addresses',
            verbose_name=_('Ú©Ø§Ø±Ø¨Ø±')
        )

        title = models.CharField(_('Ø¹Ù†ÙˆØ§Ù† Ø¢Ø¯Ø±Ø³'), max_length=100)
        first_name = models.CharField(_('Ù†Ø§Ù…'), max_length=100)
        last_name = models.CharField(_('Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ'), max_length=100)
        phone = models.CharField(_('ØªÙ„ÙÙ†'), max_length=15, validators=[validate_iranian_mobile])
        province = models.CharField(_('Ø§Ø³ØªØ§Ù†'), max_length=100)
        city = models.CharField(_('Ø´Ù‡Ø±'), max_length=100)
        address = models.TextField(_('Ø¢Ø¯Ø±Ø³'))
        postal_code = models.CharField(_('Ú©Ø¯ Ù¾Ø³ØªÛŒ'), max_length=10)
        is_default = models.BooleanField(_('Ù¾ÛŒØ´â€ŒÙØ±Ø¶'), default=False)

        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        class Meta:
            verbose_name = _('Ø¢Ø¯Ø±Ø³')
            verbose_name_plural = _('Ø¢Ø¯Ø±Ø³â€ŒÙ‡Ø§')
            ordering = ['-is_default', '-created_at']

        def __str__(self):
            return f"{self.title} - {self.user.phone}"

class LoginHistory(models.Model):
    """ØªØ§Ø±ÛŒØ®Ú†Ù‡ ÙˆØ±ÙˆØ¯"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    login_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('ØªØ§Ø±ÛŒØ®Ú†Ù‡ ÙˆØ±ÙˆØ¯')
        verbose_name_plural = _('ØªØ§Ø±ÛŒØ®Ú†Ù‡ ÙˆØ±ÙˆØ¯Ù‡Ø§')
        ordering = ['-login_at']


class PhoneChangeHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ø¯Ø± Ø§Ù†ØªØ¸Ø§Ø± ØªØ£ÛŒÛŒØ¯'),
        ('verified', 'ØªØ£ÛŒÛŒØ¯ Ø´Ø¯Ù‡'),
        ('expired', 'Ù…Ù†Ù‚Ø¶ÛŒ Ø´Ø¯Ù‡'),
        ('cancelled', 'Ù„ØºÙˆ Ø´Ø¯Ù‡'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='phone_change_history'
    )
    old_phone = models.CharField(max_length=15, validators=[validate_iranian_mobile])
    new_phone = models.CharField(max_length=15, validators=[validate_iranian_mobile])
    otp_code = models.CharField(max_length=6)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'ØªØ§Ø±ÛŒØ®Ú†Ù‡ ØªØºÛŒÛŒØ± Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†'
        verbose_name_plural = 'ØªØ§Ø±ÛŒØ®Ú†Ù‡ ØªØºÛŒÛŒØ±Ø§Øª Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†'
        ordering = ['-created_at']

class SMSLog(models.Model):
    """Ù„Ø§Ú¯ Ù¾ÛŒØ§Ù…Ú©"""
    phone = models.CharField(max_length=15, validators=[validate_iranian_mobile])
    code = models.CharField(max_length=6)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sending')

    class Meta:
        verbose_name = _('Ù„Ø§Ú¯ Ù¾ÛŒØ§Ù…Ú©')
        verbose_name_plural = _('Ù„Ø§Ú¯â€ŒÙ‡Ø§ÛŒ Ù¾ÛŒØ§Ù…Ú©')
        ordering = ['-created_at']

