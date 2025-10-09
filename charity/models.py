from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'در انتظار پرداخت'
    PAID = 'paid', 'پرداخت موفق'
    FAILED = 'failed', 'پرداخت ناموفق'
    REFUNDED = 'refunded', 'عودت داده شده'
    CANCELED = 'canceled', 'لغو شده'
    EXPIRED = 'expired', 'منقضی شده'
    PROCESSING = 'processing', 'در حال پردازش'


class PaymentGateway(models.TextChoices):
    ZARINPAL = 'zarinpal', 'زرین پال'
    SAMAN = 'saman', 'سامان'
    PAYPAL = 'paypal', 'پی پال'
    IDPAY = 'idpay', 'آیدی پی'
    MANUAL = 'manual', 'پرداخت دستی'


class CharityProject(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان پروژه')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='اسلاگ')
    short_description = models.CharField(max_length=300, verbose_name='توضیح کوتاه')
    full_description = models.TextField(verbose_name='توضیحات کامل')
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        validators=[MinValueValidator(1000)],
        verbose_name='مبلغ هدف'
    )
    current_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ جمع‌آوری شده'
    )
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    is_featured = models.BooleanField(default=False, verbose_name='پروژه ویژه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    image = models.ImageField(upload_to='charity/projects/', verbose_name='تصویر اصلی')
    gallery = models.ManyToManyField('ProjectGallery', blank=True, verbose_name='گالری تصاویر')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'پروژه خیریه'
        verbose_name_plural = 'پروژه‌های خیریه'
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.title

    @property
    def progress(self):
        """محاسبه درصد پیشرفت پروژه"""
        if self.target_amount == 0:
            return 0
        return round((self.current_amount / self.target_amount) * 100, 2)

    @property
    def remaining_days(self):
        """محاسبه روزهای باقیمانده تا پایان پروژه"""
        remaining = self.end_date - timezone.now().date()
        return remaining.days if remaining.days > 0 else 0

    @property
    def donors_count(self):
        """تعداد اهداکنندگان به این پروژه"""
        return self.donations.filter(payment_status=PaymentStatus.PAID).count()


class ProjectGallery(models.Model):
    image = models.ImageField(upload_to='charity/projects/gallery/', verbose_name='تصویر')
    caption = models.CharField(max_length=200, blank=True, verbose_name='عنوان تصویر')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر گالری'
        verbose_name_plural = 'گالری تصاویر'

    def __str__(self):
        return self.caption or f"Image {self.id}"


class Donation(models.Model):
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        verbose_name='اهداکننده'
    )
    project = models.ForeignKey(
        CharityProject,
        on_delete=models.CASCADE,
        related_name='donations',
        verbose_name='پروژه'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        validators=[MinValueValidator(1000)],
        verbose_name='مبلغ اهدایی'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='وضعیت پرداخت'
    )
    payment_gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        null=True,
        blank=True,
        verbose_name='درگاه پرداخت'
    )
    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شناسه تراکنش'
    )
    donation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ اهدا'
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='ناشناس'
    )
    message = models.TextField(
        blank=True,
        null=True,
        verbose_name='پیام اهداکننده'
    )
    receipt = models.FileField(
        upload_to='donations/receipts/',
        null=True,
        blank=True,
        verbose_name='رسید پرداخت'
    )
    ref_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='کد پیگیری'
    )

    class Meta:
        verbose_name = 'اهدا'
        verbose_name_plural = 'اهدایی‌ها'
        ordering = ['-donation_date']

    def __str__(self):
        return f"Donation #{self.id} - {self.amount}"

    def save(self, *args, **kwargs):
        """بروزرسانی مبلغ جمع‌آوری شده پروژه هنگام تغییر وضعیت پرداخت"""
        if self.pk:
            old_donation = Donation.objects.get(pk=self.pk)
            if old_donation.payment_status != self.payment_status:
                if self.payment_status == PaymentStatus.PAID and old_donation.payment_status != PaymentStatus.PAID:
                    self.project.current_amount += self.amount
                    self.project.save()
                elif self.payment_status != PaymentStatus.PAID and old_donation.payment_status == PaymentStatus.PAID:
                    self.project.current_amount -= self.amount
                    self.project.save()
        super().save(*args, **kwargs)


class DonationReceipt(models.Model):
    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name='donation_receipt',
        verbose_name='اهدا'
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='شماره رسید'
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ صدور'
    )
    pdf_file = models.FileField(
        upload_to='donations/receipts/pdf/',
        verbose_name='فایل PDF'
    )

    class Meta:
        verbose_name = 'رسید اهدا'
        verbose_name_plural = 'رسیدهای اهدا'

    def __str__(self):
        return f"Receipt #{self.receipt_number}"


class PaymentTransaction(models.Model):
    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='اهدا'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='مبلغ'
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        verbose_name='وضعیت'
    )
    gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        verbose_name='درگاه پرداخت'
    )
    transaction_code = models.CharField(
        max_length=100,
        verbose_name='کد تراکنش'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ بروزرسانی'
    )
    raw_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name='پاسخ درگاه'
    )

    class Meta:
        verbose_name = 'تراکنش پرداخت'
        verbose_name_plural = 'تراکنش‌های پرداخت'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction #{self.id} - {self.get_status_display()}"





# from django.db import models
# from django.conf import settings
#
#
# class CharityProject(models.Model):
#     title = models.CharField(max_length=200)
#     description = models.TextField()
#     target_amount = models.DecimalField(max_digits=12, decimal_places=0)
#     current_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     is_active = models.BooleanField(default=True)
#     image = models.ImageField(upload_to='charity/projects/')
#
#     @property
#     def progress(self):
#         return (self.current_amount / self.target_amount) * 100
#
#
# class Donation(models.Model):
#     donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
#     project = models.ForeignKey(CharityProject, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=12, decimal_places=0)
#     donation_date = models.DateTimeField(auto_now_add=True)
#     is_anonymous = models.BooleanField(default=False)
#     payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES)
#
#
# from django.db import models
#
# # Create your models here.
