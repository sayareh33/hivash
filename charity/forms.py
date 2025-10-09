from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    CharityProject,
    ProjectGallery,
    Donation,
    DonationReceipt,
    PaymentTransaction,
    PaymentStatus,
    PaymentGateway
)
from django.conf import settings


class CharityProjectForm(forms.ModelForm):
    class Meta:
        model = CharityProject
        fields = [
            'title', 'slug', 'short_description', 'full_description',
            'target_amount', 'start_date', 'end_date', 'is_featured',
            'is_active', 'image', 'gallery'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'full_description': forms.Textarea(attrs={'rows': 5, 'class': 'editor'}),
        }
        labels = {
            'is_featured': 'پروژه ویژه (در صفحه اصلی نمایش داده شود)',
            'is_active': 'پروژه فعال (برای کاربران قابل مشاهده باشد)',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError("تاریخ پایان باید بعد از تاریخ شروع باشد.")

        return cleaned_data

    def clean_target_amount(self):
        target_amount = self.cleaned_data['target_amount']
        if target_amount < 1000:
            raise ValidationError("مبلغ هدف باید حداقل 1,000 تومان باشد.")
        return target_amount


class ProjectGalleryForm(forms.ModelForm):
    class Meta:
        model = ProjectGallery
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={
                'placeholder': 'توضیح مختصر درباره تصویر (اختیاری)'
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError("حجم تصویر نباید بیشتر از 5 مگابایت باشد.")
            return image
        raise ValidationError("لطفا یک تصویر انتخاب کنید.")


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['project', 'amount', 'is_anonymous', 'message', 'payment_gateway']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'مبلغ به تومان'
            }),
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'پیام حمایتی شما (اختیاری)'
            }),
            'payment_gateway': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # فقط پروژه‌های فعال را نمایش بده
        self.fields['project'].queryset = CharityProject.objects.filter(is_active=True)

        # برای کاربران لاگین کرده، مقدار پیش‌فرض اهداکننده را تنظیم کن
        if user and user.is_authenticated:
            self.fields['is_anonymous'].initial = False
        else:
            self.fields['is_anonymous'].initial = True

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 1000:
            raise ValidationError("مبلغ اهدایی باید حداقل 1,000 تومان باشد.")
        return amount


class DonationAdminForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = '__all__'
        widgets = {
            'donation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_status = cleaned_data.get('payment_status')
        transaction_id = cleaned_data.get('transaction_id')

        if payment_status == PaymentStatus.PAID and not transaction_id:
            raise ValidationError("برای پرداخت موفق باید شناسه تراکنش وارد شود.")

        return cleaned_data


class DonationReceiptForm(forms.ModelForm):
    receipt_number = forms.CharField(
        label='شماره رسید',
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = DonationReceipt
        fields = ['donation', 'receipt_number', 'pdf_file']
        widgets = {
            'donation': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            # تولید خودکار شماره رسید
            last_receipt = DonationReceipt.objects.order_by('-id').first()
            last_number = int(last_receipt.receipt_number.split('-')[-1]) if last_receipt else 0
            self.initial['receipt_number'] = f"REC-{timezone.now().year}-{last_number + 1:05d}"


class PaymentTransactionForm(forms.ModelForm):
    class Meta:
        model = PaymentTransaction
        fields = ['donation', 'amount', 'status', 'gateway', 'transaction_code', 'raw_response']
        widgets = {
            'raw_response': forms.Textarea(attrs={'rows': 4}),
            'donation': forms.Select(attrs={'class': 'select2'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        transaction_code = cleaned_data.get('transaction_code')

        if status in [PaymentStatus.PAID, PaymentStatus.REFUNDED] and not transaction_code:
            raise ValidationError("برای وضعیت‌های پرداخت موفق و عودت داده شده باید کد تراکنش وارد شود.")

        return cleaned_data


class DonationFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'همه وضعیت‌ها')] + PaymentStatus.choices
    GATEWAY_CHOICES = [('', 'همه درگاه‌ها')] + PaymentGateway.choices

    project = forms.ModelChoiceField(
        queryset=CharityProject.objects.all(),
        required=False,
        label='پروژه',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    payment_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='وضعیت پرداخت',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_gateway = forms.ChoiceField(
        choices=GATEWAY_CHOICES,
        required=False,
        label='درگاه پرداخت',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        label='از تاریخ',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        label='تا تاریخ',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    min_amount = forms.IntegerField(
        required=False,
        label='حداقل مبلغ (تومان)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1000'})
    )
    max_amount = forms.IntegerField(
        required=False,
        label='حداکثر مبلغ (تومان)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1000000'})
    )