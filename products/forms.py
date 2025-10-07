from django import forms

from .models import Comment, Category, Comment


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
