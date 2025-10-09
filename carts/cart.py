#carts/cart.py
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Sum, F, Case, When, IntegerField
from orders.models import Order, OrderItem
from products.models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart
        """
        self.request = request
        # سیشن و حافظه مخصوص کاربر مشخص
        self.session = request.session
        # آیا از قبل مقدار کارتی وجود داره یا نه؟
        cart = self.session.get('cart')
        # ساخت سبد خرید در اولین ورود کاربر به سایت حتی بدون ثبت نام سشن مثل یه دیکشنری هست
        if not cart:
            cart = self.session['cart'] = {}
            # cart = self.session['cart]

        self.cart = cart
    # session = {
    #     'cart': {},
    #     'a': 12,
    #     'b': 133,
    #     'c': 'hadi',
    # }

    def add(self, product, quantity=1, replace_current_quantity=False):
        """
        Add the specified product to the cart if it exists
        """
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0}

        if replace_current_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        messages.success(self.request, _('Product Successfully Added to Cart!'))
        self.save()

    def remove(self, product):
        """
        Remove a product from the cart if it exists
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            messages.success(self.request, _('Product Successfully Deleted from Your Cart!'))
            self.save()

    def save(self):
        """
        Mark session as modified to save changes
        """
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart_item = cart[str(product.id)]
            cart_item['product_obj'] = {
                'id': product.id,
                'title': product.title,
                'unit_price': float(product.unit_price),
                'slug': product.slug,
                'image_url': product.primary_image_url,
            }
            cart_item['product_id'] = product.id
            cart_item['product_title'] = product.title
            cart_item['product_unit_price'] = float(product.unit_price)
            cart_item['product_slug'] = product.slug
            cart_item['product_image_url'] = product.primary_image_url
            cart_item['total_price'] = cart_item['quantity'] * product.unit_price

        for item in cart.values():
            yield item
    # def __iter__(self):
    #     product_ids = self.cart.keys()
    #     products = Product.objects.filter(id__in=product_ids)
    #     cart = self.cart.copy()  # ایجاد یک کپی از سبد خرید برای جلوگیری از تغییر مستقیم session
    #
    #     for product in products:
    #         cart_item = cart[str(product.id)]
    #         cart_item['product_obj'] = {  # ذخیره اطلاعات ضروری به جای کل آبجکت
    #             'id': product.id,
    #             'name': product.title,
    #             'unit_price': float(product.unit_price),  # تبدیل به float برای اطمینان از سریال‌شدن
    #             # سایر فیلدهای مورد نیاز...
    #         }
    #         cart_item['total_price'] = cart_item['quantity'] * product.unit_price
    #
    #     for item in cart.values():
    #         yield item

    def __len__(self):
        # return len(self.cart.keys())
        return sum(item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session['cart']
        self.save()

    def get_total_price(self):
        return sum(
            item['quantity'] * item['product_obj']['unit_price']
            for item in self.cart.values()
        )

    def is_empty(self):
        if self.cart:
            return False
        return True


# به جای کوئری سطح ماژول، یک متد برای محاسبه هنگام نیاز ایجاد کنید
# class CartPaid:
#     def __init__(self, request):
#         self.session = request.session
#         # ...
#
#     def get_total_spent(self):
#         """محاسبه مجموع هزینه‌ها فقط هنگام نیاز"""
#         from django.db.models import Sum, F
#         from orders.models import OrderItem, Order
#
#         try:
#             # روش بهینه‌تر برای محاسبه مجموع
#             total_spent = OrderItem.objects.filter(
#                 order__status=Order.ORDER_STATUS_PAID
#             ).aggregate(
#                 total=Sum(F('price') * F('quantity'))
#             )['total'] or 0
#             return total_spent
#         except:
#             # اگر جدول وجود ندارد، مقدار پیش‌فرض برگردانید
#             return 0


