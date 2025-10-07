from django import forms
from .models import Article, Comment, ArticleImage

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'slug', 'excerpt', 'body', 'category', 'tags', 'status', 'publish_date']
        widgets = {
            'body': forms.Textarea(attrs={'rows':10}),
            'excerpt': forms.Textarea(attrs={'rows':3}),
            'publish_date': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body', 'type', 'parent']
        widgets = {
            'body': forms.Textarea(attrs={'rows':4}),
            'parent': forms.HiddenInput(),
        }

class ArticleImageForm(forms.ModelForm):
    class Meta:
        model = ArticleImage
        fields = ['image', 'caption', 'order']