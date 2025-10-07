from django.db import models
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import timedelta
import random
import logging

from accounts.validators import validate_iranian_mobile
from accounts.services.otp_service import send_sms_via_asanak

logger = logging.getLogger(__name__)

# تنظیمات
OTP_EXPIRE_MINUTES = getattr(settings, 'OTP_EXPIRE_MINUTES', 5)
OTP_MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
LOGIN_MAX_ATTEMPTS = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('شماره همراه الزامی است')

        if not password:
            raise ValueError('رمز عبور الزامی است')

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
        verbose_name=_('شماره تلفن'),
        validators=[validate_iranian_mobile]
    )

    # فیلدهای اصلی
    password = models.CharField(_('رمز عبور'), max_length=128, blank=False, null=False)
    email = models.EmailField(_('ایمیل'), blank=True, null=True)
    is_active = models.BooleanField(_('فعال'), default=True)
    is_staff = models.BooleanField(_('کارمند'), default=False)
    is_superuser = models.BooleanField(_('کاربر برتر'), default=False)

    date_joined = models.DateTimeField(_('تاریخ عضویت'), auto_now_add=True)

    # فیلدهای تأیید
    is_phone_verified = models.BooleanField(_('تلفن تأیید شده'), default=False)

    # فیلدهای امنیتی
    otp_code = models.CharField(max_length=5, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveIntegerField(default=0)
    login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)


#______________change phone_________
    new_phone = models.CharField(
        max_length=15, unique=True, null=True, blank=True, validators=[validate_iranian_mobile],
        verbose_name=_('شماره جدید (در انتظار تأیید)'))

    # OTP برای تأیید شماره جدید
    phone_change_otp = models.CharField(max_length=6, null=True, blank=True)
    phone_change_otp_created = models.DateTimeField(null=True, blank=True)
    phone_change_otp_attempts = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['password']

    class Meta:
        verbose_name = _('کاربر')
        verbose_name_plural = _('کاربران')
        db_table = 'accounts_customuser'

    def __str__(self):
        return self.phone

    def clean(self):
        """اعتبارسنجی مدل قبل از ذخیره"""
        super().clean()

        # اعتبارسنجی شماره تلفن
        try:
            self.phone = validate_iranian_mobile(self.phone)
        except ValidationError as e:
            raise ValidationError({'phone': e.messages})

    def save(self, *args, **kwargs):
        """ذخیره کاربر با اعمال منطق مورد نیاز"""
        self.clean()

        # اگر کاربر سوپریوزر است، تأیید تلفن را تنظیم کن
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

    # متدهای OTP
    def generate_otp(self):
        """تولید و ذخیره کد OTP با مدیریت خطا"""
        try:
            # تولید کد ۶ رقمی
            otp_code = f"{random.randint(0, 99999):05d}"

            # به‌روزرسانی فیلدها
            self.otp_code = otp_code
            self.otp_created_at = timezone.now()
            self.otp_attempts = 0

            # ذخیره در دیتابیس
            if self.pk:  # کاربر از قبل در دیتابیس وجود دارد
                self.save(update_fields=['otp_code', 'otp_created_at', 'otp_attempts'])
            else:  # کاربر جدید
                self.save()  # ذخیره اولیه

            logger.info(f"OTP generated for user {self.phone}")
            return otp_code

        except Exception as e:
            logger.error(f"Failed to generate OTP for {self.phone}: {str(e)}")
            raise

    def send_otp(self):
        """ارسال OTP"""
        otp_code = self.generate_otp()
        return send_sms_via_asanak(self.phone, otp_code)

    def verify_otp(self, code):
        """تأیید OTP"""
        if self.is_locked:
            return False, "حساب قفل شده است"

        if not self.otp_code or not self.otp_created_at:
            return False, "کد OTP وجود ندارد"

        if self.is_otp_expired():
            return False, "کد OTP منقضی شده است"

        if str(code).strip() == str(self.otp_code).strip():
            self.otp_code = None
            self.otp_created_at = None
            self.otp_attempts = 0
            self.is_phone_verified = True
            self.save()
            return True, "تأیید موفق"
        else:
            self.otp_attempts += 1
            if self.otp_attempts >= OTP_MAX_ATTEMPTS:
                self.lock_account()
            self.save()
            return False, "کد OTP نامعتبر است"

    def is_otp_expired(self):
        """بررسی انقضای OTP"""
        if not self.otp_created_at:
            return True
        return timezone.now() > self.otp_created_at + timedelta(minutes=OTP_EXPIRE_MINUTES)

    @property
    def is_locked(self):
        """بررسی قفل بودن حساب"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        elif self.locked_until and timezone.now() >= self.locked_until:
            self.unlock_account()
            return False
        return False

    def lock_account(self, minutes=30):
        """قفل کردن حساب"""
        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save()

    def unlock_account(self):
        """باز کردن قفل حساب"""
        self.locked_until = None
        self.otp_attempts = 0
        self.login_attempts = 0
        self.save()

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField( User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('کاربر'))

    # اطلاعات شخصی
    first_name = models.CharField(_('نام'), max_length=100, blank=True)
    last_name = models.CharField(_('نام خانوادگی'), max_length=100, blank=True)
    national_code = models.CharField(_('کد ملی'), max_length=10, blank=True)
    birth_date = models.DateField(_('تاریخ تولد'), null=True, blank=True)

    # اطلاعات تماس
    email = models.EmailField(_('ایمیل'), blank=True, null=True)
    phone = models.CharField(_('تلفن ثابت'), max_length=15, blank=True, validators=[validate_iranian_mobile])

    # آدرس
    province = models.CharField(_('استان'), max_length=100, blank=True)
    city = models.CharField(_('شهر'), max_length=100, blank=True)
    address = models.TextField(_('آدرس'), blank=True)
    postal_code = models.CharField(_('کد پستی'), max_length=10, blank=True)

    # تنظیمات
    email_notifications = models.BooleanField(_('اعلان ایمیلی'), default=True)
    sms_notifications = models.BooleanField(_('اعلان پیامکی'), default=True)

    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    updated_at = models.DateTimeField(_('آخرین بروزرسانی'), auto_now=True)

    class Meta:
        verbose_name = _('پروفایل کاربر')
        verbose_name_plural = _('پروفایل کاربران')

    def __str__(self):
        return f"{self.user.phone} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_complete(self):
        """بررسی کامل بودن پروفایل برای خرید"""
        required_fields = ['first_name', 'last_name', 'province', 'city', 'address', 'postal_code']
        return all(bool(getattr(self, field)) for field in required_fields)

    class Address(models.Model):
        """مدل آدرس برای کاربران (اگر نیاز به چند آدرس دارید)"""
        user = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='addresses',
            verbose_name=_('کاربر')
        )

        title = models.CharField(_('عنوان آدرس'), max_length=100)
        first_name = models.CharField(_('نام'), max_length=100)
        last_name = models.CharField(_('نام خانوادگی'), max_length=100)
        phone = models.CharField(_('تلفن'), max_length=15, validators=[validate_iranian_mobile])
        province = models.CharField(_('استان'), max_length=100)
        city = models.CharField(_('شهر'), max_length=100)
        address = models.TextField(_('آدرس'))
        postal_code = models.CharField(_('کد پستی'), max_length=10)
        is_default = models.BooleanField(_('پیش‌فرض'), default=False)

        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        class Meta:
            verbose_name = _('آدرس')
            verbose_name_plural = _('آدرس‌ها')
            ordering = ['-is_default', '-created_at']

        def __str__(self):
            return f"{self.title} - {self.user.phone}"

class LoginHistory(models.Model):
    """تاریخچه ورود"""
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
        verbose_name = _('تاریخچه ورود')
        verbose_name_plural = _('تاریخچه ورودها')
        ordering = ['-login_at']


class PhoneChangeHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار تأیید'),
        ('verified', 'تأیید شده'),
        ('expired', 'منقضی شده'),
        ('cancelled', 'لغو شده'),
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
        verbose_name = 'تاریخچه تغییر شماره تلفن'
        verbose_name_plural = 'تاریخچه تغییرات شماره تلفن'
        ordering = ['-created_at']

class SMSLog(models.Model):
    """لاگ پیامک"""
    phone = models.CharField(max_length=15, validators=[validate_iranian_mobile])
    code = models.CharField(max_length=6)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sending')

    class Meta:
        verbose_name = _('لاگ پیامک')
        verbose_name_plural = _('لاگ‌های پیامک')
        ordering = ['-created_at']

