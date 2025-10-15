# # forms.py
# pages/forms.py
from django import forms
from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام شما *'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل شما *'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'موضوع *'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'متن پیام شما *'}),
        }



# from django import forms
# from .models import ContactUs
#
# class ContactUsForm(forms.ModelForm):
#     class Meta:
#         model = ContactUs
#         fields = ['name', 'email', 'subject', 'message']
#         widgets = {
#             'message': forms.Textarea(attrs={'rows': 6, 'placeholder': 'متن پیام شما *'}),
#         }
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if not email:
#             raise forms.ValidationError('ایمیل نمی‌تواند خالی باشد.')
#         return email
# from django import forms
# from .models import ContactMessage
#
#
# class ContactForm(forms.ModelForm):
#     class Meta:
#         model = ContactMessage
#         fields = ['name', 'email', 'phone', 'subject', 'message']
#         widgets = {
#             'name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'نام شما *',
#                 'required': True
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'ایمیل شما *',
#                 'required': True
#             }),
#             'phone': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'تلفن *',
#                 'required': True
#             }),
#             'subject': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'موضوع *',
#                 'required': True
#             }),
#             'message': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'متن پیام شما *',
#                 'rows': 6,
#                 'required': True
#             }),
#         }
#         labels = {
#             'name': 'نام',
#             'email': 'ایمیل',
#             'phone': 'تلفن',
#             'subject': 'موضوع',
#             'message': 'پیام',
#         }
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#         # Pre-fill form with user data if available
#         if self.user and self.user.is_authenticated:
#             if hasattr(self.user, 'profile'):
#                 profile = self.user.profile
#                 if profile.first_name and profile.last_name:
#                     self.fields['name'].initial = f"{profile.first_name} {profile.last_name}"
#                 elif profile.first_name:
#                     self.fields['name'].initial = profile.first_name
#
#                 if profile.email:
#                     self.fields['email'].initial = profile.email
#                 elif self.user.email:
#                     self.fields['email'].initial = self.user.email
#
#                 if profile.phone:
#                     self.fields['phone'].initial = profile.phone
#                 else:
#                     self.fields['phone'].initial = self.user.phone
#             else:
#                 self.fields['phone'].initial = self.user.phone
#                 if self.user.email:
#                     self.fields['email'].initial = self.user.email
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if email and not email.strip():
#             raise forms.ValidationError('لطفاً ایمیل خود را وارد کنید.')
#         return email
#
#     def clean_message(self):
#         message = self.cleaned_data.get('message')
#         if len(message.strip()) < 10:
#             raise forms.ValidationError('پیام باید حداقل ۱۰ کاراکتر داشته باشد.')
#         return message