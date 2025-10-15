# models.py

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# pages/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class ContactMessage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="contact_messages",
        verbose_name=_("کاربر")
    )
    name = models.CharField(_("نام"), max_length=100)
    email = models.EmailField(_("ایمیل"))
    subject = models.CharField(_("موضوع"), max_length=200)
    message = models.TextField(_("پیام"))
    created_at = models.DateTimeField(_("تاریخ ارسال"), default=timezone.now)
    is_read = models.BooleanField(_("خوانده شده؟"), default=False)
    admin_notes = models.TextField(
        blank=True,
        verbose_name='یادداشت مدیریت',
        help_text='یادداشت داخلی برای تیم مدیریت'
    )
    class Meta:
        verbose_name = _("پیام تماس")
        verbose_name_plural = _("پیام‌های تماس")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} - {self.subject[:30]}"

#     STATUS_CHOICES = [
#         ('new', 'جدید'),
#         ('read', 'خوانده شده'),
#         ('replied', 'پاسخ داده شده'),
#     ]
#
#     # Link to authenticated user
#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name='contact_messages',
#         verbose_name='کاربر'
#     )
#
#     # Auto-filled from user profile if available
#     name = models.CharField(max_length=100, verbose_name='نام')
#     email = models.EmailField(verbose_name='ایمیل')
#     phone = models.CharField(max_length=15, verbose_name='تلفن')
#
#     subject = models.CharField(max_length=200, verbose_name='موضوع')
#     message = models.TextField(verbose_name='پیام')
#
#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default='new',
#         verbose_name='وضعیت'
#     )
#
#     ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='آدرس IP')
#     created_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')
#     updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
#
#     class Meta:
#         verbose_name = 'پیام تماس'
#         verbose_name_plural = 'پیام‌های تماس'
#         ordering = ['-created_at']
#
#     def __str__(self):
#         return f"{self.name} - {self.subject}"
#
#     def save(self, *args, **kwargs):
#         # Auto-fill user information if not provided
#         if self.user and not self.name:
#             if hasattr(self.user, 'profile'):
#                 profile = self.user.profile
#                 if profile.first_name and profile.last_name:
#                     self.name = f"{profile.first_name} {profile.last_name}"
#                 elif profile.first_name:
#                     self.name = profile.first_name
#                 else:
#                     self.name = self.user.phone
#
#         if self.user and not self.email:
#             if hasattr(self.user, 'profile') and self.user.profile.email:
#                 self.email = self.user.profile.email
#             elif self.user.email:
#                 self.email = self.user.email
#
#         if self.user and not self.phone:
#             self.phone = self.user.phone
#
#         super().save(*args, **kwargs)
#
#
# class SiteSetting(models.Model):
#     site_name = models.CharField(max_length=100, verbose_name='نام سایت')
#     contact_email = models.EmailField(verbose_name='ایمیل تماس')
#     support_email = models.EmailField(verbose_name='ایمیل پشتیبانی')
#     phone_number = models.CharField(max_length=15, verbose_name='تلفن')
#     mobile_number = models.CharField(max_length=15, verbose_name='موبایل')
#     address = models.TextField(verbose_name='آدرس')
#
#     # Social Media
#     instagram_url = models.URLField(blank=True, null=True, verbose_name='اینستاگرام')
#     telegram_url = models.URLField(blank=True, null=True, verbose_name='تلگرام')
#     whatsapp_url = models.URLField(blank=True, null=True, verbose_name='واتساپ')
#     linkedin_url = models.URLField(blank=True, null=True, verbose_name='لینکدین')
#
#     # Business Hours
#     sat_to_wed_hours = models.CharField(max_length=50, verbose_name='ساعات کاری شنبه تا چهارشنبه')
#     thursday_hours = models.CharField(max_length=50, verbose_name='ساعات کاری پنجشنبه')
#     friday_hours = models.CharField(max_length=50, default='تعطیل', verbose_name='ساعات کاری جمعه')
#
#     # Map
#     map_embed_url = models.TextField(verbose_name='لینک نقشه')
#
#     class Meta:
#         verbose_name = 'تنظیمات سایت'
#         verbose_name_plural = 'تنظیمات سایت'
#
#     def __str__(self):
#         return self.site_name
#
#     def save(self, *args, **kwargs):
#         if not self.pk and SiteSetting.objects.exists():
#             existing = SiteSetting.objects.first()
#             existing.site_name = self.site_name
#             existing.contact_email = self.contact_email
#             existing.support_email = self.support_email
#             existing.phone_number = self.phone_number
#             existing.mobile_number = self.mobile_number
#             existing.address = self.address
#             existing.instagram_url = self.instagram_url
#             existing.telegram_url = self.telegram_url
#             existing.whatsapp_url = self.whatsapp_url
#             existing.linkedin_url = self.linkedin_url
#             existing.sat_to_wed_hours = self.sat_to_wed_hours
#             existing.thursday_hours = self.thursday_hours
#             existing.friday_hours = self.friday_hours
#             existing.map_embed_url = self.map_embed_url
#             existing.save()
#             return
#         super(SiteSetting, self).save(*args, **kwargs)