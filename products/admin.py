from decimal import Decimal
from django.contrib import admin, messages
from django.db.models import Count, Sum, F
from django.utils import timezone


from .forms import ProductAdminForm, DiscountAdminForm
from .models import (
    Category, Tag, Discount, Product, Feature, Images, Videos,
    Comment, Customer, Address, Cart, CartItem, Wishlist, WishlistItem,
    Order, OrderItem
)

# ---------- اینلاین‌ها ----------
class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1
    min_num = 0


class ProductImageInline(admin.TabularInline):
    model = Images
    extra = 1
    verbose_name = "تصویر"
    verbose_name_plural = "تصاویر"


class ProductVideoInline(admin.TabularInline):
    model = Videos
    extra = 0
    verbose_name = "ویدئو"
    verbose_name_plural = "ویدئوها"


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "body", "status", "stars", "active", "datetime_created")
    readonly_fields = ("datetime_created",)
    show_change_link = True


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    autocomplete_fields = ("product",)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("product",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("price",)

# ---------- مدل‌های اصلی ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "is_active", "display_order")
    list_filter = ("is_active", "parent")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "title")
    autocomplete_fields = ("parent", "top_product")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    form = DiscountAdminForm
    list_display = ("name", "discount_type", "scope", "is_active_now", "usage_count", "start_date", "end_date")
    list_filter = ("discount_type", "scope", "is_active")
    search_fields = ("name", "festival_name")
    filter_horizontal = ("categories", "products")
    readonly_fields = ("usage_count",)
    fieldsets = (
        ("مشخصات تخفیف", {"fields": ("name", "discount_type", "discount_value", "scope", "priority")}),
        ("دامنه اعمال", {"fields": ("categories", "products", "festival_name")}),
        ("قوانین استفاده", {"fields": ("is_active", "start_date", "end_date", "max_usage", "usage_count", "min_order_amount")}),
        ("توضیحات", {"fields": ("description",)}),
    )

    def is_active_now(self, obj):
        return obj.is_active_now()
    is_active_now.boolean = True
    is_active_now.short_description = "فعال؟"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("title", "category", "status", "is_active", "inventory", "unit_price", "has_active_discount")
    list_filter = ("status", "is_active", "category", "is_featured", "discounts")
    search_fields = ("title", "slug", "short_description", "search_vector")
    autocomplete_fields = ("category", "created_by", "updated_by", "tags", "discounts")
    inlines = [FeatureInline, ProductImageInline, ProductVideoInline, CommentInline]
    readonly_fields = ("datetime_created", "datetime_modified", "search_vector")
    prepopulated_fields = {"slug": ("title",)}
    actions = ("mark_as_published", "mark_as_out_of_stock")

    def mark_as_published(self, request, queryset):
        updated = queryset.update(status="published", is_active=True)
        self.message_user(request, f"{updated} محصول منتشر شد.", messages.SUCCESS)
    mark_as_published.short_description = "انتشار محصولات انتخاب شده"

    def mark_as_out_of_stock(self, request, queryset):
        updated = queryset.update(status="out_of_stock")
        self.message_user(request, f"{updated} محصول ناموجود شد.", messages.WARNING)
    mark_as_out_of_stock.short_description = "ناموجود کردن محصولات"



@admin.register(Videos)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "main", "date_uploaded")
    list_filter = ("main", "date_uploaded")
    search_fields = ("product__title", "user__phone")
    autocomplete_fields = ("product", "user")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "status", "stars", "active", "datetime_created")
    list_filter = ("status", "active", "stars", "datetime_created")
    search_fields = ("name", "body", "product__title")
    autocomplete_fields = ("product", "parent", "author", "video")
    actions = ("approve_comments", "reject_comments")
    readonly_fields = ("datetime_created", "datetime_modified")

    def approve_comments(self, request, queryset):
        updated = queryset.update(status=Comment.COMMENT_STATUS_APPROVED)
        self.message_user(request, f"{updated} نظر تایید شد.", messages.SUCCESS)
    approve_comments.short_description = "تایید نظرات انتخابی"

    def reject_comments(self, request, queryset):
        updated = queryset.update(status=Comment.COMMENT_STATUS_NOT_APPROVED)
        self.message_user(request, f"{updated} نظر رد شد.", messages.WARNING)
    reject_comments.short_description = "رد نظرات انتخابی"



@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "birth_date", "get_order_count")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone_number")
    list_filter = ("birth_date",)
    readonly_fields = ("get_order_count",)

    def get_order_count(self, obj):
        return obj.orders.count()
    get_order_count.short_description = "تعداد سفارش‌ها"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("customer", "province", "city", "street", "is_default")
    list_filter = ("province", "is_default")
    search_fields = ("city", "street", "postal_code")
    autocomplete_fields = ("customer",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "items_count", "total_price")
    search_fields = ("id", "user__username")
    readonly_fields = ("created_at", "total_price")
    inlines = [CartItemInline]  # اگر نمی‌خواهی داخل Cart هم نمایش بده؛ می‌توان حذف کرد

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _items_count=Count("items"), _total_price=Sum(F("items__product__unit_price") * F("items__quantity"))
        )

    def items_count(self, obj):
        return getattr(obj, "_items_count", 0)
    items_count.short_description = "تعداد اقلام"

    def total_price(self, obj):
        return getattr(obj, "_total_price", Decimal("0.00"))
    total_price.short_description = "مبلغ تخمینی"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")
    search_fields = ("cart__id", "product__title")
    autocomplete_fields = ("cart", "product")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at", "products_count")
    search_fields = ("user__username", "user__email")
    inlines = [WishlistItemInline]

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = "تعداد محصولات"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total_amount", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "customer__user__username", "customer__user__email")
    autocomplete_fields = ("customer", "address")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at", "updated_at")

    actions = ("mark_as_paid", "mark_as_shipped")

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status="paid", updated_at=timezone.now())
        self.message_user(request, f"{updated} سفارش پرداخت شده علامت خورد.", messages.SUCCESS)
    mark_as_paid.short_description = "علامت‌گذاری به‌عنوان پرداخت‌شده"

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status="shipped", updated_at=timezone.now())
        self.message_user(request, f"{updated} سفارش ارسال‌شده شد.", messages.SUCCESS)
    mark_as_shipped.short_description = "ارسال سفارش"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "price", "quantity")
    search_fields = ("order__id", "product__title")
    autocomplete_fields = ("order", "product")
    readonly_fields = ("price",)








