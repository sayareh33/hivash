# orders/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField

from accounts.validators import validate_iranian_mobile
from .models import Order, UserAddress
from django.utils.translation import gettext_lazy as _
# orders/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings

# ایمپورت پروفایل از اپ اکانت
try:
    from account.models import UserProfile
except ImportError:
    # اگر اپ اکانت جدا است
    UserProfile = None


# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = [
#             'first_name', 'last_name', 'phone_number',
#             'country', 'province', 'city', 'address',
#             'postal_code', 'email', 'order_notes'
#         ]
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#         if self.user and self.user.is_authenticated:
#             self._set_initial_values()
#
#     def _set_initial_values(self):
#         """تعیین مقادیر اولیه از پروفایل کاربر"""
#         User = get_user_model()
#
#         try:
#             # بررسی وجود پروفایل
#             if hasattr(self.user, 'profile'):
#                 profile = self.user.profile
#
#                 # پر کردن فیلدها از پروفایل
#                 field_mapping = {
#                     'first_name': profile.first_name,
#                     'last_name': profile.last_name,
#                     'country': profile.country,
#                     'province': profile.province,
#                     'city': profile.city,
#                     'address': profile.address,
#                     'postal_code': profile.postal_code,
#                     'email': profile.email or self.user.email,
#                 }
#
#                 for field, value in field_mapping.items():
#                     if value and not self.initial.get(field):
#                         self.fields[field].initial = value
#
#             # شماره تلفن همیشه از کاربر اصلی گرفته شود
#             if hasattr(self.user, 'phone_number'):
#                 self.fields['phone_number'].initial = self.user.phone_number
#
#         except Exception as e:
#             # لاگ کردن خطا ولی ادامه اجرا
#             import logging
#             logger = logging.getLogger(__name__)
#             logger.warning(f"Error setting initial values: {e}")


class OrderForm(forms.ModelForm):
    # فقط فیلدهای قابل تغییر برای این سفارش
    use_profile_address = forms.BooleanField(
        initial=True,
        required=False,
        label=_('استفاده از آدرس ذخیره شده در پروفایل')
    )

    # فیلدهای آدرس فقط در صورت نیاز نمایش داده شوند
    country = CountryField(blank_label=_('انتخاب کشور')).formfield(required=False)
    province = forms.CharField(max_length=100, required=False, label=_('استان'))
    city = forms.CharField(max_length=100, required=False, label=_('شهر'))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label=_('آدرس'))
    postal_code = forms.CharField(max_length=10, required=False, label=_('کد پستی'))

    class Meta:
        model = Order
        fields = ['order_notes']  # تنها فیلد واقعی در مدل Order

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile
            # فقط مقدار اولیه برای نمایش - غیرقابل ویرایش
            self.fields['country'].initial = profile.country
            self.fields['province'].initial = profile.province
            self.fields['city'].initial = profile.city
            self.fields['address'].initial = profile.address
            self.fields['postal_code'].initial = profile.postal_code

            # غیرفعال کردن فیلدهای اطلاعات شخصی
            self.fields['country'].disabled = True
            self.fields['province'].disabled = True
            self.fields['city'].disabled = True
            self.fields['address'].disabled = True
            self.fields['postal_code'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        use_profile_address = cleaned_data.get('use_profile_address', True)

        if not use_profile_address:
            # اعتبارسنجی فیلدهای آدرس در صورت نیاز به آدرس جدید
            required_fields = ['country', 'province', 'city', 'address']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('این فیلد برای آدرس جدید ضروری است.'))

        return cleaned_data
class OrderAddressForm(forms.ModelForm):
    USE_DEFAULT_ADDRESS = 'default'
    USE_NEW_ADDRESS = 'new'
    USE_SAVED_ADDRESS = 'saved'

    address_choice = forms.ChoiceField(
        choices=[
            (USE_DEFAULT_ADDRESS, 'استفاده از آدرس پیش‌فرض'),
            (USE_SAVED_ADDRESS, 'انتخاب از آدرس‌های ذخیره شده'),
            (USE_NEW_ADDRESS, 'استفاده از آدرس جدید'),
        ],
        initial=USE_DEFAULT_ADDRESS,
        widget=forms.RadioSelect,
        label=_('نحوه انتخاب آدرس')
    )

    saved_address = forms.ModelChoiceField(
        queryset=UserAddress.objects.none(),
        required=False,
        label=_('آدرس ذخیره شده')
    )

    # فیلدهای آدرس جدید
    first_name = forms.CharField(max_length=100, required=False, label=_('نام گیرنده'))
    last_name = forms.CharField(max_length=100, required=False, label=_('نام خانوادگی گیرنده'))
    phone_number = forms.CharField(max_length=15, required=False, label=_('شماره تماس'))
    country = CountryField(blank_label=_('انتخاب کشور')).formfield(required=False)
    province = forms.CharField(max_length=100, required=False, label=_('استان'))
    city = forms.CharField(max_length=100, required=False, label=_('شهر'))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label=_('آدرس'))
    postal_code = forms.CharField(max_length=10, required=False, label=_('کد پستی'))

    save_new_address = forms.BooleanField(
        required=False,
        initial=False,
        label=_('ذخیره این آدرس در پروفایل')
    )
    address_title = forms.CharField(max_length=100, required=False, label=_('عنوان آدرس'))

    class Meta:
        model = Order
        fields = ['order_notes']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile
            # پر کردن آدرس پیش‌فرض
            default_address = profile.addresses.filter(is_default=True).first()
            if default_address:
                self.fields['first_name'].initial = default_address.first_name
                self.fields['last_name'].initial = default_address.last_name
                self.fields['phone_number'].initial = default_address.phone_number
                self.fields['country'].initial = default_address.country
                self.fields['province'].initial = default_address.province
                self.fields['city'].initial = default_address.city
                self.fields['address'].initial = default_address.address
                self.fields['postal_code'].initial = default_address.postal_code

            # آدرس‌های ذخیره شده کاربر
            self.fields['saved_address'].queryset = profile.addresses.all()

    def clean(self):
        cleaned_data = super().clean()
        address_choice = cleaned_data.get('address_choice')

        if address_choice == self.USE_NEW_ADDRESS:
            # اعتبارسنجی آدرس جدید
            required_fields = ['first_name', 'last_name', 'phone_number',
                               'country', 'province', 'city', 'address']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('این فیلد برای آدرس جدید ضروری است.'))

            # اعتبارسنجی شماره تلفن
            if cleaned_data.get('phone_number'):
                try:
                    validate_iranian_mobile(cleaned_data['phone_number'])
                except ValidationError:
                    self.add_error('phone_number', _('شماره تلفن معتبر نیست.'))

        elif address_choice == self.USE_SAVED_ADDRESS and not cleaned_data.get('saved_address'):
            self.add_error('saved_address', _('لطفا یک آدرس انتخاب کنید.'))

        return cleaned_data
#
# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = [
#             'first_name', 'last_name', 'phone_number',
#             'country', 'province', 'city', 'address',
#             'postal_code', 'order_notes'
#         ]
#         widgets = {
#             'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'آدرس کامل پستی'}),
#             'order_notes': forms.Textarea(attrs={'rows': 5, 'placeholder': 'ملاحظات سفارش (اختیاری)'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#         # پر کردن خودکار فیلدها از پروفایل کاربر
#         if user and hasattr(user, 'profile'):
#             profile = user.profile
#             if not self.instance.pk:  # فقط برای ایجاد سفارش جدید
#                 self.fields['first_name'].initial = profile.first_name
#                 self.fields['last_name'].initial = profile.last_name
#                 self.fields['phone_number'].initial = user.phone
#                 self.fields['country'].initial = profile.country
#                 self.fields['province'].initial = profile.province
#                 self.fields['city'].initial = profile.city
#                 self.fields['address'].initial = profile.address
#                 self.fields['postal_code'].initial = profile.postal_code
#                 self.fields['email'].initial = profile.email or user.email