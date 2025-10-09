from django import forms
from marshmallow.fields import Decimal

from .models import Category, Comment, Product, Discount


# __________________________________________________
class ProductSearchForm(forms.Form):
    query = forms.CharField(
        label='جستجو',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'جستجوی محصول...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='همه دسته‌بندی‌ها',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']  # فیلدی که کاربر باید پر کند، مثلا متن نظر

        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'نظر خود را وارد کنید...'
            }),
        }

        labels = {
            'body': '',
        }

class AddToWishlistForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput)

class RemoveFromWishlistForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput)


# ____________________________________________
# admin forms
#___________________________________________

class DiscountAdminForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        d_type, value = cleaned.get("discount_type"), cleaned.get("discount_value")

        if end and start and end <= start:
            raise forms.ValidationError("تاریخ پایان باید بعد از تاریخ شروع باشد.")

        if d_type == "percentage" and value and value > Decimal("100"):
            raise forms.ValidationError("مقدار تخفیف درصدی نباید بیشتر از ۱۰۰ باشد.")

        return cleaned


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean_inventory(self):
        inventory = self.cleaned_data["inventory"]
        if inventory < 0:
            raise forms.ValidationError("موجودی نمی‌تواند منفی باشد.")
        return inventory


