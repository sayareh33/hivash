# products/views.py
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import View, generic
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from .models import Product, Comment, Wishlist, WishlistItem, Category
from .forms import CommentForm, AddToWishlistForm, RemoveFromWishlistForm, ProductSearchForm
# from articles.models import Article


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True, status='published').order_by('-datetime_created')
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('display_order')
        return context


class FoodsListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(category__slug='foods', is_active=True, status='published')

class BagsListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(category__slug='bags', is_active=True, status='published')


from django.views.generic import ListView
from django.db.models import Q
from .models import Product, Category
from .forms import ProductSearchForm

# 🟢 لیست عمومی محصولات
class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=True, status='published')
            .select_related('category')
            .prefetch_related('images')
        )

        # مرتب‌سازی
        sort = self.request.GET.get('sort')
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'cheapest':
            queryset = queryset.order_by('unit_price')
        elif sort == 'expensive':
            queryset = queryset.order_by('-unit_price')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['search_form'] = ProductSearchForm()
        context['sort'] = self.request.GET.get('sort', '')
        return context


# 🟡 نمایش محصولات یک دسته خاص
class CategoryProductListView(ProductListView):
    def get_queryset(self):
        category_slug = self.kwargs.get('slug')
        self.category = Category.objects.get(slug=category_slug)
        return (
            Product.objects.filter(category=self.category, is_active=True, status='published')
            .select_related('category')
            .prefetch_related('images')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = self.category
        return context


# 🔵 محصولات دارای تخفیف فعال
class DiscountedProductsView(ProductListView):
    template_name = 'products/discounted_products.html'

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, status='published', discount__is_active=True)
            .select_related('category')
            .prefetch_related('images')
        )


# 🔍 جستجو
class ProductSearchView(ProductListView):
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        queryset = Product.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_active=True,
            status='published'
        )
        return queryset.select_related('category').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

# ============================
# 🔹 Product Detail View
# ============================
class ProductDetailView(generic.DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # فرم نظر کاربر
        context['comment_form'] = CommentForm()

        # دریافت نظرات تأییدشده
        context['comments'] = product.comments.filter(
            status=Comment.COMMENT_STATUS_APPROVED,
            active=True
        ).select_related('author')

        # تخفیف فعال
        context['active_discount'] = product.get_best_discount()
        context['final_price'] = product.get_final_price()

        # محصولات مشابه
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:8]

        return context

from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Product, Comment
from .forms import CommentForm

class ProductDetailView(generic.DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        context['comment_form'] = CommentForm()
        context['comments'] = product.comments.filter(
            status=Comment.COMMENT_STATUS_APPROVED, active=True
        )
        context['active_discount'] = product.get_best_discount()
        context['final_price'] = product.get_final_price()
        context['related_products'] = Product.objects.filter(
            category=product.category, is_active=True
        ).exclude(id=product.id)[:8]
        return context

class ProductDetailView(generic.DetailView):
    model = Product
    template_name = 'products/product_details.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # فرم نظر
        context['comment_form'] = CommentForm()

        # نظرات تأیید شده
        context['comments'] = product.comments.filter(
            status=Comment.COMMENT_STATUS_APPROVED,
            active=True
        ).select_related('author')

        # تخفیف فعال
        context['active_discount'] = product.get_best_discount()
        context['final_price'] = product.get_final_price()

        # محصولات مشابه
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:8]

        # ✅ ذخیره در محصولات اخیراً مشاهده‌شده (Session)
        request = self.request
        viewed_products = request.session.get('recently_viewed', [])

        if product.id in viewed_products:
            viewed_products.remove(product.id)
        viewed_products.insert(0, product.id)
        request.session['recently_viewed'] = viewed_products[:8]  # فقط ۸ مورد آخر

        # ✅ بازیابی محصولات اخیراً مشاهده‌شده
        recent_ids = [pid for pid in viewed_products if pid != product.id]
        context['recently_viewed_products'] = Product.objects.filter(
            id__in=recent_ids,
            is_active=True
        )[:8]

        return context

class CommentCreateView(generic.CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            messages.error(self.request, _("برای ارسال نظر ابتدا وارد شوید."))
            return redirect("accounts:login")

        product_id = self.kwargs.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.product = product
        obj.save()

        messages.success(self.request, _("نظر شما با موفقیت ثبت شد و پس از تأیید نمایش داده می‌شود."))
        return redirect(product.get_absolute_url())

# ============================
# 🔹 Comment Create View
# ============================
class CommentCreateView(generic.CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            messages.error(self.request, _("برای ارسال نظر ابتدا وارد شوید."))
            return redirect("accounts:login")

        product_id = self.kwargs.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.product = product
        obj.save()

        messages.success(self.request, _("نظر شما با موفقیت ثبت شد و پس از تأیید نمایش داده می‌شود."))
        return redirect(product.get_absolute_url())


# ============================
# 🔹 Simple Product Search
# ============================
class ProductSearchView(ListView):
    model = Product
    template_name = 'products/product_search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        self.form = ProductSearchForm(self.request.GET or None)

        if self.form.is_valid():
            query = self.form.cleaned_data.get('query')
            category = self.form.cleaned_data.get('category')

            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(short_description__icontains=query) |
                    Q(description__icontains=query)
                )

            if category:
                queryset = queryset.filter(category=category)

        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['query'] = self.request.GET.get('query', '')
        return context


# ============================
# 🔹 Advanced Search View (MySQL Friendly)
# ============================
class AdvancedSearchView(View):
    template_name = 'products/advanced_search.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()

        if not query:
            return render(request, self.template_name, {'query': query})

        # جستجوی محصولات با icontains (سازگار با MySQL)
        product_results = Product.objects.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query),
            is_active=True
        ).distinct()[:10]

        # جستجوی مقالات با icontains
        # article_results = Article.objects.filter(
        #     Q(title__icontains=query) |
        #     Q(content__icontains=query) |
        #     Q(summary__icontains=query),
        #     status='published'
        # ).distinct()[:5]
        #
        # context = {
        #     'query': query,
        #     'product_results': product_results,
        #     'article_results': article_results,
        # }

        # return render(request, self.template_name, context)


# ============================
# 🔹 Unified Search (Products + Articles)
# ============================
class UnifiedSearchView(View):
    template_name = 'products/unified_search.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        context = {'query': query}

        if query:
            # Products
            product_results = Product.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query),
                is_active=True
            ).distinct()[:10]

            # Articles
        #     article_results = Article.objects.filter(
        #         Q(title__icontains=query) |
        #         Q(content__icontains=query) |
        #         Q(summary__icontains=query),
        #         status='published'
        #     ).distinct()[:5]
        #
        #     context.update({
        #         'product_results': product_results,
        #         'article_results': article_results,
        #         'has_results': product_results.exists() or article_results.exists()
        #     })
        #
        # return render(request, self.template_name, context)

# ============================
# 🔹 Wishlist Views
# ============================
@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = WishlistItem.objects.filter(wishlist=wishlist).select_related('product')

    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'products/wishlist.html', context)


@login_required
def add_to_wishlist(request):
    if request.method == 'POST':
        form = AddToWishlistForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            product = get_object_or_404(Product, id=product_id)
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

            exists = WishlistItem.objects.filter(wishlist=wishlist, product=product).exists()
            if not exists:
                WishlistItem.objects.create(wishlist=wishlist, product=product)
                messages.success(request, _('محصول به لیست علاقه‌مندی‌ها اضافه شد.'))
            else:
                messages.info(request, _('این محصول قبلاً در لیست علاقه‌مندی‌های شما وجود دارد.'))

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect(product.get_absolute_url())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error'})
    return redirect('home')


@login_required
def remove_from_wishlist(request):
    if request.method == 'POST':
        form = RemoveFromWishlistForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            product = get_object_or_404(Product, id=product_id)
            wishlist = get_object_or_404(Wishlist, user=request.user)

            WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
            messages.success(request, _('محصول از لیست علاقه‌مندی‌ها حذف شد.'))

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect('products:wishlist')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error'})
    return redirect('products:wishlist')
