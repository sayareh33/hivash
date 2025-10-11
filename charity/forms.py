from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from .models import (
    CharityProject,
    ProjectGallery,
    ProjectUpdate,
    ParticipationMethod,
    ImpactStat,
    Donation,
    DonationReceipt,
    PaymentTransaction,
    PaymentStatus,
    PaymentGateway,
)


class CharityProjectForm(forms.ModelForm):
    class Meta:
        model = CharityProject
        fields = [
            'title',
            'slug',
            'short_description',
            'full_description',
            'impact_summary',
            'status',
            'location',
            'beneficiaries_count',
            'hero_video_url',
            'target_amount',
            'current_amount',
            'start_date',
            'end_date',
            'completion_date',
            'is_featured',
            'is_active',
            'image',
            'gallery',
        ]
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'full_description': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'impact_summary': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gallery': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError('تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.')
        return cleaned_data

    def clean_target_amount(self):
        target_amount = self.cleaned_data['target_amount']
        if target_amount < 1000:
            raise ValidationError('مبلغ هدف باید حداقل ۱٬۰۰۰ تومان باشد.')
        return target_amount


class ProjectGalleryForm(forms.ModelForm):
    class Meta:
        model = ProjectGallery
        fields = [
            'media_type',
            'image',
            'video_file',
            'external_url',
            'caption',
            'display_order',
        ]

    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get('media_type')
        image = cleaned_data.get('image')
        video_file = cleaned_data.get('video_file')
        external_url = cleaned_data.get('external_url')

        if media_type == ProjectGallery.MediaType.IMAGE and not image:
            raise ValidationError('برای رسانه تصویری باید فایل تصویر بارگذاری شود.')
        if media_type == ProjectGallery.MediaType.VIDEO and not video_file:
            raise ValidationError('برای رسانه ویدئویی باید فایل ویدئو بارگذاری شود.')
        if media_type == ProjectGallery.MediaType.EXTERNAL and not external_url:
            raise ValidationError('برای رسانه لینک باید آدرس معتبر وارد شود.')
        return cleaned_data


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectUpdate
        fields = [
            'project',
            'title',
            'summary',
            'body',
            'progress_percent',
            'highlight_image',
            'video_file',
            'video_url',
            'is_public',
            'display_order',
            'published_at',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'body': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def clean_progress_percent(self):
        value = self.cleaned_data.get('progress_percent')
        if value is not None and not 0 <= value <= 100:
            raise ValidationError('درصد پیشرفت باید بین ۰ تا ۱۰۰ باشد.')
        return value


class ParticipationMethodForm(forms.ModelForm):
    class Meta:
        model = ParticipationMethod
        fields = [
            'title',
            'slug',
            'description',
            'icon',
            'action_text',
            'action_url',
            'is_active',
            'display_order',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class ImpactStatForm(forms.ModelForm):
    class Meta:
        model = ImpactStat
        fields = ['title', 'value', 'unit', 'description', 'is_active', 'display_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['project', 'amount', 'is_anonymous', 'message', 'payment_gateway']
        widgets = {
            'project': forms.HiddenInput(),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ (تومان)'}),
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'پیام اختیاری'}),
            'payment_gateway': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = CharityProject.objects.filter(is_active=True)
        self.fields['payment_gateway'].initial = PaymentGateway.MANUAL
        if user and user.is_authenticated:
            self.fields['is_anonymous'].initial = False
        else:
            self.fields['is_anonymous'].initial = True

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 1000:
            raise ValidationError('حداقل مبلغ اهدایی ۱٬۰۰۰ تومان است.')
        return amount


class DonationAdminForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = '__all__'
        widgets = {
            'created_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'updated_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_status = cleaned_data.get('payment_status')
        transaction_id = cleaned_data.get('transaction_id')

        if payment_status == PaymentStatus.PAID and not transaction_id:
            raise ValidationError('برای پرداخت موفق باید شناسه تراکنش ثبت شود.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            paid_total = Donation.objects.filter(
                project=instance.project,
                payment_status=PaymentStatus.PAID,
            ).aggregate(total=Sum('amount'))['total'] or 0
            instance.project.current_amount = paid_total
            instance.project.save(update_fields=['current_amount'])
        return instance


class DonationReceiptForm(forms.ModelForm):
    receipt_number = forms.CharField(
        label='شماره رسید',
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
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
            last_receipt = DonationReceipt.objects.order_by('-id').first()
            last_number = int(last_receipt.receipt_number.split('-')[-1]) if last_receipt else 0
            self.initial['receipt_number'] = f"REC-{timezone.now().year}-{last_number + 1:05d}"


class PaymentTransactionForm(forms.ModelForm):
    class Meta:
        model = PaymentTransaction
        fields = ['donation', 'amount', 'status', 'gateway', 'transaction_code', 'raw_response']
        widgets = {
            'raw_response': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'donation': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        transaction_code = cleaned_data.get('transaction_code')

        if status in (PaymentStatus.PAID, PaymentStatus.REFUNDED) and not transaction_code:
            raise ValidationError('برای وضعیت پرداخت‌شده یا بازپرداخت‌شده باید کد تراکنش ثبت شود.')
        return cleaned_data


class DonationFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'همه وضعیت‌ها')] + list(PaymentStatus.choices)
    GATEWAY_CHOICES = [('', 'همه درگاه‌ها')] + list(PaymentGateway.choices)

    project = forms.ModelChoiceField(
        queryset=CharityProject.objects.all(),
        required=False,
        label='پروژه',
        widget=forms.Select(attrs={'class': 'form-control'})
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
        label='درگاه',
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
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    max_amount = forms.IntegerField(
        required=False,
        label='حداکثر مبلغ (تومان)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
