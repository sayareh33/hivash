"""Session-based cart utilities with shipping support."""

from decimal import Decimal

from django.contrib import messages
from django.utils.translation import gettext as _

from products.models import Product
from .models import ShippingMethod


class Cart:
    """Simple cart stored in the session."""

    SHIPPING_SESSION_KEY = "shipping_method_id"

    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.cart = self.session.get("cart")

        if self.cart is None:
            self.cart = self.session["cart"] = {}

        self.shipping_method_id = self.session.get(self.SHIPPING_SESSION_KEY)
        self._shipping_method = None
        self._ensure_shipping_method()

    # ------------------------------------------------------------------#
    # Session helpers
    # ------------------------------------------------------------------#
    def save(self):
        self.session.modified = True

    def _ensure_shipping_method(self):
        """Guarantee that a valid shipping method is stored in the session."""
        method = None

        if self.shipping_method_id:
            try:
                method = ShippingMethod.objects.get(id=self.shipping_method_id, is_active=True)
            except ShippingMethod.DoesNotExist:
                method = None

        if method is None:
            method = (
                ShippingMethod.objects.filter(is_active=True, is_default=True).first()
                or ShippingMethod.objects.filter(is_active=True).order_by("base_cost").first()
            )

        stored_id = self.session.get(self.SHIPPING_SESSION_KEY)
        if method:
            self._shipping_method = method
            if stored_id != method.id:
                self.session[self.SHIPPING_SESSION_KEY] = method.id
                self.save()
        else:
            self._shipping_method = None
            if stored_id:
                self.session.pop(self.SHIPPING_SESSION_KEY, None)
                self.save()

    def set_shipping_method(self, method_id: int) -> bool:
        """Persist chosen shipping method."""
        try:
            method = ShippingMethod.objects.get(id=method_id, is_active=True)
        except ShippingMethod.DoesNotExist:
            return False

        self.session[self.SHIPPING_SESSION_KEY] = method.id
        self._shipping_method = method
        self.save()
        return True

    def get_shipping_method(self):
        if self._shipping_method is None and self.shipping_method_id:
            try:
                self._shipping_method = ShippingMethod.objects.get(
                    id=self.shipping_method_id, is_active=True
                )
            except ShippingMethod.DoesNotExist:
                self._shipping_method = None
        return self._shipping_method

    # ------------------------------------------------------------------#
    # Cart mutation
    # ------------------------------------------------------------------#
    def add(self, product, quantity=1, replace_current_quantity=False):
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0}

        if replace_current_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity

        messages.success(self.request, _("محصول به سبد خرید اضافه شد."))
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            messages.success(self.request, _("محصول از سبد خرید حذف شد."))
            self.save()

    def clear(self):
        self.session.pop("cart", None)
        self.session.pop(self.SHIPPING_SESSION_KEY, None)
        self.cart = {}
        self._shipping_method = None
        self.save()

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    # ------------------------------------------------------------------#
    # Iteration helpers
    # ------------------------------------------------------------------#
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart_snapshot = self.cart.copy()

        for product in products:
            cart_item = cart_snapshot[str(product.id)]
            cart_item["product_obj"] = {
                "id": product.id,
                "title": product.title,
                "unit_price": float(product.unit_price),
                "slug": product.slug,
                "image_url": product.primary_image_url,
            }
            cart_item["product_id"] = product.id
            cart_item["product_title"] = product.title
            cart_item["product_unit_price"] = float(product.unit_price)
            cart_item["product_slug"] = product.slug
            cart_item["product_image_url"] = product.primary_image_url
            cart_item["total_price"] = float(cart_item["quantity"] * product.unit_price)

        for item in cart_snapshot.values():
            yield item

    # ------------------------------------------------------------------#
    # Pricing helpers
    # ------------------------------------------------------------------#
    def is_empty(self):
        return len(self.cart) == 0

    def get_subtotal(self):
        return sum(
            item["quantity"] * float(item.get("product_obj", {}).get("unit_price", 0))
            for item in self.cart.values()
        )

    def get_discount(self):
        # Placeholder for future coupon integration.
        return 0

    def get_total_price(self):
        return self.get_subtotal()

    def get_total_price_after_discount(self):
        subtotal = self.get_subtotal() - self.get_discount()
        return subtotal if subtotal > 0 else 0

    def get_shipping_cost(self):
        if self.is_empty():
            return 0

        method = self.get_shipping_method()
        if not method:
            return 0

        if method.minimum_order_total and self.get_subtotal() < float(method.minimum_order_total):
            return 0

        return float(method.base_cost)

    def get_grand_total(self):
        return self.get_total_price_after_discount() + self.get_shipping_cost()
