# products/views.py
from django.db.models import Prefetch, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import View, generic
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from .models import Product, Comment, Wishlist, WishlistItem, Category
from .forms import CommentForm, AddToWishlistForm, RemoveFromWishlistForm, ProductSearchForm


def _get_safe_redirect(request, fallback):
    """
    Return a safe URL to redirect the user back to after wishlist actions.
    Prefer explicit 'next' parameter, then Referer header, otherwise fallback.
    """
    next_url = request.POST.get('next') or request.GET.get('next')
    allowed_hosts = {request.get_host()}

    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=allowed_hosts):
        return next_url

    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts=allowed_hosts):
        return referer

    return fallback
# from articles.models import Article


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    @staticmethod
    def _get_category_family_ids(root_category):
        """Return the ids of the category together with all active descendants."""
        ids = [root_category.id]
        child_ids = list(
            Category.objects.filter(parent=root_category, is_active=True).values_list('id', flat=True)
        )
        while child_ids:
            ids.extend(child_ids)
            child_ids = list(
                Category.objects.filter(parent__in=child_ids, is_active=True).values_list('id', flat=True)
            )
        return ids

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=True, status='published')
            .select_related('category')
            .prefetch_related('images')
        )

        self.selected_category = None
        category_slug = self.request.GET.get('category')
        if category_slug:
            self.selected_category = get_object_or_404(
                Category, slug=category_slug, is_active=True
            )
            category_ids = self._get_category_family_ids(self.selected_category)
            queryset = queryset.filter(category_id__in=category_ids)

        sort = self.request.GET.get('sort')
        if sort == 'cheapest':
            queryset = queryset.order_by('unit_price')
        elif sort == 'expensive':
            queryset = queryset.order_by('-unit_price')
        else:
            queryset = queryset.order_by('-datetime_created')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        showcase_prefetch = Prefetch(
            'products',
            queryset=Product.objects.filter(
                is_active=True,
                status='published'
            )
            .select_related('category')
            .prefetch_related('images')
            .order_by('-datetime_created')[:4],
            to_attr='showcase_products'
        )

        categories_qs = (
            Category.objects.filter(
                is_active=True,
                products__is_active=True,
                products__status='published'
            )
            .prefetch_related(showcase_prefetch)
            .order_by('display_order', 'title')
            .distinct()
        )

        selected_category = getattr(self, 'selected_category', None)

        context['categories'] = [
            category for category in categories_qs
            if getattr(category, 'showcase_products', [])
            and (selected_category is None or category.pk != selected_category.pk)
        ]
        context['search_form'] = ProductSearchForm()
        context['sort'] = self.request.GET.get('sort', '')
        context['selected_category'] = selected_category
        context['selected_category_products'] = (
            self.object_list if selected_category else Product.objects.none()
        )
        context['selected_category_slug'] = (
            selected_category.slug if selected_category else ''
        )

        if self.request.user.is_authenticated:
            wishlist_ids = WishlistItem.objects.filter(
                wishlist__user=self.request.user
            ).values_list('product_id', flat=True)
            context['wishlist_product_ids'] = list(wishlist_ids)
        else:
            context['wishlist_product_ids'] = []

        return context

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

        if self.request.user.is_authenticated:
            context['is_in_wishlist'] = WishlistItem.objects.filter(
                wishlist__user=self.request.user,
                product=product
            ).exists()
        else:
            context['is_in_wishlist'] = False

        return context


class BagsListView(generic.ListView):
    model = Product
    template_name = 'products/bag_list.html'
    context_object_name = 'bags'
    paginate_by = 6

    def get_queryset(self):
        main_category = get_object_or_404(Category, slug='bags')
        # همه محصولات این دسته و زیردسته‌هایش
        sub_categories = Category.objects.filter(parent=main_category)
        category_ids = ProductListView._get_category_family_ids(main_category)
        return Product.objects.filter(
            category_id__in=category_ids,
            is_active=True,
            status='published'
        )

class FoodsListView(generic.ListView):
    model = Product
    template_name = 'products/food_list.html'
    context_object_name = 'foods'
    paginate_by = 6

    def get_queryset(self):
        main_category = get_object_or_404(Category, slug='foods')
        # همه محصولات این دسته و زیردسته‌هایش
        sub_categories = Category.objects.filter(parent=main_category)
        category_ids = ProductListView._get_category_family_ids(main_category)
        return Product.objects.filter(
            category_id__in=category_ids,
            is_active=True,
            status='published'
        )



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
    wishlist_items_qs = (
        WishlistItem.objects.filter(wishlist=wishlist)
        .select_related('product')
        .order_by('-added_at')
    )

    paginator = Paginator(wishlist_items_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'wishlist': wishlist,
        'wishlist_items': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'total_items': paginator.count,
    }
    return render(request, 'products/wishlist.html', context)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def add_to_wishlist_ajax(request):
    """ویو AJAX برای افزودن - نسخه اصلاح شده"""
    # بررسی لاگین بودن کاربر
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'لطفاً ابتدا وارد حساب کاربری خود شوید',
            'login_required': True
        }, status=401)

    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({
            'status': 'error',
            'message': 'شناسه محصول الزامی است'
        }, status=400)

    try:
        product = Product.objects.get(id=product_id, is_active=True, status='published')
    except Product.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'محصول یافت نشد'
        }, status=404)

    try:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )

        if created:
            return JsonResponse({
                'status': 'success',
                'action': 'added',
                'message': 'محصول به علاقه‌مندی‌ها اضافه شد',
                'in_wishlist': True,
                'wishlist_count': wishlist.wishlistitem_set.count()
            })
        else:
            return JsonResponse({
                'status': 'info',
                'action': 'already_exists',
                'message': 'این محصول قبلاً در علاقه‌مندی‌ها بود',
                'in_wishlist': True,
                'wishlist_count': wishlist.wishlistitem_set.count()
            })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'خطای سرور: {str(e)}'
        }, status=500)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def remove_from_wishlist_ajax(request):
    """ویو AJAX برای حذف - نسخه اصلاح شده"""
    # بررسی لاگین بودن کاربر
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'لطفاً ابتدا وارد حساب کاربری خود شوید',
            'login_required': True
        }, status=401)

    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({
            'status': 'error',
            'message': 'شناسه محصول الزامی است'
        }, status=400)

    try:
        wishlist = Wishlist.objects.get(user=request.user)
        deleted_count = WishlistItem.objects.filter(
            wishlist=wishlist,
            product_id=product_id
        ).delete()[0]

        if deleted_count > 0:
            return JsonResponse({
                'status': 'success',
                'action': 'removed',
                'message': 'محصول از علاقه‌مندی‌ها حذف شد',
                'in_wishlist': False,
                'wishlist_count': wishlist.wishlistitem_set.count()
            })
        else:
            return JsonResponse({
                'status': 'info',
                'action': 'not_found',
                'message': 'محصول در علاقه‌مندی‌ها یافت نشد',
                'in_wishlist': False,
                'wishlist_count': wishlist.wishlistitem_set.count()
            })

    except Wishlist.DoesNotExist:
        return JsonResponse({
            'status': 'info',
            'action': 'not_found',
            'message': 'لیست علاقه‌مندی‌ها یافت نشد',
            'in_wishlist': False,
            'wishlist_count': 0
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'خطای سرور: {str(e)}'
        }, status=500)


# @require_http_methods(["POST"])
# @login_required
# def add_to_wishlist(request):
#     # اگر کاربر لاگین نباشد، به صفحه لاگین هدایت می‌شود
#     if not request.user.is_authenticated:
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'لطفاً ابتدا وارد شوید',
#                 'login_required': True,
#                 'login_url': '/accounts/login/'
#             }, status=401)
#         return redirect('accounts:login')
#
#     if request.method == 'POST':
#         form = AddToWishlistForm(request.POST)
#         if form.is_valid():
#             product_id = form.cleaned_data['product_id']
#             product = get_object_or_404(Product, id=product_id)
#             wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
#
#             exists = WishlistItem.objects.filter(wishlist=wishlist, product=product).exists()
#             if not exists:
#                 WishlistItem.objects.create(wishlist=wishlist, product=product)
#                 messages.success(request, _('محصول به لیست علاقه‌مندی‌ها اضافه شد.'))
#
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({'status': 'success', 'action': 'added'})
#             else:
#                 messages.info(request, _('این محصول قبلاً در لیست علاقه‌مندی‌های شما وجود دارد.'))
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({'status': 'info', 'action': 'already_exists'})
#
#             return redirect(_get_safe_redirect(request, product.get_absolute_url()))
#
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         return JsonResponse({'status': 'error'}, status=400)
#     return redirect('home')
#
#
# @login_required
# def remove_from_wishlist(request):
#     if request.method == 'POST':
#         form = RemoveFromWishlistForm(request.POST)
#         if form.is_valid():
#             product_id = form.cleaned_data['product_id']
#             product = get_object_or_404(Product, id=product_id)
#             wishlist = get_object_or_404(Wishlist, user=request.user)
#
#             deleted_count = WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()[0]
#             if deleted_count > 0:
#                 messages.success(request, _('محصول از لیست علاقه‌مندی‌ها حذف شد.'))
#
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({'status': 'success', 'action': 'removed'})
#             else:
#                 messages.info(request, _('این محصول در لیست علاقه‌مندی‌های شما وجود ندارد.'))
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({'status': 'info', 'action': 'not_found'})
#
#             return redirect(_get_safe_redirect(request, 'products:wishlist'))
#
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         return JsonResponse({'status': 'error'}, status=400)
#     return redirect('products:wishlist')
#
#
# from django.views.decorators.http import require_http_methods
# from django.views.decorators.csrf import ensure_csrf_cookie

