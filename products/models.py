from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

User = get_user_model()


# --------------------------
# Helper: unique slug
# --------------------------
def generate_unique_slug(model, text, max_length=50):
    """
    تولید اسلاگ منحصر به فرد برای یک مدل مشخص
    """
    base_slug = slugify(unidecode(text))[:max_length]
    slug = base_slug
    counter = 1

    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        if len(slug) > max_length:
            base_slug = base_slug[: max_length - len(str(counter)) - 1]
            slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# --------------------------
# Category
# --------------------------
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name='کاربر')
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(max_length=500, blank=True)

    # درختی (برای عملکرد بهتر می‌توان از django-mptt استفاده کرد)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    top_product = models.ForeignKey('Product', on_delete=models.SET_NULL, blank=True, null=True, related_name='+')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Category, self.title, max_length=100)
        super().save(*args, **kwargs)


# --------------------------
# Tag
# --------------------------
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=70)
    description = models.TextField(blank=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Tag, self.name, max_length=70)
        super().save(*args, **kwargs)


# --------------------------
# Discount
# --------------------------
class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'درصدی'),
        ('fixed', 'مبلغ ثابت'),
        ('buy_one_get_one', 'خرید یک به یک هدیه'),
    ]

    DISCOUNT_SCOPES = [
        ('product', 'محصول خاص'),
        ('category', 'دسته‌بندی'),
        ('all', 'همه محصولات'),
        ('festival', 'جشنواره'),
    ]

    name = models.CharField(_('نام تخفیف'), max_length=100)
    discount_type = models.CharField(_('نوع تخفیف'), max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    # مقدار به صورت Decimal برای دقت مالی
    discount_value = models.DecimalField(_('مقدار تخفیف'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    scope = models.CharField(_('حوزه تخفیف'), max_length=20, choices=DISCOUNT_SCOPES, default='product')
    description = models.TextField(_('توضیحات'), max_length=250, blank=True)
    start_date = models.DateTimeField(_('تاریخ شروع'), default=timezone.now)
    end_date = models.DateTimeField(_('تاریخ پایان'), null=True, blank=True)
    is_active = models.BooleanField(_('فعال'), default=True)
    max_usage = models.IntegerField(_('حداکثر استفاده'), default=0)
    usage_count = models.IntegerField(_('تعداد استفاده'), default=0)
    min_order_amount = models.DecimalField(_('حداقل مبلغ سفارش'), max_digits=12, decimal_places=2, default=Decimal('0.00'))

    categories = models.ManyToManyField('Category', blank=True, related_name='category_discounts')
    products = models.ManyToManyField('Product', blank=True, related_name='product_discounts')
    festival_name = models.CharField(_('نام جشنواره'), max_length=100, blank=True)
    priority = models.IntegerField(_('اولویت'), default=1)

    class Meta:
        verbose_name = _('تخفیف')
        verbose_name_plural = _('تخفیف‌ها')
        ordering = ['-priority', '-start_date']

    def __str__(self):
        return f'{self.name} - {self.get_discount_type_display()}'

    def is_active_now(self):
        """بررسی فعال بودن تخفیف در زمان حال (شامل فیلد is_active)."""
        now = timezone.now()
        return (self.is_active and
                self.start_date <= now and
                (self.end_date is None or now <= self.end_date) and
                (self.max_usage == 0 or self.usage_count < self.max_usage))

    def calculate_discount_amount(self, product_price: Decimal, quantity: int = 1) -> Decimal:
        """محاسبه مقدار تخفیف بر اساس نوع. خروجی Decimal است."""
        product_price = Decimal(product_price)
        if self.discount_type == 'percentage':
            return (product_price * (self.discount_value / Decimal('100'))) * quantity
        elif self.discount_type == 'fixed':
            # مبلغ ثابت به ازای هر واحد
            return (self.discount_value) * quantity
        elif self.discount_type == 'buy_one_get_one':
            free_items = quantity // 2
            return product_price * free_items
        return Decimal('0.00')

    def can_apply_to_product(self, product):
        """بررسی امکان اعمال تخفیف روی محصول"""
        if not self.is_active_now():
            return False

        if self.scope == 'all':
            return True
        elif self.scope == 'category':
            return self.categories.filter(id=product.category.id).exists()
        elif self.scope == 'product':
            return self.products.filter(id=product.id).exists()
        elif self.scope == 'festival':
            return True

        return False

    def increment_usage(self):
        """افزایش شمارنده مصرف به صورت ایمن (اتمی) برای جلوگیری از race condition"""
        with transaction.atomic():
            # قفل سطر و افزایش ایمن
            Discount.objects.filter(id=self.id).update(usage_count=F('usage_count') + 1)
            # اگر نیاز داری مقدار usage_count داخل شی به‌روز شود:
            self.refresh_from_db(fields=['usage_count'])


# --------------------------
# Product
# --------------------------
class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
        ('out_of_stock', 'ناموجود'),
        ('archived', 'آرشیو شده'),
    ]

    title = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(_('Description'), max_length=1000)
    short_description = models.TextField(_('Short Description'), max_length=300, blank=True)

    # استفاده از DecimalField برای قیمت
    unit_price = models.DecimalField(_('Price'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='published')
    is_active = models.BooleanField(_('active'), default=True)
    inventory = models.IntegerField(_('Inventory'), validators=[MinValueValidator(0)], default=0)

    image = models.ImageField(_('Product Image'), upload_to='product/product_cover/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name='کاربر')
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name='created_products', verbose_name="ایجاد کننده")
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name='updated_products', verbose_name="آخرین ویرایش کننده")

    discounts = models.ManyToManyField('Discount', blank=True, related_name='discount_products')

    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True)
    material = models.CharField(max_length=100, blank=True)
    expiration_date = models.DateField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')

    # برای جستجوی ساده از یک فیلد متنی استفاده شده؛ در production بهتر است از SearchVectorField یا یک موتور جستجو استفاده کنید
    search_vector = models.CharField(max_length=500, blank=True, editable=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['unit_price']),
            models.Index(fields=['is_featured']),
        ]
        ordering = ['-datetime_created']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Product, self.title, max_length=100)

        search_content = f"{self.title} {self.short_description}"
        self.search_vector = search_content[:500]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    def get_active_discounts(self):
        """بازگشت تخفیف‌های مرتبط که الان فعال هستند"""
        now = timezone.now()
        return self.discounts.filter(
            start_date__lte=now,
            is_active=True
        ).filter(Q(end_date__gte=now) | Q(end_date__isnull=True))

    def get_festival_discounts(self):
        return Discount.objects.filter(
            scope='festival',
            is_active=True,
            start_date__lte=timezone.now(),
        ).filter(Q(end_date__gte=timezone.now()) | Q(end_date__isnull=True))

    def get_best_discount(self, quantity=1):
        """بهترین مقدار تخفیف از بین تخفیف‌های فعال برای تعداد مشخص"""
        active_discounts = list(self.get_active_discounts())
        festival_discounts = list(self.get_festival_discounts())

        all_discounts = active_discounts + festival_discounts
        if not all_discounts:
            return None

        # مقایسه بر اساس مقدار تخفیف برای quantity مورد نظر
        return max(all_discounts, key=lambda d: d.calculate_discount_amount(self.unit_price, quantity))

    def get_final_price(self, quantity=1):
        discount = self.get_best_discount(quantity)
        if discount:
            discount_amount = discount.calculate_discount_amount(self.unit_price, quantity)
            final = Decimal(self.unit_price) - discount_amount
            return max(Decimal('0.00'), final)
        return self.unit_price

    def has_active_discount(self):
        return self.get_active_discounts().exists() or self.get_festival_discounts().exists()

    def is_in_festival(self):
        return self.get_festival_discounts().exists()

    # متد قدیمی برای سازگاری
    def get_discounted_price(self):
        active_discounts = self.discounts.filter(
            Q(start_date__lte=timezone.now()) &
            (Q(end_date__isnull=True) | Q(end_date__gte=timezone.now()))
        )

        if active_discounts.exists():
            discount = active_discounts.first().discount_value
            return int(self.unit_price * (1 - discount / Decimal('100')))
        return self.unit_price

    @classmethod
    def search(cls, query):
        return cls.objects.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(search_vector__icontains=query)
        )



# models.py
class Feature(models.Model):
    product = models.ForeignKey('Product', related_name='features', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.name}: {self.value}"

# --------------------------
# Media for product
# --------------------------
class Images(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='images')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    main = models.BooleanField(_('main image'), default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    date_uploaded = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.title} - Image {self.id}"


class Videos(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='videos')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.FileField(upload_to='product_videos/')
    main = models.BooleanField(_('main video'), default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)
    date_uploaded = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.title} - Video {self.id}"


# --------------------------
# Comment
# --------------------------
class CommentManager(models.Manager):
    def get_approved(self):
        return self.get_queryset().filter(status=Comment.COMMENT_STATUS_APPROVED)


class ApprovedCommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Comment.COMMENT_STATUS_APPROVED)


class ActiveCommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class Comment(models.Model):
    COMMENT_STATUS_WAITING = 'w'
    COMMENT_STATUS_APPROVED = 'a'
    COMMENT_STATUS_NOT_APPROVED = 'na'
    COMMENT_STATUS = [
        (COMMENT_STATUS_WAITING, 'Waiting'),
        (COMMENT_STATUS_APPROVED, 'Approved'),
        (COMMENT_STATUS_NOT_APPROVED, 'Not Approved'),
    ]

    PRODUCT_STARS = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments',
                               verbose_name='Comment author', null=True, blank=True)
    name = models.CharField(max_length=255)
    body = models.TextField(max_length=500, verbose_name=_('متن نظر:'))
    status = models.CharField(max_length=2, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING,
                              verbose_name='status')

    stars = models.PositiveSmallIntegerField(choices=PRODUCT_STARS, verbose_name=_('به این محصول چند ستاره می دهید؟:'), default=5)
    video = models.ForeignKey(Videos, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    objects = CommentManager()
    approved = ApprovedCommentManager()
    active_comments = ActiveCommentManager()

    def __str__(self):
        return f"Comment by {self.name} on {self.product.title}"

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.product.id])


# --------------------------
# Customer & Address
# --------------------------
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    phone_number = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        permissions = [
            ('send_private_email', 'Can send private email'),
        ]


class Address(models.Model):
    # اجازه چند آدرس برای هر مشتری
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    province = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.province}"


# --------------------------
# Cart & CartItem
# --------------------------
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id}"

    def get_total_price(self):
        total = Decimal('0.00')
        for item in self.items.select_related('product'):
            total += (item.product.get_final_price(item.quantity) * item.quantity)
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], default=1)

    class Meta:
        unique_together = [['cart', 'product']]

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


# --------------------------
# Wishlist
# --------------------------
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='WishlistItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f"{self.product.title} in {self.wishlist.user.username}'s wishlist"


# --------------------------
# Basic Order skeleton (recommended)
# --------------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('paid', 'پرداخت شده'),
        ('shipped', 'ارسال شده'),
        ('cancelled', 'لغو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.title} in {self.order.id}"
