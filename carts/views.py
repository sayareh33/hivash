from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.formats import number_format
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from products.models import Product

from .cart import Cart
from .forms import AddToCartProductForm
from .models import ShippingMethod


# ---------------------------------------------------------------------------#
# Helpers
# ---------------------------------------------------------------------------#
def _decimalize(value) -> Decimal:
    return Decimal(str(value)) if value is not None else Decimal("0")


def format_currency(value) -> str:
    amount = _decimalize(value).quantize(Decimal("1"))
    return f"{number_format(amount, decimal_pos=0, use_l10n=True, force_grouping=True)} تومان"


def cart_totals_payload(cart: Cart) -> dict:
    subtotal = cart.get_subtotal()
    discount = cart.get_discount()
    total_after_discount = cart.get_total_price_after_discount()
    shipping_cost = cart.get_shipping_cost()
    grand_total = cart.get_grand_total()

    return {
        "total_items": len(cart),
        "subtotal": subtotal,
        "formatted_subtotal": format_currency(subtotal),
        "discount": discount,
        "formatted_discount": format_currency(discount) if discount else format_currency(0),
        "total_after_discount": total_after_discount,
        "formatted_total_after_discount": format_currency(total_after_discount),
        "shipping_cost": shipping_cost,
        "formatted_shipping_cost": format_currency(shipping_cost),
        "grand_total": grand_total,
        "formatted_grand_total": format_currency(grand_total),
    }


def cart_item_payload(item: dict) -> dict:
    total_price = item.get("total_price", 0)
    return {
        "product_id": item.get("product_id"),
        "quantity": item.get("quantity", 0),
        "unit_price": item.get("product_unit_price", 0),
        "total_price": total_price,
        "formatted_total_price": format_currency(total_price),
    }


def json_success(message: str, cart: Cart, extra: dict | None = None) -> JsonResponse:
    payload = {"success": True, "message": message, "totals": cart_totals_payload(cart)}
    if extra:
        payload.update(extra)
    return JsonResponse(payload)


def json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"success": False, "message": message}, status=status)


def _find_item(cart: Cart, product_id: int | str) -> dict | None:
    product_id = int(product_id)
    for item in cart:
        if item.get("product_id") == product_id:
            return item
    return None


# ---------------------------------------------------------------------------#
# Views
# ---------------------------------------------------------------------------#
def cart_detail_view(request):
    """Render the cart detail page."""
    cart = Cart(request)

    cart_items = []
    for item in cart:
        form = AddToCartProductForm(initial={
            "quantity": item["quantity"],
            "inplace": True,
        })

        total_price = item.get("total_price", 0)
        cart_items.append({
            "product_id": item.get("product_id"),
            "product_title": item.get("product_title", _("نامشخص")),
            "product_unit_price": item.get("product_unit_price", 0),
            "product_slug": item.get("product_slug", ""),
            "product_image_url": item.get("product_image_url", ""),
            "quantity": item["quantity"],
            "total_price": total_price,
            "total_price_display": format_currency(total_price),
            "form": form,
        })

    totals = cart_totals_payload(cart)
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    selected_shipping = cart.get_shipping_method()

    context = {
        "cart_items": cart_items,
        "cart": cart,
        "shipping_methods": shipping_methods,
        "selected_shipping_method_id": selected_shipping.id if selected_shipping else None,
        "cart_totals": totals,
    }

    return render(request, "carts/cart_detail.html", context)


@require_POST
def ajax_add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartProductForm(request.POST)

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return redirect("carts:cart_detail")

    if not form.is_valid():
        return json_error(_("فرم نامعتبر است."))

    cleaned_data = form.cleaned_data
    quantity = cleaned_data["quantity"]
    cart.add(product, quantity, replace_current_quantity=cleaned_data["inplace"])

    item = _find_item(cart, product_id)
    extra = {"item": cart_item_payload(item)} if item else {}
    return json_success(
        _("محصول با موفقیت به سبد اضافه شد."),
        cart,
        extra=extra,
    )


@require_POST
def ajax_update_cart_item(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return json_error(_("درخواست نامعتبر است."))

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return json_error(_("تعداد نامعتبر است."))

    if quantity <= 0:
        cart.remove(product)
        return json_success(_("محصول از سبد حذف شد."), cart, extra={"item_id": product_id})

    cart.add(product, quantity, replace_current_quantity=True)
    item = _find_item(cart, product_id)
    return json_success(
        _("تعداد محصول به‌روزرسانی شد."),
        cart,
        extra={"item": cart_item_payload(item)} if item else None,
    )


@require_POST
def ajax_remove_from_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return redirect("carts:cart_detail")

    cart.remove(product)
    return json_success(_("محصول از سبد حذف شد."), cart, extra={"item_id": product_id})


@require_POST
def ajax_clear_cart(request):
    cart = Cart(request)

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return redirect("carts:cart_detail")

    cart.clear()
    return json_success(_("سبد خرید خالی شد."), cart)


@require_POST
def ajax_update_shipping(request):
    cart = Cart(request)

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return json_error(_("درخواست نامعتبر است."))

    shipping_id = request.POST.get("shipping_method")
    if not shipping_id:
        return json_error(_("روش ارسال انتخاب نشده است."))

    if not cart.set_shipping_method(shipping_id):
        return json_error(_("روش ارسال انتخاب شده معتبر نیست."))

    return json_success(_("روش ارسال به‌روزرسانی شد."), cart)


# ---------------------------------------------------------------------------#
# Non-AJAX fallbacks
# ---------------------------------------------------------------------------#
@require_POST
def add_to_cart_view(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartProductForm(request.POST)

    if form.is_valid():
        cleaned_data = form.cleaned_data
        quantity = cleaned_data["quantity"]
        cart.add(product, quantity, replace_current_quantity=cleaned_data["inplace"])
        messages.success(request, _(f"{product.title} به سبد خرید شما اضافه شد."))
    else:
        messages.error(request, _("اطلاعات وارد شده نامعتبر است."))

    return redirect("carts:cart_detail")


@require_POST
def update_cart_item(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartProductForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        cart.add(product, quantity, replace_current_quantity=True)
        messages.success(request, _("تعداد محصول به‌روزرسانی شد."))
    else:
        messages.error(request, _("امکان به‌روزرسانی محصول وجود ندارد."))

    return redirect("carts:cart_detail")


@require_POST
def remove_from_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.remove(product)
    return redirect("carts:cart_detail")


@require_POST
def clear_cart(request):
    cart = Cart(request)
    cart.clear()
    messages.success(request, _("سبد خرید خالی شد."))
    return redirect("carts:cart_detail")
