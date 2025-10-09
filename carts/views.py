from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.conf import settings
import requests
import json
from products.models import Product
from .cart import Cart
from .forms import AddToCartProductForm

# در carts/views.py
from django.http import JsonResponse
# def cart_detail_view(request):
#     """نمایش جزئیات سبد خرید"""
#     cart = Cart(request)
#     forms = []
#
#     for item in cart:
#         form = AddToCartProductForm(initial={
#             'quantity': item['quantity'],
#             'inplace': True,
#         })
#         forms.append(form)
#
#     # استفاده از zip برای ترکیب آیتم‌های سبد خرید و فرم‌ها
#     cart_with_forms = zip(cart, forms)
#
#     return render(request, 'carts/cart_detail.html', {
#         'cart_with_forms': cart_with_forms,
#         'cart': cart  # در صورت نیاز برای دسترسی به سایر اطلاعات سبد خرید
#     })

#
# def cart_detail_view(request):
#     """نمایش جزئیات سبد خرید"""
#     cart = Cart(request)
#
#     # ایجاد لیست آیتم‌ها با اطلاعات کامل
#     cart_items = []
#     for item in cart:
#         product = item.get('product')
#         if product:
#             form = AddToCartProductForm(initial={
#                 'quantity': item['quantity'],
#                 'inplace': True,
#             })
#             cart_items.append({
#                 'product': product,
#                 'quantity': item['quantity'],
#                 'total_price': item['total_price'],
#                 'image_url': product.image.url if product.image else '',
#                 'form': form
#             })
#
#     return render(request, 'carts/cart_detail.html', {
#         'cart_items': cart_items,
#         'cart': cart
#     })


def cart_detail_view(request):
    """نمایش جزئیات سبد خرید"""
    cart = Cart(request)

    # ایجاد لیست آیتم‌ها با اطلاعات لازم برای template
    cart_items = []
    for item in cart:
        form = AddToCartProductForm(initial={
            'quantity': item['quantity'],
            'inplace': True,
        })

        cart_items.append({
            'product_id': item.get('product_id'),
            'product_title': item.get('product_title', 'محصول'),
            'product_unit_price': item.get('product_unit_price', 0),
            'product_slug': item.get('product_slug', ''),
            'product_image_url': item.get('product_image_url', ''),
            'quantity': item['quantity'],
            'total_price': item.get('total_price', 0),
            'form': form
        })

    return render(request, 'carts/cart_detail.html', {
        'cart_items': cart_items,
        'cart': cart
    })


@require_POST
def ajax_add_to_cart(request, product_id):
    """افزودن محصول به سبد خرید با AJAX"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartProductForm(request.POST)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if form.is_valid():
            cleaned_data = form.cleaned_data
            quantity = cleaned_data['quantity']
            cart.add(product, quantity, replace_current_quantity=cleaned_data['inplace'])

            return JsonResponse({
                'success': True,
                'total_items': len(cart),
                'total_price': str(cart.get_total_price()),
                'item_id': product_id,
                'item_quantity': quantity,
                'message': f'{product.title} به سبد خرید اضافه شد'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'خطا در افزودن محصول به سبد خرید'
            })

    return redirect('carts:cart_detail')


@require_POST
def ajax_update_cart_item(request, product_id):
    """به‌روزرسانی تعداد محصول در سبد خرید با AJAX"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            quantity = int(request.POST.get('quantity', 1))

            if quantity <= 0:
                cart.remove(product)
                return JsonResponse({
                    'success': True,
                    'total_items': len(cart),
                    'total_price': str(cart.get_total_price()),
                    'item_id': product_id,
                    'message': f'{product.title} از سبد خرید حذف شد'
                })

            # به‌روزرسانی مقدار
            cart.add(product, quantity, replace_current_quantity=True)

            # محاسبه قیمت کل برای این آیتم خاص
            item_total_price = 0
            for item in cart:
                if item.get('product_id') == product_id:
                    item_total_price = item.get('total_price', 0)
                    break

            return JsonResponse({
                'success': True,
                'total_items': len(cart),
                'total_price': str(cart.get_total_price()),
                'item_id': product_id,
                'item_quantity': quantity,
                'item_total_price': str(item_total_price),
                'message': f'تعداد {product.title} به روز رسانی شد'
            })

        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'مقدار تعداد نامعتبر است'
            })

    return JsonResponse({'success': False})
#
# @require_POST
# def ajax_update_cart_item(request, product_id):
#     """به‌روزرسانی تعداد محصول در سبد خرید با AJAX"""
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         try:
#             quantity = int(request.POST.get('quantity', 1))
#
#             if quantity <= 0:
#                 cart.remove(product)
#                 success = False
#             else:
#                 success = cart.update_item_price(product_id, quantity)
#
#             if success:
#                 # محاسبه قیمت‌های جدید
#                 item_total = 0
#                 for item in cart:
#                     if 'product' in item and str(item['product'].id) == str(product_id):
#                         item_total = item['total_price']
#                         break
#
#                 return JsonResponse({
#                     'success': True,
#                     'total_items': len(cart),
#                     'total_price': str(cart.get_total_price()),
#                     'item_id': product_id,
#                     'item_quantity': quantity,
#                     'item_total': str(item_total),
#                     'message': f'تعداد {product.title} به روز رسانی شد'
#                 })
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'خطا در به روز رسانی تعداد محصول'
#                 })
#
#         except ValueError:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'مقدار تعداد نامعتبر است'
#             })
#
#     return JsonResponse({'success': False})
#
#
# @require_POST
# def ajax_add_to_cart(request, product_id):
#     """افزودن محصول به سبد خرید با AJAX"""
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#     form = AddToCartProductForm(request.POST)
#
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         if form.is_valid():
#             cleaned_data = form.cleaned_data
#             quantity = cleaned_data['quantity']
#             cart.add(product, quantity, replace_current_quantity=cleaned_data['inplace'])
#
#             return JsonResponse({
#                 'success': True,
#                 'total_items': len(cart),
#                 'total_price': str(cart.get_total_price()),
#                 'item_id': product_id,
#                 'item_quantity': quantity,
#                 'item_total': str(cart.cart[str(product_id)]['total_price']),
#                 'message': f'{product.title} به سبد خرید اضافه شد'
#             })
#         else:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'خطا در افزودن محصول به سبد خرید'
#             })
#
#     # اگر AJAX نبود، redirect کن
#     return redirect('carts:cart_detail')
#

@require_POST
def ajax_remove_from_cart(request, product_id):
    """حذف محصول از سبد خرید با AJAX"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart.remove(product)

        return JsonResponse({
            'success': True,
            'total_items': len(cart),
            'total_price': str(cart.get_total_price()),
            'item_id': product_id,
            'message': f'{product.title} از سبد خرید حذف شد'
        })

    return redirect('carts:cart_detail')


@require_POST
def ajax_clear_cart(request):
    """پاک کردن کامل سبد خرید با AJAX"""
    cart = Cart(request)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if len(cart):
            cart.clear()
            return JsonResponse({
                'success': True,
                'total_items': 0,
                'total_price': '0',
                'message': 'تمام محصولات از سبد خرید حذف شدند'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'سبد خرید شما قبلاً خالی است'
            })

    return redirect('pages/home')


@require_POST
def ajax_clear_cart(request):
    """پاک کردن کامل سبد خرید با AJAX"""
    cart = Cart(request)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if len(cart):
            cart.clear()
            return JsonResponse({
                'success': True,
                'total_items': 0,
                'total_price': '0',
                'message': 'تمام محصولات از سبد خرید حذف شدند'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'سبد خرید شما قبلاً خالی است'
            })

    return JsonResponse({'success': False})






@require_POST
def add_to_cart_view(request, product_id):
    """افزودن محصول به سبد خرید"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartProductForm(request.POST)

    if form.is_valid():
        cleaned_data = form.cleaned_data
        quantity = cleaned_data['quantity']
        cart.add(product, quantity, replace_current_quantity=cleaned_data['inplace'])
        messages.success(request, _(f'{product.title} به سبد خرید اضافه شد'))
    else:
        messages.error(request, _('خطا در افزودن محصول به سبد خرید'))

    return redirect('carts:cart_detail')


@require_POST
def remove_from_cart(request, product_id):
    """حذف محصول از سبد خرید"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, _(f'{product.title} از سبد خرید حذف شد'))
    return redirect('carts:cart_detail')


@require_POST
def clear_cart(request):
    """پاک کردن کامل سبد خرید"""
    cart = Cart(request)

    if len(cart):
        cart.clear()
        messages.success(request, _('تمام محصولات از سبد خرید حذف شدند'))
    else:
        messages.warning(request, _('سبد خرید شما قبلاً خالی است'))

    return redirect('carts:cart_detail')


@require_POST
def update_cart_item(request, product_id):
    """به روز رسانی تعداد محصول در سبد خرید"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartProductForm(request.POST)

    if form.is_valid():
        cleaned_data = form.cleaned_data
        quantity = cleaned_data['quantity']
        cart.add(product, quantity, replace_current_quantity=True)
        messages.success(request, _(f'تعداد {product.title} به روز رسانی شد'))
    else:
        messages.error(request, _('خطا در به روز رسانی تعداد محصول'))

    return redirect('carts:cart_detail')


# اگر می‌خواهید از API استفاده کنید، این توابع را فعال کنید
# و توابع بالا را غیرفعال یا حذف کنید

"""
# @login_required
# def api_cart_view(request):
#     # نمایش سبد خرید مبتنی بر API
#     headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
#     try:
#         response = requests.get(f'{settings.API_BASE_URL}carts/', headers=headers)
#         response.raise_for_status()
#         cart = response.json()
#         return render(request, 'carts/api_cart.html', {'cart': cart})
#     except requests.RequestException:
#         messages.error(request, _('خطا در دریافت اطلاعات سبد خرید'))
#         return redirect('product_list')
# 
# @login_required
# @require_POST
# def api_add_to_cart(request, product_id):
#     # افزودن محصول به سبد خرید مبتنی بر API
#     headers = {
#         'Authorization': f'Bearer {request.session.get("access_token")}',
#         'Content-Type': 'application/json'
#     }
#     data = {'product': product_id, 'quantity': 1}
# 
#     try:
#         response = requests.post(
#             f'{settings.API_BASE_URL}cart/items/',
#             json=data,
#             headers=headers
#         )
#         response.raise_for_status()
#         messages.success(request, _('محصول به سبد خرید اضافه شد'))
#     except requests.RequestException:
#         messages.error(request, _('خطا در افزودن محصول به سبد خرید'))
# 
#     return redirect('product_list')
# 
# @login_required
# def api_checkout(request):
#     # پرداخت و ایجاد سفارش مبتنی بر API
#     if request.method == 'POST':
#         cart_id = request.session.get('cart_id')
#         if not cart_id:
#             return redirect('carts:api_cart')
# 
#         headers = {'Authorization': f'Token {request.user.auth_token.key}'}
# 
#         try:
#             response = requests.post(
#                 f'{settings.API_BASE_URL}orders/',
#                 data={'cart_id': cart_id},
#                 headers=headers
#             )
#             response.raise_for_status()
# 
#             if response.status_code == 201:
#                 del request.session['cart_id']
#                 order_id = response.json()['id']
#                 return redirect('order_confirmation', order_id=order_id)
#         except requests.RequestException:
#             messages.error(request, _('خطا در ایجاد سفارش'))
# 
#     return render(request, 'carts/api_checkout.html')
"""



# from django.shortcuts import render, get_object_or_404, redirect
# from django.views.decorators.http import require_POST
# from products.models import Product
# from django.contrib import messages
# from django.utils.translation import gettext as _
# import requests
# from django.conf import settings
# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from .cart import Cart
# from .forms import AddToCartProductForm
#
#
# def cart_detail_view(request):
#     cart = Cart(request)
#
#     for item in cart:
#         item['product_update_quantity_form'] = AddToCartProductForm(initial={
#             'quantity': item['quantity'],
#             'inplace': True,
#         })
#     return render(request, 'carts/cart_detail.html', context={'cart': cart, })
#
#
# @require_POST
# def add_to_cart_view(request, product_id):
#     cart = Cart(request)
#
#     product = get_object_or_404(Product, id=product_id)
#     form = AddToCartProductForm(request.POST)
#
#     if form.is_valid():
#         cleaned_data = form.cleaned_data
#         quantity = cleaned_data['quantity']
#         cart.add(product, quantity, replace_current_quantity=cleaned_data['inplace'])
#
#     return redirect('carts:cart_detail')
#
#
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#
#     product = get_object_or_404(Product, id=product_id)
#
#     cart.remove(product)
#
#     return redirect('carts:cart_detail')
#
#
# @require_POST
# def clear_cart(request):
#     cart = Cart(request)
#
#     if len(cart):
#         cart.clear()
#         messages.success(request, _('All products successfully removed from your cart.'))
#     else:
#         messages.error(request, _('Your cart is already empty.'))
#     return redirect('product_list')
#
# #________________________________
#
# from django.shortcuts import render, get_object_or_404, redirect
# from django.views.decorators.http import require_POST
# from products.models import Product
# from django.contrib import messages
# from django.utils.translation import gettext as _
#
# from .models import Cart
# from .forms import AddToCartProductForm
#
#
# def cart_detail_view(request):
#     cart = Cart(request)
#
#     for item in cart:
#         item['product_update_quantity_form'] = AddToCartProductForm(initial={
#             'quantity': item['quantity'],
#             'inplace': True,
#         })
#     return render(request, 'cart/carts_detail.html', context={'cart': cart, })
#
#
# @require_POST
# def add_to_cart_view(request, product_id):
#     cart = Cart(request)
#
#     product = get_object_or_404(Product, id=product_id)
#     form = AddToCartProductForm(request.POST)
#
#     if form.is_valid():
#         cleaned_data = form.cleaned_data
#         quantity = cleaned_data['quantity']
#         cart.add(product, quantity, replace_current_quantity=cleaned_data['inplace'])
#
#     return redirect('carts:cart_detail')
#
#
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#
#     product = get_object_or_404(Product, id=product_id)
#
#     cart.remove(product)
#
#     return redirect('carts:cart_detail')
#
#
# @require_POST
# def clear_cart(request):
#     cart = Cart(request)
#
#     if len(cart):
#         cart.clear()
#         messages.success(request, _('All products successfully removed from your cart.'))
#     else:
#         messages.error(request, _('Your cart is already empty.'))
#     return redirect('product_list')
# from django.shortcuts import render, get_object_or_404, redirect
# from django.views.decorators.http import require_POST
# from products.models import Product
# from django.contrib import messages
# from django.utils.translation import gettext as _
#
# from .models import Cart
# from .forms import AddToCartProductForm
#
#
# def cart_detail_view(request):
#     cart = Cart(request)
#
#     for item in cart:
#         item['product_update_quantity_form'] = AddToCartProductForm(initial={
#             'quantity': item['quantity'],
#             'inplace': True,
#         })
#     return render(request, 'carts/cart_detail.html', context={'cart': cart, })
#
#
# @require_POST
# def add_to_cart_view(request, product_id):
#     cart = Cart(request)
#
#     product = get_object_or_404(Product, id=product_id)
#     form = AddToCartProductForm(request.POST)
#
#     if form.is_valid():
#         cleaned_data = form.cleaned_data
#         quantity = cleaned_data['quantity']
#         cart.add(product, quantity, replace_current_quantity=cleaned_data['inplace'])
#
#     return redirect('carts:cart_detail')
#
#
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#
#     product = get_object_or_404(Product, id=product_id)
#
#     cart.remove(product)
#
#     return redirect('carts:cart_detail')
#
#
# @require_POST
# def clear_cart(request):
#     cart = Cart(request)
#
#     if len(cart):
#         cart.clear()
#         messages.success(request, _('All products successfully removed from your cart.'))
#     else:
#         messages.error(request, _('Your cart is already empty.'))
#     return redirect('product_list')
#
# @login_required
# def cart_view(request):
#     headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
#     response = requests.get(f'{API_BASE_URL}carts/', headers=headers)
#     cart = response.json()
#     return render(request, 'cart/view.html', {'cart': cart})
#
# @login_required
# def add_to_cart(request, product_id):
#     if request.method == 'POST':
#         headers = {
#             'Authorization': f'Bearer {request.session.get("access_token")}',
#             'Content-Type': 'application/json'
#         }
#         data = {'product': product_id, 'quantity': 1}
#         requests.post(f'{API_BASE_URL}cart/items/', json=data, headers=headers)
#     return redirect('product_list')
#
#
# @login_required
# def cart(request):
#     # ایجاد یا دریافت سبد خرید
#     cart_id = request.session.get('cart_id')
#     if not cart_id:
#         response = requests.post(f'{settings.API_BASE_URL}carts/')
#         cart_id = response.json()['id']
#         request.session['cart_id'] = cart_id
#
#     # دریافت محتویات سبد خرید
#     response = requests.get(f'{settings.API_BASE_URL}carts/{cart_id}/')
#     cart = response.json()
#
#     return render(request, 'store/cart.html', {'cart': cart})
#
#
# @login_required
# def add_to_cart(request, product_id):
#     cart_id = request.session.get('cart_id')
#     if not cart_id:
#         return redirect('product_list')
#
#     data = {
#         'product': product_id,
#         'quantity': 1
#     }
#
#     requests.post(
#         f'{settings.API_BASE_URL}carts/{cart_id}/items/',
#         data=data
#     )
#
#     return redirect('cart')
#
#
# @login_required
# def checkout(request):
#     if request.method == 'POST':
#         cart_id = request.session.get('cart_id')
#         if not cart_id:
#             return redirect('cart')
#
#         # ایجاد سفارش
#         response = requests.post(
#             f'{settings.API_BASE_URL}orders/',
#             data={'cart_id': cart_id},
#             headers={'Authorization': f'Token {request.user.auth_token.key}'}
#         )
#
#         if response.status_code == 201:
#             del request.session['cart_id']
#             return redirect('order_confirmation', order_id=response.json()['id'])
#
#     return render(request, 'carts/checkout.html')
#
#
# login_required
# def cart(request):
#     # ایجاد یا دریافت سبد خرید
#     cart_id = request.session.get('cart_id')
#     if not cart_id:
#         response = requests.post(f'{settings.API_BASE_URL}carts/')
#         cart_id = response.json()['id']
#         request.session['cart_id'] = cart_id
#
#     # دریافت محتویات سبد خرید
#     response = requests.get(f'{settings.API_BASE_URL}carts/{cart_id}/')
#     cart = response.json()
#
#     return render(request, 'carts/cart.html', {'cart': cart})
#
#
# @login_required
# def add_to_cart(request, product_id):
#     cart_id = request.session.get('cart_id')
#     if not cart_id:
#         return redirect('product_list')
#
#     data = {
#         'product': product_id,
#         'quantity': 1
#     }
#
#     requests.post(
#         f'{settings.API_BASE_URL}carts/{cart_id}/items/',
#         data=data
#     )
#
#     return redirect('cart')
#
#
# @login_required
# def checkout(request):
#     if request.method == 'POST':
#         cart_id = request.session.get('cart_id')
#         if not cart_id:
#             return redirect('cart')
#
#         # ایجاد سفارش
#         response = requests.post(
#             f'{settings.API_BASE_URL}orders/',
#             data={'cart_id': cart_id},
#             headers={'Authorization': f'Token {request.user.auth_token.key}'}
#         )
#
#         if response.status_code == 201:
#             del request.session['cart_id']
#             return redirect('order_confirmation', order_id=response.json()['id'])
#
#     return render(request, 'carts/checkout.html')
#
#
