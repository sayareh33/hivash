from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Q
from django.utils import timezone
from .models import Article, Category, Tag
from .forms import Article, Comment, CommentForm

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    paginate_by = 10

    def get_queryset(self):
        qs = Article.objects.filter(status='published')
        # فقط مقالاتی که تاریخ انتشار مشخص و در گذشته یا الان هستند
        qs = qs.filter(Q(publish_date__lte=timezone.now()) | Q(publish_date__isnull=True))
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        tag = self.request.GET.get('tag')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q))
        if category:
            qs = qs.filter(category__slug=category)
        if tag:
            qs = qs.filter(tags__slug=tag)
        return qs.select_related('category', 'author').prefetch_related('tags', 'images')


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Article.objects.filter(status='published').select_related('category', 'author').prefetch_related('images', 'tags', 'comments')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        # نمایش فقط نظرات عمومی
        ctx['comments'] = self.object.comments.filter(is_public=True, parent__isnull=True)
        return ctx


class SubmitCommentView(CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        article = get_object_or_404(Article, slug=self.kwargs.get('slug'), status='published')
        comment = form.save(commit=False)
        comment.article = article
        # به طور پیش‌فرض نیاز به تایید دارد
        comment.is_public = False
        comment.save()
        return redirect(article.get_absolute_url())
