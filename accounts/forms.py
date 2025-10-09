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
        label=_('Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡'),
        max_length=11,
        validators=[lambda x: validate_iranian_mobile(x, 'database')],
        widget=forms.TextInput(attrs={
            'placeholder': '09xxxxxxxxx',
            'class': 'form-control',
            'autocomplete': 'phone'
        })
    )

    email = forms.EmailField(
        label='Ø§ÛŒÙ…ÛŒÙ„ (Ø§Ø®ØªÛŒØ§Ø±ÛŒ)',
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@domain.com',
            'class': 'form-control'
        })
    )

    password = forms.CharField(
        label=_('Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ±',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )

    confirm_password = forms.CharField(
        label=_('ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    terms_accepted = forms.BooleanField(  # Ù†Ø§Ù… ÙÛŒÙ„Ø¯ Ø¨Ø§ÛŒØ¯ Ø¨Ø§ HTML Ù…Ø·Ø§Ø¨Ù‚Øª Ø¯Ø§Ø´ØªÙ‡ Ø¨Ø§Ø´Ø¯
        label='Ù…ÙˆØ§ÙÙ‚Øª Ø¨Ø§ Ø´Ø±Ø§ÛŒØ· Ø§Ø³ØªÙØ§Ø¯Ù‡',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Ù„Ø·ÙØ§Ù‹ Ø´Ø±Ø§ÛŒØ· Ø§Ø³ØªÙØ§Ø¯Ù‡ Ø±Ø§ Ø¨Ù¾Ø°ÛŒØ±ÛŒØ¯'}

    )

    # privacy_policy_accepted = forms.BooleanField(
    #     label=_('Ù…ÙˆØ§ÙÙ‚Øª Ø¨Ø§ Ø­Ø±ÛŒÙ… Ø®ØµÙˆØµÛŒ'),
    #     widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    #     error_messages={'required': _('Ù„Ø·ÙØ§Ù‹ Ø­Ø±ÛŒÙ… Ø®ØµÙˆØµÛŒ Ø±Ø§ Ø¨Ù¾Ø°ÛŒØ±ÛŒØ¯')}
    # )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _('Passwords do not match.'))

        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        try:
            validated_phone = validate_iranian_mobile(phone)

            if CustomUser.objects.filter(phone=validated_phone).exists():
                raise ValidationError(_('This phone number is already registered.'))

            if password and confirm_password and password != confirm_password:
                raise ValidationError(_('Passwords do not match.'))

            return validated_phone
        except ValidationError as exc:
            raise ValidationError(exc.messages[0] if exc.messages else _('Enter a valid phone number.'))


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label=_('Ú©Ø¯ ØªØ£ÛŒÛŒØ¯'),
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
        label='Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡',
        validators=[validate_iranian_mobile],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09xxxxxxxxx'
        })
    )

    password = forms.CharField(
        label='Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        label='Ù…Ø±Ø§ Ø¨Ù‡ Ø®Ø§Ø·Ø± Ø¨Ø³Ù¾Ø§Ø±',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

#
# class ForgotPasswordForm(forms.Form):
#     phone = forms.CharField(
#         max_length=15,
#         label=_('Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡'),
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
#         label=_('Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯'),
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ±',
#             'autocomplete': 'new-password'
#         }),
#         min_length=8
#     )
#
#     confirm_password = forms.CharField(
#         label=_('ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯'),
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯',
#             'autocomplete': 'new-password'
#         })
#     )
#
#     def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _('Passwords do not match.'))

        return cleaned_data
#
#
class ResendOTPForm(forms.Form):
    """
    ÙØ±Ù… Ø³Ø§Ø¯Ù‡ Ø¨Ø±Ø§ÛŒ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ OTP
    Ø§ÛŒÙ† ÙØ±Ù… Ù…Ø¹Ù…ÙˆÙ„Ø§Ù‹ Ø§Ø² Ø·Ø±ÛŒÙ‚ AJAX Ø§Ø±Ø³Ø§Ù„ Ù…ÛŒâ€ŒØ´ÙˆØ¯
    """
    pass  # Ù‡ÛŒÚ† ÙÛŒÙ„Ø¯ÛŒ Ù†ÛŒØ§Ø² Ù†ÛŒØ³ØªØŒ ÙÙ‚Ø· Ø¯Ú©Ù…Ù‡ Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯


class PasswordResetRequestForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        label='Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡',
        validators=[validate_iranian_mobile],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09xxxxxxxxx'
        })
    )



# class PasswordResetConfirmForm(forms.Form):
#     new_password = forms.CharField(
#         label='Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯'
#         }),
#         min_length=8
#     )
#     confirm_password = forms.CharField(
#         label='ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯'
#         })
#     )
#
#     def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _('Passwords do not match.'))

        return cleaned_data
#
#
#
#
#
#
#
# class CustomPasswordChangeForm(PasswordChangeForm):
#     """
#     ÙØ±Ù… Ø³ÙØ§Ø±Ø´ÛŒ ØªØºÛŒÛŒØ± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±
#     """
#     old_password = forms.CharField(
#         label=_("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± ÙØ¹Ù„ÛŒ"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± ÙØ¹Ù„ÛŒ Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯',
#             'autocomplete': 'current-password'
#         }),
#         error_messages={
#             'required': 'Ù„Ø·ÙØ§Ù‹ Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± ÙØ¹Ù„ÛŒ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#         }
#     )
#     new_password1 = forms.CharField(
#         label=_("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯',
#             'autocomplete': 'new-password'
#         }),
#         help_text=_(
#             "Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ± Ø¯Ø§Ø´ØªÙ‡ Ùˆ ØªØ±Ú©ÛŒØ¨ÛŒ Ø§Ø² Ø­Ø±ÙˆÙ Ùˆ Ø§Ø¹Ø¯Ø§Ø¯ Ø¨Ø§Ø´Ø¯."
#         ),
#         error_messages={
#             'required': 'Ù„Ø·ÙØ§Ù‹ Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#         }
#     )
#     new_password2 = forms.CharField(
#         label=_("ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø®ÙˆØ¯ Ø±Ø§ ØªÚ©Ø±Ø§Ø± Ú©Ù†ÛŒØ¯',
#             'autocomplete': 'new-password'
#         }),
#         error_messages={
#             'required': 'Ù„Ø·ÙØ§Ù‹ ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#         }
#     )
#
#     def clean_new_password1(self):
#         password1 = self.cleaned_data.get('new_password1')
#
#         # Ø¨Ø±Ø±Ø³ÛŒ Ø­Ø¯Ø§Ù‚Ù„ Ø·ÙˆÙ„
#         if len(password1) < 8:
#             raise ValidationError("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ± Ø¨Ø§Ø´Ø¯.")
#
#         # Ø¨Ø±Ø±Ø³ÛŒ ÙˆØ¬ÙˆØ¯ Ø­Ø±ÙˆÙ
#         if not re.search(r'[a-zA-ZØ¢-ÛŒ]', password1):
#             raise ValidationError("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø´Ø§Ù…Ù„ Ø­Ø¯Ø§Ù‚Ù„ ÛŒÚ© Ø­Ø±Ù Ø¨Ø§Ø´Ø¯.")
#
#         # Ø¨Ø±Ø±Ø³ÛŒ ÙˆØ¬ÙˆØ¯ Ø§Ø¹Ø¯Ø§Ø¯
#         if not re.search(r'\d', password1):
#             raise ValidationError("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø´Ø§Ù…Ù„ Ø­Ø¯Ø§Ù‚Ù„ ÛŒÚ© Ø¹Ø¯Ø¯ Ø¨Ø§Ø´Ø¯.")
#
#         return password1
#
#     def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _('Passwords do not match.'))

        return cleaned_data
#
#
# class CustomPasswordResetForm(PasswordResetForm):
#     """
#     ÙØ±Ù… Ø³ÙØ§Ø±Ø´ÛŒ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ø¨Ø§Ø²Ù†Ø´Ø§Ù†ÛŒ Ø±Ù…Ø² Ø¹Ø¨ÙˆØ±
#     """
#     phone = forms.CharField(
#         label=_("Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡"),
#         max_length=15,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡ Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯',
#             'autocomplete': 'tel'
#         }),
#         error_messages={
#             'required': 'Ù„Ø·ÙØ§Ù‹ Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#         }
#     )
#
#     def clean_phone(self):
#         phone = self.cleaned_data.get('phone')
#
#         # Ø§Ø³ØªÙØ§Ø¯Ù‡ Ø§Ø² ÙˆÙ„ÛŒØ¯ÛŒØªÙˆØ± Ù…Ø¯Ù„ Ø¨Ø±Ø§ÛŒ Ø¨Ø±Ø±Ø³ÛŒ Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
#         from .validators import validate_iranian_mobile
#         try:
#             phone = validate_iranian_mobile(phone)
#         except ValidationError:
#             raise ValidationError("Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‡Ù…Ø±Ø§Ù‡ Ù…Ø¹ØªØ¨Ø± Ù†ÛŒØ³Øª.")
#
#         # Ø¨Ø±Ø±Ø³ÛŒ ÙˆØ¬ÙˆØ¯ Ú©Ø§Ø±Ø¨Ø± Ø¨Ø§ Ø§ÛŒÙ† Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
#         if not User.objects.filter(phone=phone, is_active=True).exists():
#             raise ValidationError("Ú©Ø§Ø±Ø¨Ø±ÛŒ Ø¨Ø§ Ø§ÛŒÙ† Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† ÛŒØ§ÙØª Ù†Ø´Ø¯.")
#
#         return phone
#
#     def get_users(self, phone):
#         """Ø¨Ø§Ø²Ú¯Ø±Ø¯Ø§Ù†Ø¯Ù† Ú©Ø§Ø±Ø¨Ø±Ø§Ù† Ø¨Ø± Ø§Ø³Ø§Ø³ Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†"""
#         return User.objects.filter(phone=phone, is_active=True)
#
#
# class CustomSetPasswordForm(SetPasswordForm):
#     """
#     ÙØ±Ù… Ø³ÙØ§Ø±Ø´ÛŒ ØªÙ†Ø¸ÛŒÙ… Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯
#     """
#     new_password1 = forms.CharField(
#         label=_("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯',
#             'autocomplete': 'new-password'
#         }),
#         help_text=_(
#             "Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ± Ø¯Ø§Ø´ØªÙ‡ Ùˆ ØªØ±Ú©ÛŒØ¨ÛŒ Ø§Ø² Ø­Ø±ÙˆÙ Ùˆ Ø§Ø¹Ø¯Ø§Ø¯ Ø¨Ø§Ø´Ø¯."
#         ),
#         error_messages={
#             'required': 'Ù„Ø·ÙØ§Ù‹ Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#         }
#     )
#     new_password2 = forms.CharField(
#         label=_("ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø®ÙˆØ¯ Ø±Ø§ ØªÚ©Ø±Ø§Ø± Ú©Ù†ÛŒØ¯',
#             'autocomplete': 'new-password'
#         }),
#         error_messages={
#             'required': 'Ù„Ø·ÙØ§Ù‹ ØªÚ©Ø±Ø§Ø± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¬Ø¯ÛŒØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#         }
#     )
#
#     def clean_new_password1(self):
#         password1 = self.cleaned_data.get('new_password1')
#
#         # Ø¨Ø±Ø±Ø³ÛŒ Ø­Ø¯Ø§Ù‚Ù„ Ø·ÙˆÙ„
#         if len(password1) < 8:
#             raise ValidationError("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ± Ø¨Ø§Ø´Ø¯.")
#
#         # Ø¨Ø±Ø±Ø³ÛŒ ÙˆØ¬ÙˆØ¯ Ø­Ø±ÙˆÙ
#         if not re.search(r'[a-zA-ZØ¢-ÛŒ]', password1):
#             raise ValidationError("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø´Ø§Ù…Ù„ Ø­Ø¯Ø§Ù‚Ù„ ÛŒÚ© Ø­Ø±Ù Ø¨Ø§Ø´Ø¯.")
#
#         # Ø¨Ø±Ø±Ø³ÛŒ ÙˆØ¬ÙˆØ¯ Ø§Ø¹Ø¯Ø§Ø¯
#         if not re.search(r'\d', password1):
#             raise ValidationError("Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø´Ø§Ù…Ù„ Ø­Ø¯Ø§Ù‚Ù„ ÛŒÚ© Ø¹Ø¯Ø¯ Ø¨Ø§Ø´Ø¯.")
#
#         return password1
#
#     def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _('Passwords do not match.'))

        return cleaned_data
#
# class UserProfileForm(forms.ModelForm):
#     """
#     ÙØ±Ù… Ø³ÙØ§Ø±Ø´ÛŒ Ø¨Ø±Ø§ÛŒ ÙˆÛŒØ±Ø§ÛŒØ´ Ù¾Ø±ÙˆÙØ§ÛŒÙ„ Ú©Ø§Ø±Ø¨Ø±
#     """
#     class Meta:
#         model = UserProfile  # ØªØºÛŒÛŒØ± Ø§Ø² CustomUser Ø¨Ù‡ UserProfile
#         fields = ['first_name', 'last_name', 'birth_date', 'avatar', 'country',
#                   'province', 'city', 'address', 'postal_code', 'email',
#                   'emergency_contact', 'email_notifications', 'sms_notifications']
#         labels = {
#             'first_name': _('Ù†Ø§Ù…'),
#             'last_name': _('Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ'),
#             'email': _('Ø§ÛŒÙ…ÛŒÙ„'),
#         }
#         widgets = {
#             'first_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ù†Ø§Ù… Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#             }),
#             'last_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ø§ÛŒÙ…ÛŒÙ„ Ø®ÙˆØ¯ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'
#             }),
#         }
#         error_messages = {
#             'first_name': {
#                 'max_length': 'Ù†Ø§Ù… Ù†Ù…ÛŒâ€ŒØªÙˆØ§Ù†Ø¯ Ø¨ÛŒØ´ Ø§Ø² Û±ÛµÛ° Ú©Ø§Ø±Ø§Ú©ØªØ± Ø¨Ø§Ø´Ø¯'
#             },
#             'last_name': {
#                 'max_length': 'Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ Ù†Ù…ÛŒâ€ŒØªÙˆØ§Ù†Ø¯ Ø¨ÛŒØ´ Ø§Ø² Û±ÛµÛ° Ú©Ø§Ø±Ø§Ú©ØªØ± Ø¨Ø§Ø´Ø¯'
#             },
#             'email': {
#                 'invalid': 'ÙØ±Ù…Øª Ø§ÛŒÙ…ÛŒÙ„ Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª'
#             }
#         }
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
#             raise ValidationError("Ø§ÛŒÙ† Ø§ÛŒÙ…ÛŒÙ„ Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø§Ø³Øª")
#         return email
#
#
# class ProfileEditForm(forms.ModelForm):
#     # Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ø§Ø®ØªÛŒØ§Ø±ÛŒ Ø¨Ø±Ø§ÛŒ Ú©Ø¯ Ù¾Ø³ØªÛŒ
#     postal_code_validator = RegexValidator(
#         regex=r'^\d{10}$',
#         message='Ú©Ø¯ Ù¾Ø³ØªÛŒ Ø¨Ø§ÛŒØ¯ 10 Ø±Ù‚Ù… Ø¨Ø§Ø´Ø¯.',
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
#                 'placeholder': 'Ù†Ø§Ù…'
#             }),
#             'last_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ'
#             }),
#             'birth_date': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date',
#                 'placeholder': 'ØªØ§Ø±ÛŒØ® ØªÙˆÙ„Ø¯'
#             }),
#             'avatar': forms.ClearableFileInput(attrs={
#                 'class': 'form-control'
#             }),
#             'country': forms.Select(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ú©Ø´ÙˆØ±'
#             }),
#             'province': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ø§Ø³ØªØ§Ù†'
#             }),
#             'city': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ø´Ù‡Ø±'
#             }),
#             'address': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Ø¢Ø¯Ø±Ø³ Ú©Ø§Ù…Ù„'
#             }),
#             'postal_code': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ú©Ø¯ Ù¾Ø³ØªÛŒ',
#                 'maxlength': 10
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ø§ÛŒÙ…ÛŒÙ„'
#             }),
#             'emergency_contact': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ø´Ù…Ø§Ø±Ù‡ ØªÙ…Ø§Ø³ Ø§Ø¶Ø·Ø±Ø§Ø±ÛŒ'
#             }),
#             'email_notifications': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'sms_notifications': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#         }
#         labels = {
#             'first_name': _('Ù†Ø§Ù…'),
#             'last_name': _('Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ'),
#             'birth_date': _('ØªØ§Ø±ÛŒØ® ØªÙˆÙ„Ø¯'),
#             'avatar': _('ØªØµÙˆÛŒØ± Ù¾Ø±ÙˆÙØ§ÛŒÙ„'),
#             'country': _('Ú©Ø´ÙˆØ±'),
#             'province': _('Ø§Ø³ØªØ§Ù†'),
#             'city': _('Ø´Ù‡Ø±'),
#             'address': _('Ø¢Ø¯Ø±Ø³'),
#             'postal_code': _('Ú©Ø¯ Ù¾Ø³ØªÛŒ'),
#             'email': _('Ø§ÛŒÙ…ÛŒÙ„'),
#             'emergency_contact': _('ØªÙ…Ø§Ø³ Ø§Ø¶Ø·Ø±Ø§Ø±ÛŒ'),
#             'email_notifications': _('Ø§Ø¹Ù„Ø§Ù†â€ŒÙ‡Ø§ÛŒ Ø§ÛŒÙ…ÛŒÙ„ÛŒ'),
#             'sms_notifications': _('Ø§Ø¹Ù„Ø§Ù†â€ŒÙ‡Ø§ÛŒ Ù¾ÛŒØ§Ù…Ú©ÛŒ'),
#         }
#         help_texts = {
#             'avatar': _('ØªØµÙˆÛŒØ±ÛŒ Ø¨Ø§ Ú©ÛŒÙÛŒØª Ù…Ù†Ø§Ø³Ø¨ Ø§Ù†ØªØ®Ø§Ø¨ Ú©Ù†ÛŒØ¯'),
#             'email': _('Ø§ÛŒÙ…ÛŒÙ„ Ø®ÙˆØ¯ Ø±Ø§ Ø¨Ø±Ø§ÛŒ Ø¯Ø±ÛŒØ§ÙØª Ø§Ø·Ù„Ø§Ø¹ÛŒÙ‡â€ŒÙ‡Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯'),
#             'emergency_contact': _('Ø´Ù…Ø§Ø±Ù‡ ØªÙ…Ø§Ø³ÛŒ Ø¨Ø±Ø§ÛŒ Ù…ÙˆØ§Ù‚Ø¹ Ø¶Ø±ÙˆØ±ÛŒ'),
#         }
#
#     def __init__(self, *args, **kwargs):
#         # Ø®Ø§Ø±Ø¬ Ú©Ø±Ø¯Ù† Ù¾Ø§Ø±Ø§Ù…ØªØ± user Ø§Ø² kwargs Ù‚Ø¨Ù„ Ø§Ø² ÙØ±Ø§Ø®ÙˆØ§Ù†ÛŒ super
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#         # Ø§Ø¶Ø§ÙÙ‡ Ú©Ø±Ø¯Ù† Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ø¨Ù‡ ÙÛŒÙ„Ø¯ postal_code
#         self.fields['postal_code'].validators.append(self.postal_code_validator)
#
#         # ØºÛŒØ±ÙØ¹Ø§Ù„ Ú©Ø±Ø¯Ù† ÙÛŒÙ„Ø¯ Ø§ÛŒÙ…ÛŒÙ„ Ø§Ú¯Ø± Ù‚Ø¨Ù„Ø§Ù‹ Ù¾Ø± Ø´Ø¯Ù‡ Ø§Ø³Øª
#         if self.instance and self.instance.email:
#             self.fields['email'].disabled = True
#             self.fields['email'].help_text = _('Ø¨Ø±Ø§ÛŒ ØªØºÛŒÛŒØ± Ø§ÛŒÙ…ÛŒÙ„ Ø¨Ø§ Ù¾Ø´ØªÛŒØ¨Ø§Ù†ÛŒ ØªÙ…Ø§Ø³ Ø¨Ú¯ÛŒØ±ÛŒØ¯')
#
#     def clean_postal_code(self):
#         postal_code = self.cleaned_data.get('postal_code')
#         if postal_code and len(postal_code) != 10:
#             raise forms.ValidationError(_('Ú©Ø¯ Ù¾Ø³ØªÛŒ Ø¨Ø§ÛŒØ¯ Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ 10 Ø±Ù‚Ù… Ø¨Ø§Ø´Ø¯'))
#         return postal_code
#
#     def clean_emergency_contact(self):
#         emergency_contact = self.cleaned_data.get('emergency_contact')
#         if emergency_contact and not emergency_contact.isdigit():
#             raise forms.ValidationError(_('Ø´Ù…Ø§Ø±Ù‡ ØªÙ…Ø§Ø³ Ø§Ø¶Ø·Ø±Ø§Ø±ÛŒ Ø¨Ø§ÛŒØ¯ ÙÙ‚Ø· Ø´Ø§Ù…Ù„ Ø§Ø¹Ø¯Ø§Ø¯ Ø¨Ø§Ø´Ø¯'))
#         return emergency_contact
#
#
# def _handle_invalid_form(self, request, form):
#     """Ù…Ø¯ÛŒØ±ÛŒØª ÙØ±Ù… Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø¨Ø§ Ù¾ÛŒØ§Ù…â€ŒÙ‡Ø§ÛŒ Ø¯Ù‚ÛŒÙ‚â€ŒØªØ±"""
#     if 'phone' in form.errors:
#         if 'unique' in form.errors['phone']:
#             messages.error(request, 'Ø§ÛŒÙ† Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø§Ø³Øª.')
#         else:
#             messages.error(request, 'Ù„Ø·ÙØ§Ù‹ Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù…Ø¹ØªØ¨Ø± ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯.')
#
#     if 'password' in form.errors:
#         messages.error(request, 'Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ÛŒØ¯ Ø­Ø¯Ø§Ù‚Ù„ Û¸ Ú©Ø§Ø±Ø§Ú©ØªØ± Ùˆ Ø´Ø§Ù…Ù„ Ø­Ø±ÙˆÙ Ùˆ Ø§Ø¹Ø¯Ø§Ø¯ Ø¨Ø§Ø´Ø¯.')
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
#         fields = ('phone',)  # ÙÙ‚Ø· Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ø¨Ø±Ø§ÛŒ Ø§ÛŒØ¬Ø§Ø¯ Ú©Ø§Ø±Ø¨Ø±
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Ø­Ø°Ù ÙÛŒÙ„Ø¯ username Ø§Ø² ÙØ±Ù…
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
#         # Ø­Ø°Ù ÙÛŒÙ„Ø¯ username Ø§Ø² ÙØ±Ù…
#         if 'username' in self.fields:
#             del self.fields['username']
#
#
# class ChangePhoneNumberForm(forms.Form):
#     """
#     ÙØ±Ù… ØªØºÛŒÛŒØ± Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
#     """
#     new_phone_number = forms.CharField(
#         max_length=15,
#         validators=[validate_iranian_mobile],
#         label=_('Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ø¬Ø¯ÛŒØ¯'),
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
#         # Ø¨Ø±Ø±Ø³ÛŒ ØªÚ©Ø±Ø§Ø±ÛŒ Ù†Ø¨ÙˆØ¯Ù† Ø´Ù…Ø§Ø±Ù‡
#         if CustomUser.objects.filter(phone_number=new_phone).exclude(pk=self.user.pk).exists():
#             raise forms.ValidationError(_('Ø§ÛŒÙ† Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø§Ø³Øª.'))
#
#         # Ø¨Ø±Ø±Ø³ÛŒ Ø§ÛŒÙ†Ú©Ù‡ Ø´Ù…Ø§Ø±Ù‡ Ø¬Ø¯ÛŒØ¯ Ø¨Ø§ Ø´Ù…Ø§Ø±Ù‡ ÙØ¹Ù„ÛŒ Ù…ØªÙØ§ÙˆØª Ø¨Ø§Ø´Ø¯
#         if self.user and new_phone == self.user.phone_number:
#             raise forms.ValidationError(_('Ø´Ù…Ø§Ø±Ù‡ Ø¬Ø¯ÛŒØ¯ Ø¨Ø§ Ø´Ù…Ø§Ø±Ù‡ ÙØ¹Ù„ÛŒ ÛŒÚ©Ø³Ø§Ù† Ø§Ø³Øª.'))
#
#         return new_phone
#
#
# class VerifyPhoneChangeForm(forms.Form):
#     """
#     ÙØ±Ù… ØªØ£ÛŒÛŒØ¯ Ú©Ø¯ OTP Ø¨Ø±Ø§ÛŒ ØªØºÛŒÛŒØ± Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
#     """
#     verification_code = forms.CharField(
#         max_length=6,
#         min_length=6,
#         label=_('Ú©Ø¯ ØªØ£ÛŒÛŒØ¯'),
#         widget=forms.TextInput(attrs={
#             'placeholder': '123456',
#             'class': 'form-control',
#             'maxlength': '6'
#         }),
#         validators=[
#             RegexValidator(
#                 regex='^[0-9]{6}$',
#                 message=_('Ú©Ø¯ ØªØ£ÛŒÛŒØ¯ Ø¨Ø§ÛŒØ¯ Û¶ Ø±Ù‚Ù… Ø¹Ø¯Ø¯ÛŒ Ø¨Ø§Ø´Ø¯.')
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
#     ÙØ±Ù… ØªØºÛŒÛŒØ± Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
#     """
#     new_phone_number = forms.CharField(
#         max_length=15,
#         validators=[validate_iranian_mobile],
#         label=_('Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ø¬Ø¯ÛŒØ¯'),
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
#         # Ø¨Ø±Ø±Ø³ÛŒ ØªÚ©Ø±Ø§Ø±ÛŒ Ù†Ø¨ÙˆØ¯Ù† Ø´Ù…Ø§Ø±Ù‡
#         if CustomUser.objects.filter(phone_number=new_phone).exclude(pk=self.user.pk).exists():
#             raise forms.ValidationError(_('Ø§ÛŒÙ† Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ† Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø§Ø³Øª.'))
#
#         # Ø¨Ø±Ø±Ø³ÛŒ Ø§ÛŒÙ†Ú©Ù‡ Ø´Ù…Ø§Ø±Ù‡ Ø¬Ø¯ÛŒØ¯ Ø¨Ø§ Ø´Ù…Ø§Ø±Ù‡ ÙØ¹Ù„ÛŒ Ù…ØªÙØ§ÙˆØª Ø¨Ø§Ø´Ø¯
#         if self.user and new_phone == self.user.phone_number:
#             raise forms.ValidationError(_('Ø´Ù…Ø§Ø±Ù‡ Ø¬Ø¯ÛŒØ¯ Ø¨Ø§ Ø´Ù…Ø§Ø±Ù‡ ÙØ¹Ù„ÛŒ ÛŒÚ©Ø³Ø§Ù† Ø§Ø³Øª.'))
#
#         return new_phone
#
#
# class VerifyPhoneChangeForm(forms.Form):
#     """
#     ÙØ±Ù… ØªØ£ÛŒÛŒØ¯ Ú©Ø¯ OTP Ø¨Ø±Ø§ÛŒ ØªØºÛŒÛŒØ± Ø´Ù…Ø§Ø±Ù‡ ØªÙ„ÙÙ†
#     """
#     verification_code = forms.CharField(
#         max_length=6,
#         min_length=6,
#         label=_('Ú©Ø¯ ØªØ£ÛŒÛŒØ¯'),
#         widget=forms.TextInput(attrs={
#             'placeholder': '123456',
#             'class': 'form-control',
#             'maxlength': '6'
#         }),
#         validators=[
#             RegexValidator(
#                 regex='^[0-9]{6}$',
#                 message=_('Ú©Ø¯ ØªØ£ÛŒÛŒØ¯ Ø¨Ø§ÛŒØ¯ Û¶ Ø±Ù‚Ù… Ø¹Ø¯Ø¯ÛŒ Ø¨Ø§Ø´Ø¯.')
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
#             # Ø¨Ø±Ø±Ø³ÛŒ ÛŒÚ©ØªØ§ Ø¨ÙˆØ¯Ù† Ø§ÛŒÙ…ÛŒÙ„ (Ø¨Ù‡ Ø¬Ø² Ø¨Ø±Ø§ÛŒ Ú©Ø§Ø±Ø¨Ø± ÙØ¹Ù„ÛŒ)
#             if UserProfile.objects.exclude(user=self.user).filter(email=email).exists():
#                 raise forms.ValidationError('Ø§ÛŒÙ† Ø§ÛŒÙ…ÛŒÙ„ Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø§Ø³Øª.')
#         return email


