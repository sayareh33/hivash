from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField

from accounts.models import UserProfile
from accounts.validators import validate_iranian_mobile

User = get_user_model()

class UnpaidOrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Order.ORDER_STATUS_UNPAID)


class PaidOrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Order.ORDER_STATUS_PAID)


class Order(models.Model):
    ORDER_STATUS_PAID = 'p'
    ORDER_STATUS_UNPAID = 'u'
    ORDER_STATUS_CANCELED = 'c'
    ORDER_STATUS = [
        (ORDER_STATUS_PAID, 'Paid'),
        (ORDER_STATUS_UNPAID, 'Unpaid'),
        (ORDER_STATUS_CANCELED, 'Canceled'),
    ]

    # ارتباط با User از طریق UserProfile
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        verbose_name=_('پروفایل کاربر'),
        related_name='orders'
    )

    status = models.CharField(max_length=1, choices=ORDER_STATUS, default=ORDER_STATUS_UNPAID)
    is_paid = models.BooleanField(_('پرداخت شده؟'), default=False)

    # ✅ حذف فیلدهای تکراری - اطلاعات از UserProfile گرفته می‌شود
    order_notes = models.TextField(_('یادداشت سفارش'), blank=True, max_length=700)

    datetime_created = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    datetime_modified = models.DateTimeField(_('تاریخ ویرایش'), auto_now=True)

    objects = models.Manager()
    unpaid_orders = UnpaidOrderManager()
    paid_orders = PaidOrderManager()

    class Meta:
        indexes = [
            models.Index(fields=['status', 'datetime_created']),
            models.Index(fields=['user_profile', 'datetime_created']),
        ]
        verbose_name = _('سفارش')
        verbose_name_plural = _('سفارشات')

    def __str__(self):
        return f"سفارش {self.id} - {self.user_profile.full_name}"


    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('order_detail', kwargs={'order_id': self.id})


    # Property برای دسترسی آسان به اطلاعات کاربر
    @property
    def customer(self):
        """دسترسی به کاربر مربوطه"""
        return self.user_profile.user

    @property
    def user_phone(self):
        """شماره تلفن کاربر"""
        return self.user_profile.user.phone_number
    @property
    def receiver_name(self):
        """نام مشتری از آدرس سفارش"""
        if self.shipping_address:
            return self.shipping_address.full_name
        return self.user_profile.full_name

    @property
    def receiver_phone(self):
        """شماره تماس مشتری از آدرس سفارش"""
        if self.shipping_address:
            return self.shipping_address.phone_number
        return self.user_profile.user.phone_number

    @property
    def shipping_address(self):
        """دریافت آدرس سفارش از طریق مدل OrderAddress"""
        if hasattr(self, 'shipping_address_obj'):
            return self.shipping_address_obj
        return None

    @property
    def total_price(self):
        return sum(item.price * item.quantity for item in self.items.all())

    @classmethod
    def get_total_sales(cls):
        """محاسبه کل فروش به روش بهینه"""
        from django.db.models import Sum, F
        return OrderItem.objects.filter(
            order__status=cls.ORDER_STATUS_PAID
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

    @property
    def total_quantity(self):
        """تعداد کل آیتم‌های سفارش"""
        return sum(item.quantity for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField()

    def __str__(self):
        return f'OrderItem {self.id} or Order {self.order.id}: {self.product} x {self.quantity} (price: {self.price})'

    class Meta:
        unique_together = [['order', 'product']]


class OrderAddress(models.Model):
    """ذخیره آدرس هر سفارش به صورت جداگانه"""
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipping_address_obj',
        verbose_name=_('سفارش')
    )

    # اطلاعات گیرنده
    first_name = models.CharField(max_length=100, verbose_name=_('نام گیرنده'))
    last_name = models.CharField(max_length=100, verbose_name=_('نام خانوادگی گیرنده'))
    phone_number = models.CharField(
        max_length=15,
        validators=[validate_iranian_mobile],
        verbose_name=_('شماره تماس گیرنده')
    )

    # آدرس تحویل
    country = CountryField(verbose_name=_('کشور'))
    province = models.CharField(max_length=100, verbose_name=_('استان'))
    city = models.CharField(max_length=100, verbose_name=_('شهر'))
    address = models.TextField(verbose_name=_('آدرس کامل'))
    postal_code = models.CharField(max_length=10, verbose_name=_('کد پستی'))

    # اطلاعات اضافی
    is_business_address = models.BooleanField(default=False, verbose_name=_('آدرس تجاری'))
    company_name = models.CharField(max_length=200, blank=True, verbose_name=_('نام شرکت'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))

    class Meta:
        verbose_name = _('آدرس سفارش')
        verbose_name_plural = _('آدرس‌های سفارش')
        indexes = [
            models.Index(fields=['order', 'phone_number']),
            models.Index(fields=['province', 'city']),
        ]

    def __str__(self):
        return f"آدرس سفارش {self.order.id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def formatted_address(self):
        return f"{self.country.name}، {self.province}، {self.city}، {self.address} - کد پستی: {self.postal_code}"


class UserAddress(models.Model):
    """ذخیره آدرس‌های مختلف کاربر"""
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('پروفایل کاربر')
    )

    title = models.CharField(max_length=100, verbose_name=_('عنوان آدرس'))
    first_name = models.CharField(max_length=100, verbose_name=_('نام'))
    last_name = models.CharField(max_length=100, verbose_name=_('نام خانوادگی'))
    phone_number = models.CharField(
        max_length=15,
        validators=[validate_iranian_mobile],
        verbose_name=_('شماره تماس')
    )

    country = CountryField(verbose_name=_('کشور'))
    province = models.CharField(max_length=100, verbose_name=_('استان'))
    city = models.CharField(max_length=100, verbose_name=_('شهر'))
    address = models.TextField(verbose_name=_('آدرس کامل'))
    postal_code = models.CharField(max_length=10, validators=[MinLengthValidator(10)], verbose_name=_('کد پستی'))
    # تنظیمات آدرس
    is_default = models.BooleanField(default=False, verbose_name=_('آدرس پیش‌فرض'))
    is_business = models.BooleanField(default=False, verbose_name=_('آدرس تجاری'))
    company_name = models.CharField(max_length=200, blank=True, verbose_name=_('نام شرکت'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('آدرس کاربر')
        verbose_name_plural = _('آدرس‌های کاربر')
        ordering = ['-is_default', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user_profile'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_user'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.user_profile.user.phone}"

    def save(self, *args, **kwargs):
        # اگر این آدرس به عنوان پیش‌فرض تنظیم شده، سایر آدرس‌ها را از حالت پیش‌فرض خارج کن
        if self.is_default:
            UserAddress.objects.filter(
                user_profile=self.user_profile,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        return f"{self.country.name}، {self.province}، {self.city}، {self.address}"

    @property
    def formatted_address(self):
        components = [
            self.country.name if self.country else '',
            self.province,
            self.city,
            self.address
        ]
        return "، ".join(filter(None, components))

    def clean(self):
        """اعتبارسنجی سفارشی"""
        super().clean()

        if self.postal_code and len(self.postal_code) != 10:
            raise ValidationError({'postal_code': 'کد پستی باید ۱۰ رقمی باشد'})