from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class PaymentStatus(models.TextChoices):
    """Status values used for donations and payment transactions."""

    PENDING = 'pending', 'در انتظار پرداخت'
    PAID = 'paid', 'پرداخت‌شده'
    FAILED = 'failed', 'ناموفق'
    REFUNDED = 'refunded', 'بازپرداخت‌شده'
    CANCELED = 'canceled', 'لغوشده'
    EXPIRED = 'expired', 'منقضی‌شده'
    PROCESSING = 'processing', 'در حال پردازش'


class PaymentGateway(models.TextChoices):
    """Supported payment gateways."""

    ZARINPAL = 'zarinpal', 'زرین‌پال'
    SAMAN = 'saman', 'سامان'
    PAYPAL = 'paypal', 'پی‌پل'
    IDPAY = 'idpay', 'آی‌دی‌پی'
    MANUAL = 'manual', 'دستی'


class CharityProject(models.Model):
    """Represents a charity project that users can support."""

    class ProjectStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'در حال برنامه‌ریزی'
        ACTIVE = 'active', 'در حال اجرا'
        COMPLETED = 'completed', 'تکمیل شده'
        ARCHIVED = 'archived', 'آرشیو شده'

    title = models.CharField(max_length=200, verbose_name='عنوان پروژه')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='نامک')
    short_description = models.CharField(max_length=300, verbose_name='توضیح کوتاه')
    full_description = models.TextField(verbose_name='توضیحات کامل')
    impact_summary = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='جمع‌بندی اثرگذاری'
    )
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
        verbose_name='وضعیت'
    )
    location = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='مکان اجرا'
    )
    beneficiaries_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='تعداد ذی‌نفعان'
    )
    hero_video_url = models.URLField(
        blank=True,
        verbose_name='لینک ویدئوی معرفی'
    )
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        validators=[MinValueValidator(1000)],
        verbose_name='مبلغ هدف (تومان)'
    )
    current_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ جمع‌آوری‌شده فعلی (تومان)'
    )
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاریخ تکمیل'
    )
    is_featured = models.BooleanField(default=False, verbose_name='نمایش ویژه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    image = models.ImageField(upload_to='charity/projects/', verbose_name='تصویر شاخص')
    gallery = models.ManyToManyField(
        'ProjectGallery',
        blank=True,
        related_name='projects',
        verbose_name='رسانه‌های پروژه'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'پروژه حمایتی'
        verbose_name_plural = 'پروژه‌های حمایتی'
        ordering = ['-is_featured', '-created_at']

    def __str__(self) -> str:
        return self.title

    @property
    def progress(self) -> float:
        if self.target_amount == 0:
            return 0
        return round((self.current_amount / self.target_amount) * 100, 2)

    @property
    def remaining_days(self) -> int:
        remaining = self.end_date - timezone.now().date()
        return remaining.days if remaining.days > 0 else 0

    @property
    def donors_count(self) -> int:
        return self.donations.filter(payment_status=PaymentStatus.PAID).count()

    @property
    def amount_remaining(self):
        remaining = self.target_amount - self.current_amount
        return remaining if remaining > 0 else 0

    @property
    def is_completed(self) -> bool:
        if self.status == self.ProjectStatus.COMPLETED:
            return True
        if self.target_amount > 0 and self.current_amount >= self.target_amount:
            return True
        return False

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('charity:project_detail', args=[self.slug])


class ProjectGallery(models.Model):
    """Stores media assets (images/videos/links) for projects."""

    class MediaType(models.TextChoices):
        IMAGE = 'image', 'تصویر'
        VIDEO = 'video', 'ویدئو'
        EXTERNAL = 'external', 'لینک خارجی'

    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
        verbose_name='نوع رسانه'
    )
    image = models.ImageField(
        upload_to='charity/projects/gallery/images/',
        null=True,
        blank=True,
        verbose_name='فایل تصویر'
    )
    video_file = models.FileField(
        upload_to='charity/projects/gallery/videos/',
        null=True,
        blank=True,
        verbose_name='فایل ویدئو'
    )
    external_url = models.URLField(
        blank=True,
        verbose_name='لینک خارجی'
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name='عنوان')
    display_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'رسانه پروژه'
        verbose_name_plural = 'رسانه‌های پروژه'
        ordering = ['display_order', '-created_at']

    def __str__(self) -> str:
        return self.caption or f"Media {self.id}"

    def source(self):
        if self.media_type == self.MediaType.IMAGE:
            return self.image.url if self.image else ''
        if self.media_type == self.MediaType.VIDEO:
            return self.video_file.url if self.video_file else ''
        return self.external_url

    source.short_description = 'مسیر رسانه'


class ProjectUpdate(models.Model):
    """Progress update for a project."""

    project = models.ForeignKey(
        CharityProject,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name='پروژه'
    )
    title = models.CharField(max_length=200, verbose_name='عنوان به‌روزرسانی')
    summary = models.CharField(max_length=300, blank=True, verbose_name='خلاصه')
    body = models.TextField(verbose_name='متن کامل')
    progress_percent = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='درصد پیشرفت'
    )
    highlight_image = models.ImageField(
        upload_to='charity/projects/updates/images/',
        null=True,
        blank=True,
        verbose_name='تصویر اصلی'
    )
    video_file = models.FileField(
        upload_to='charity/projects/updates/videos/',
        null=True,
        blank=True,
        verbose_name='فایل ویدئو'
    )
    video_url = models.URLField(blank=True, verbose_name='لینک ویدئو')
    is_public = models.BooleanField(default=True, verbose_name='قابل نمایش در سایت')
    display_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ انتشار')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'به‌روزرسانی پروژه'
        verbose_name_plural = 'به‌روزرسانی‌های پروژه'
        ordering = ['display_order', '-published_at']

    def __str__(self) -> str:
        return f"{self.project.title} - {self.title}"

    @property
    def has_video(self) -> bool:
        return bool(self.video_file or self.video_url)


class ParticipationMethod(models.Model):
    """Ways the audience can collaborate with the charity."""

    title = models.CharField(max_length=150, verbose_name='عنوان')
    slug = models.SlugField(max_length=160, unique=True, verbose_name='نامک')
    description = models.TextField(verbose_name='توضیحات')
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='کلاس آیکن (Bootstrap/Icon)'
    )
    action_text = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='متن دکمه اقدام'
    )
    action_url = models.URLField(blank=True, verbose_name='لینک اقدام')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    display_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'روش مشارکت'
        verbose_name_plural = 'روش‌های مشارکت'
        ordering = ['display_order', 'title']

    def __str__(self) -> str:
        return self.title


class ImpactStat(models.Model):
    """High-level impact numbers shown on the landing page."""

    title = models.CharField(max_length=120, verbose_name='عنوان')
    value = models.CharField(max_length=120, verbose_name='مقدار')
    unit = models.CharField(max_length=60, blank=True, verbose_name='واحد')
    description = models.TextField(blank=True, verbose_name='توضیح تکمیلی')
    display_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'آمار اثرگذاری'
        verbose_name_plural = 'آمارهای اثرگذاری'
        ordering = ['display_order', 'title']

    def __str__(self) -> str:
        return self.title


class Donation(models.Model):
    """Donation records linked to projects."""

    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        verbose_name='حامی'
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
        verbose_name='مبلغ کمک (تومان)'
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
    donor_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='نام حامی (برای پرداخت مهمان)'
    )
    donor_email = models.EmailField(blank=True, verbose_name='ایمیل حامی')
    donor_phone = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')
    is_anonymous = models.BooleanField(default=False, verbose_name='نمایش ناشناس')
    message = models.CharField(max_length=300, blank=True, verbose_name='پیام حامی')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'کمک مالی'
        verbose_name_plural = 'کمک‌های مالی'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Donation #{self.id} - {self.amount} تومان"

    def save(self, *args, **kwargs):
        """Ensure project totals stay in sync when payment status changes."""
        update_project_total = False
        if self.pk:
            previous = Donation.objects.get(pk=self.pk)
            if previous.payment_status != self.payment_status:
                update_project_total = True
        else:
            if self.payment_status == PaymentStatus.PAID:
                update_project_total = True

        super().save(*args, **kwargs)

        if update_project_total:
            paid_total = self.project.donations.filter(
                payment_status=PaymentStatus.PAID
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            self.project.current_amount = paid_total
            if self.project.is_completed and not self.project.completion_date:
                self.project.completion_date = timezone.now().date()
            self.project.save(update_fields=['current_amount', 'completion_date', 'updated_at'])


class DonationReceipt(models.Model):
    """Receipt generated for a paid donation."""

    donation = models.OneToOneField(
        Donation,
        on_delete=models.CASCADE,
        related_name='donation_receipt',
        verbose_name='کمک مالی'
    )
    receipt_number = models.CharField(max_length=50, unique=True, verbose_name='شماره رسید')
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ صدور')
    pdf_file = models.FileField(upload_to='donations/receipts/pdf/', verbose_name='فایل PDF')

    class Meta:
        verbose_name = 'رسید کمک'
        verbose_name_plural = 'رسیدهای کمک'
        ordering = ['-issued_at']

    def __str__(self) -> str:
        return f"Receipt #{self.receipt_number}"


class PaymentTransaction(models.Model):
    """Audit trail for gateway responses."""

    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کمک مالی'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ')
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
    transaction_code = models.CharField(max_length=100, verbose_name='کد تراکنش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    raw_response = models.JSONField(null=True, blank=True, verbose_name='پاسخ خام درگاه')

    class Meta:
        verbose_name = 'تراکنش پرداخت'
        verbose_name_plural = 'تراکنش‌های پرداخت'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Transaction #{self.id} - {self.get_status_display()}"
