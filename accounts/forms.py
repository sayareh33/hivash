# accounts/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from pyexpat.errors import messages

from .validators import validate_iranian_mobile
from .models import CustomUser, UserProfile
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class SignUpForm(forms.Form):
    phone = forms.CharField(
        label=_('شماره تلفن همراه'),
        max_length=11,
        validators=[lambda x: validate_iranian_mobile(x, 'database')],
        widget=forms.TextInput(attrs={
            'placeholder': '09xxxxxxxxx',
            'class': 'form-control',
            'autocomplete': 'phone'
        })
    )

    email = forms.EmailField(
        label='ایمیل (اختیاری)',
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@domain.com',
            'class': 'form-control'
        })
    )

    password = forms.CharField(
        label=_('رمز عبور'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'حداقل ۸ کاراکتر',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )

    confirm_password = forms.CharField(
        label=_('تکرار رمز عبور'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    terms_accepted = forms.BooleanField(  # نام فیلد باید با HTML مطابقت داشته باشد
        label='موافقت با شرایط استفاده',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'لطفاً شرایط استفاده را بپذیرید'}

    )

    # privacy_policy_accepted = forms.BooleanField(
    #     label=_('موافقت با حریم خصوصی'),
    #     widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    #     error_messages={'required': _('لطفاً حریم خصوصی را بپذیرید')}
    # )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError(_('رمز عبور و تکرار آن مطابقت ندارند'))

        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        try:
            validated_phone = validate_iranian_mobile(phone)

            # بررسی وجود کاربر با این شماره
            if CustomUser.objects.filter(phone=validated_phone).exists():
                raise ValidationError(_('این شماره تلفن قبلاً ثبت شده است'))

            if password and confirm_password and password != confirm_password:
                raise ValidationError('رمز عبور و تکرار آن مطابقت ندارند')
            return validated_phone
        except ValidationError as e:
            raise ValidationError(_('شماره تلفن معتبر نیست'))

class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label=_('کد تأیید'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'xxxxxx',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )


from django import forms
from .validators import validate_iranian_mobile


class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        label='شماره تلفن همراه',
        validators=[validate_iranian_mobile],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09xxxxxxxxx'
        })
    )

    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید'
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        label='مرا به خاطر بسپار',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

#
# class ForgotPasswordForm(forms.Form):
#     phone = forms.CharField(
#         max_length=15,
#         label=_('شماره تلفن همراه'),
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': '09xxxxxxxxx',
#             'autocomplete': 'tel'
#         }),
#         validators=[validate_iranian_mobile]
#     )
#
#
# class ResetPasswordForm(forms.Form):
#     new_password = forms.CharField(
#         label=_('رمز عبور جدید'),
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'حداقل ۸ کاراکتر',
#             'autocomplete': 'new-password'
#         }),
#         min_length=8
#     )
#
#     confirm_password = forms.CharField(
#         label=_('تکرار رمز عبور جدید'),
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'تکرار رمز عبور جدید',
#             'autocomplete': 'new-password'
#         })
#     )
#
#     def clean(self):
#         cleaned_data = super().clean()
#         new_password = cleaned_data.get('new_password')
#         confirm_password = cleaned_data.get('confirm_password')
#
#         if new_password and confirm_password and new_password != confirm_password:
#             raise ValidationError(_('رمز عبور و تکرار آن مطابقت ندارند'))
#
#         return cleaned_data
#
#
class ResendOTPForm(forms.Form):
    """
    فرم ساده برای درخواست ارسال مجدد OTP
    این فرم معمولاً از طریق AJAX ارسال می‌شود
    """
    pass  # هیچ فیلدی نیاز نیست، فقط دکمه ارسال مجدد


class PasswordResetRequestForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        label='شماره تلفن همراه',
        validators=[validate_iranian_mobile],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09xxxxxxxxx'
        })
    )



# class PasswordResetConfirmForm(forms.Form):
#     new_password = forms.CharField(
#         label='رمز عبور جدید',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'رمز عبور جدید'
#         }),
#         min_length=8
#     )
#     confirm_password = forms.CharField(
#         label='تکرار رمز عبور جدید',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'تکرار رمز عبور جدید'
#         })
#     )
#
#     def clean(self):
#         cleaned_data = super().clean()
#         new_password = cleaned_data.get('new_password')
#         confirm_password = cleaned_data.get('confirm_password')
#
#         if new_password and confirm_password and new_password != confirm_password:
#             raise forms.ValidationError('رمز عبور و تکرار آن مطابقت ندارند')
#
#         return cleaned_data
#
#
#
#
#
#
#
# class CustomPasswordChangeForm(PasswordChangeForm):
#     """
#     فرم سفارشی تغییر رمز عبور
#     """
#     old_password = forms.CharField(
#         label=_("رمز عبور فعلی"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'رمز عبور فعلی خود را وارد کنید',
#             'autocomplete': 'current-password'
#         }),
#         error_messages={
#             'required': 'لطفاً رمز عبور فعلی را وارد کنید'
#         }
#     )
#     new_password1 = forms.CharField(
#         label=_("رمز عبور جدید"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'رمز عبور جدید خود را وارد کنید',
#             'autocomplete': 'new-password'
#         }),
#         help_text=_(
#             "رمز عبور باید حداقل ۸ کاراکتر داشته و ترکیبی از حروف و اعداد باشد."
#         ),
#         error_messages={
#             'required': 'لطفاً رمز عبور جدید را وارد کنید'
#         }
#     )
#     new_password2 = forms.CharField(
#         label=_("تکرار رمز عبور جدید"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'رمز عبور جدید خود را تکرار کنید',
#             'autocomplete': 'new-password'
#         }),
#         error_messages={
#             'required': 'لطفاً تکرار رمز عبور جدید را وارد کنید'
#         }
#     )
#
#     def clean_new_password1(self):
#         password1 = self.cleaned_data.get('new_password1')
#
#         # بررسی حداقل طول
#         if len(password1) < 8:
#             raise ValidationError("رمز عبور باید حداقل ۸ کاراکتر باشد.")
#
#         # بررسی وجود حروف
#         if not re.search(r'[a-zA-Zآ-ی]', password1):
#             raise ValidationError("رمز عبور باید شامل حداقل یک حرف باشد.")
#
#         # بررسی وجود اعداد
#         if not re.search(r'\d', password1):
#             raise ValidationError("رمز عبور باید شامل حداقل یک عدد باشد.")
#
#         return password1
#
#     def clean(self):
#         cleaned_data = super().clean()
#         password1 = cleaned_data.get('new_password1')
#         password2 = cleaned_data.get('new_password2')
#
#         if password1 and password2 and password1 != password2:
#             raise ValidationError({
#                 'new_password2': 'رمز عبورهای وارد شده یکسان نیستند'
#             })
#
#         return cleaned_data
#
#
# class CustomPasswordResetForm(PasswordResetForm):
#     """
#     فرم سفارشی درخواست بازنشانی رمز عبور
#     """
#     phone = forms.CharField(
#         label=_("شماره تلفن همراه"),
#         max_length=15,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'شماره تلفن همراه خود را وارد کنید',
#             'autocomplete': 'tel'
#         }),
#         error_messages={
#             'required': 'لطفاً شماره تلفن همراه را وارد کنید'
#         }
#     )
#
#     def clean_phone(self):
#         phone = self.cleaned_data.get('phone')
#
#         # استفاده از ولیدیتور مدل برای بررسی شماره تلفن
#         from .validators import validate_iranian_mobile
#         try:
#             phone = validate_iranian_mobile(phone)
#         except ValidationError:
#             raise ValidationError("شماره تلفن همراه معتبر نیست.")
#
#         # بررسی وجود کاربر با این شماره تلفن
#         if not User.objects.filter(phone=phone, is_active=True).exists():
#             raise ValidationError("کاربری با این شماره تلفن یافت نشد.")
#
#         return phone
#
#     def get_users(self, phone):
#         """بازگرداندن کاربران بر اساس شماره تلفن"""
#         return User.objects.filter(phone=phone, is_active=True)
#
#
# class CustomSetPasswordForm(SetPasswordForm):
#     """
#     فرم سفارشی تنظیم رمز عبور جدید
#     """
#     new_password1 = forms.CharField(
#         label=_("رمز عبور جدید"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'رمز عبور جدید خود را وارد کنید',
#             'autocomplete': 'new-password'
#         }),
#         help_text=_(
#             "رمز عبور باید حداقل ۸ کاراکتر داشته و ترکیبی از حروف و اعداد باشد."
#         ),
#         error_messages={
#             'required': 'لطفاً رمز عبور جدید را وارد کنید'
#         }
#     )
#     new_password2 = forms.CharField(
#         label=_("تکرار رمز عبور جدید"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'رمز عبور جدید خود را تکرار کنید',
#             'autocomplete': 'new-password'
#         }),
#         error_messages={
#             'required': 'لطفاً تکرار رمز عبور جدید را وارد کنید'
#         }
#     )
#
#     def clean_new_password1(self):
#         password1 = self.cleaned_data.get('new_password1')
#
#         # بررسی حداقل طول
#         if len(password1) < 8:
#             raise ValidationError("رمز عبور باید حداقل ۸ کاراکتر باشد.")
#
#         # بررسی وجود حروف
#         if not re.search(r'[a-zA-Zآ-ی]', password1):
#             raise ValidationError("رمز عبور باید شامل حداقل یک حرف باشد.")
#
#         # بررسی وجود اعداد
#         if not re.search(r'\d', password1):
#             raise ValidationError("رمز عبور باید شامل حداقل یک عدد باشد.")
#
#         return password1
#
#     def clean(self):
#         cleaned_data = super().clean()
#         password1 = cleaned_data.get('new_password1')
#         password2 = cleaned_data.get('new_password2')
#
#         if password1 and password2 and password1 != password2:
#             raise ValidationError({
#                 'new_password2': 'رمز عبورهای وارد شده یکسان نیستند'
#             })
#
#         return cleaned_data
#
# class UserProfileForm(forms.ModelForm):
#     """
#     فرم سفارشی برای ویرایش پروفایل کاربر
#     """
#     class Meta:
#         model = UserProfile  # تغییر از CustomUser به UserProfile
#         fields = ['first_name', 'last_name', 'birth_date', 'avatar', 'country',
#                   'province', 'city', 'address', 'postal_code', 'email',
#                   'emergency_contact', 'email_notifications', 'sms_notifications']
#         labels = {
#             'first_name': _('نام'),
#             'last_name': _('نام خانوادگی'),
#             'email': _('ایمیل'),
#         }
#         widgets = {
#             'first_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'نام خود را وارد کنید'
#             }),
#             'last_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'نام خانوادگی خود را وارد کنید'
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'ایمیل خود را وارد کنید'
#             }),
#         }
#         error_messages = {
#             'first_name': {
#                 'max_length': 'نام نمی‌تواند بیش از ۱۵۰ کاراکتر باشد'
#             },
#             'last_name': {
#                 'max_length': 'نام خانوادگی نمی‌تواند بیش از ۱۵۰ کاراکتر باشد'
#             },
#             'email': {
#                 'invalid': 'فرمت ایمیل نامعتبر است'
#             }
#         }
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
#             raise ValidationError("این ایمیل قبلاً ثبت شده است")
#         return email
#
#
# class ProfileEditForm(forms.ModelForm):
#     # اعتبارسنجی اختیاری برای کد پستی
#     postal_code_validator = RegexValidator(
#         regex=r'^\d{10}$',
#         message='کد پستی باید 10 رقم باشد.',
#         code='invalid_postal_code'
#     )
#
#     class Meta:
#         model = UserProfile
#         fields = [
#             'first_name', 'last_name', 'birth_date', 'avatar',
#             'country', 'province', 'city', 'address', 'postal_code',
#             'email', 'emergency_contact',
#             'email_notifications', 'sms_notifications'
#         ]
#         widgets = {
#             'first_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'نام'
#             }),
#             'last_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'نام خانوادگی'
#             }),
#             'birth_date': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date',
#                 'placeholder': 'تاریخ تولد'
#             }),
#             'avatar': forms.ClearableFileInput(attrs={
#                 'class': 'form-control'
#             }),
#             'country': forms.Select(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'کشور'
#             }),
#             'province': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'استان'
#             }),
#             'city': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'شهر'
#             }),
#             'address': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'آدرس کامل'
#             }),
#             'postal_code': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'کد پستی',
#                 'maxlength': 10
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'ایمیل'
#             }),
#             'emergency_contact': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'شماره تماس اضطراری'
#             }),
#             'email_notifications': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'sms_notifications': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#         }
#         labels = {
#             'first_name': _('نام'),
#             'last_name': _('نام خانوادگی'),
#             'birth_date': _('تاریخ تولد'),
#             'avatar': _('تصویر پروفایل'),
#             'country': _('کشور'),
#             'province': _('استان'),
#             'city': _('شهر'),
#             'address': _('آدرس'),
#             'postal_code': _('کد پستی'),
#             'email': _('ایمیل'),
#             'emergency_contact': _('تماس اضطراری'),
#             'email_notifications': _('اعلان‌های ایمیلی'),
#             'sms_notifications': _('اعلان‌های پیامکی'),
#         }
#         help_texts = {
#             'avatar': _('تصویری با کیفیت مناسب انتخاب کنید'),
#             'email': _('ایمیل خود را برای دریافت اطلاعیه‌ها وارد کنید'),
#             'emergency_contact': _('شماره تماسی برای مواقع ضروری'),
#         }
#
#     def __init__(self, *args, **kwargs):
#         # خارج کردن پارامتر user از kwargs قبل از فراخوانی super
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#         # اضافه کردن اعتبارسنجی به فیلد postal_code
#         self.fields['postal_code'].validators.append(self.postal_code_validator)
#
#         # غیرفعال کردن فیلد ایمیل اگر قبلاً پر شده است
#         if self.instance and self.instance.email:
#             self.fields['email'].disabled = True
#             self.fields['email'].help_text = _('برای تغییر ایمیل با پشتیبانی تماس بگیرید')
#
#     def clean_postal_code(self):
#         postal_code = self.cleaned_data.get('postal_code')
#         if postal_code and len(postal_code) != 10:
#             raise forms.ValidationError(_('کد پستی باید دقیقاً 10 رقم باشد'))
#         return postal_code
#
#     def clean_emergency_contact(self):
#         emergency_contact = self.cleaned_data.get('emergency_contact')
#         if emergency_contact and not emergency_contact.isdigit():
#             raise forms.ValidationError(_('شماره تماس اضطراری باید فقط شامل اعداد باشد'))
#         return emergency_contact
#
#
# def _handle_invalid_form(self, request, form):
#     """مدیریت فرم نامعتبر با پیام‌های دقیق‌تر"""
#     if 'phone' in form.errors:
#         if 'unique' in form.errors['phone']:
#             messages.error(request, 'این شماره تلفن قبلاً ثبت شده است.')
#         else:
#             messages.error(request, 'لطفاً شماره تلفن معتبر وارد کنید.')
#
#     if 'password' in form.errors:
#         messages.error(request, 'رمز عبور باید حداقل ۸ کاراکتر و شامل حروف و اعداد باشد.')
#
#     return render(request, self.template_name, {'form': form})
#
#
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from .models import CustomUser
#
# class CustomUserCreationForm(UserCreationForm):
#     class Meta(UserCreationForm.Meta):
#         model = CustomUser
#         fields = ('phone',)  # فقط شماره تلفن برای ایجاد کاربر
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # حذف فیلد username از فرم
#         if 'username' in self.fields:
#             del self.fields['username']
#
# class CustomUserChangeForm(UserChangeForm):
#     class Meta:
#         model = CustomUser
#         fields = '__all__'
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # حذف فیلد username از فرم
#         if 'username' in self.fields:
#             del self.fields['username']
#
#
# class ChangePhoneNumberForm(forms.Form):
#     """
#     فرم تغییر شماره تلفن
#     """
#     new_phone_number = forms.CharField(
#         max_length=15,
#         validators=[validate_iranian_mobile],
#         label=_('شماره تلفن جدید'),
#         widget=forms.TextInput(attrs={
#             'placeholder': '09xxxxxxxxx',
#             'class': 'form-control'
#         })
#     )
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#     def clean_new_phone_number(self):
#         new_phone = self.cleaned_data['new_phone_number']
#
#         # بررسی تکراری نبودن شماره
#         if CustomUser.objects.filter(phone_number=new_phone).exclude(pk=self.user.pk).exists():
#             raise forms.ValidationError(_('این شماره تلفن قبلاً ثبت شده است.'))
#
#         # بررسی اینکه شماره جدید با شماره فعلی متفاوت باشد
#         if self.user and new_phone == self.user.phone_number:
#             raise forms.ValidationError(_('شماره جدید با شماره فعلی یکسان است.'))
#
#         return new_phone
#
#
# class VerifyPhoneChangeForm(forms.Form):
#     """
#     فرم تأیید کد OTP برای تغییر شماره تلفن
#     """
#     verification_code = forms.CharField(
#         max_length=6,
#         min_length=6,
#         label=_('کد تأیید'),
#         widget=forms.TextInput(attrs={
#             'placeholder': '123456',
#             'class': 'form-control',
#             'maxlength': '6'
#         }),
#         validators=[
#             RegexValidator(
#                 regex='^[0-9]{6}$',
#                 message=_('کد تأیید باید ۶ رقم عددی باشد.')
#             )
#         ]
#     )
#
#
# # accounts/forms.py
# from django import forms
# from django.core.validators import RegexValidator
# from django.utils.translation import gettext as _
# from .models import CustomUser
# from .validators import validate_iranian_mobile
#
#
# class ChangePhoneNumberForm(forms.Form):
#     """
#     فرم تغییر شماره تلفن
#     """
#     new_phone_number = forms.CharField(
#         max_length=15,
#         validators=[validate_iranian_mobile],
#         label=_('شماره تلفن جدید'),
#         widget=forms.TextInput(attrs={
#             'placeholder': '09xxxxxxxxx',
#             'class': 'form-control'
#         })
#     )
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#     def clean_new_phone_number(self):
#         new_phone = self.cleaned_data['new_phone_number']
#
#         # بررسی تکراری نبودن شماره
#         if CustomUser.objects.filter(phone_number=new_phone).exclude(pk=self.user.pk).exists():
#             raise forms.ValidationError(_('این شماره تلفن قبلاً ثبت شده است.'))
#
#         # بررسی اینکه شماره جدید با شماره فعلی متفاوت باشد
#         if self.user and new_phone == self.user.phone_number:
#             raise forms.ValidationError(_('شماره جدید با شماره فعلی یکسان است.'))
#
#         return new_phone
#
#
# class VerifyPhoneChangeForm(forms.Form):
#     """
#     فرم تأیید کد OTP برای تغییر شماره تلفن
#     """
#     verification_code = forms.CharField(
#         max_length=6,
#         min_length=6,
#         label=_('کد تأیید'),
#         widget=forms.TextInput(attrs={
#             'placeholder': '123456',
#             'class': 'form-control',
#             'maxlength': '6'
#         }),
#         validators=[
#             RegexValidator(
#                 regex='^[0-9]{6}$',
#                 message=_('کد تأیید باید ۶ رقم عددی باشد.')
#             )
#         ]
#     )













# from django import forms
# from .models import UserProfile
# from django.contrib.auth import get_user_model
#
# User = get_user_model()
#
#
# class ProfileEditForm(forms.ModelForm):
#     class Meta:
#         model = UserProfile
#         fields = [
#             'first_name', 'last_name', 'birth_date', 'avatar',
#             'country', 'province', 'city', 'address', 'postal_code',
#             'email', 'emergency_contact', 'email_notifications', 'sms_notifications'
#         ]
#         widgets = {
#             'birth_date': forms.DateInput(attrs={'type': 'date'}),
#             'address': forms.Textarea(attrs={'rows': 3}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if email:
#             # بررسی یکتا بودن ایمیل (به جز برای کاربر فعلی)
#             if UserProfile.objects.exclude(user=self.user).filter(email=email).exists():
#                 raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
#         return email