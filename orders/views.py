from django.conf import settings
from django.contrib.sites import requests
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

from accounts.models import UserProfile
from carts.cart import Cart
from .forms import OrderForm, OrderAddressForm
from .models import OrderItem, OrderAddress, Order, UserAddress

from django import forms


@login_required
def order_create_view(request):
    order_form = OrderForm()
    cart = Cart(request)


    if len(cart) == 0:
        messages.warning(request, _('You have not proceed to checkout page because your cart is empty.'))
        return redirect('product_list')

    if request.method == 'POST':
        order_form = OrderForm(request.POST, )

        if order_form.is_valid():
            order_obj = order_form.save(commit=False)
            order_obj.user = request.user
            order_obj.save()

            for item in cart:
                product = item['product_obj']
                OrderItem.objects.create(
                    order=order_obj,
                    product=product,
                    quantity=item['quantity'],
                    price=product.price,
                )

            cart.clear()

            request.user.first_name = order_obj.first_name
            request.user.last_name = order_obj.last_name
            request.user.save()

            messages.success(request, _('Your order has been successfully created.'))

    return render(request, 'orders/order_create.html', context={'form': OrderForm, })


@login_required
def order_history(request):
    response = requests.get(
        f'{settings.API_BASE_URL}orders/',
        headers={'Authorization': f'Token {request.user.auth_token.key}'}
    )
    orders = response.json()
    return render(request, 'store/order_history.html', {'orders': orders})
#___________________________________________________________


@login_required
def order_history(request):
    response = requests.get(
        f'{settings.API_BASE_URL}orders/',
        headers={'Authorization': f'Token {request.user.auth_token.key}'}
    )
    orders = response.json()
    return render(request, 'store/order_history.html', {'orders': orders})

#______________________________
@login_required
def order_create_view(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(request, _('سبد خرید شما خالی است.'))
        return redirect('product_list')

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
        messages.info(request, _('لطفا اطلاعات پروفایل خود را تکمیل کنید.'))

    if request.method == 'POST':
        order_form = OrderAddressForm(request.POST, user=request.user)

        if order_form.is_valid():
            try:
                with transaction.atomic():
                    # ایجاد سفارش
                    order_obj = Order.objects.create(
                        user_profile=profile,
                        order_notes=order_form.cleaned_data['order_notes']
                    )

                    # ایجاد آدرس سفارش بر اساس انتخاب کاربر
                    address_choice = order_form.cleaned_data['address_choice']

                    if address_choice == OrderAddressForm.USE_DEFAULT_ADDRESS:
                        # استفاده از آدرس پیش‌فرض
                        default_address = profile.addresses.filter(is_default=True).first()
                        if default_address:
                            self._create_order_address_from_user_address(order_obj, default_address)
                        else:
                            # اگر آدرس پیش‌فرض وجود ندارد، از پروفایل استفاده کن
                            self._create_order_address_from_profile(order_obj, profile)

                    elif address_choice == OrderAddressForm.USE_SAVED_ADDRESS:
                        # استفاده از آدرس ذخیره شده انتخاب شده
                        saved_address = order_form.cleaned_data['saved_address']
                        self._create_order_address_from_user_address(order_obj, saved_address)

                    elif address_choice == OrderAddressForm.USE_NEW_ADDRESS:
                        # ایجاد آدرس جدید
                        order_address = OrderAddress.objects.create(
                            order=order_obj,
                            first_name=order_form.cleaned_data['first_name'],
                            last_name=order_form.cleaned_data['last_name'],
                            phone_number=order_form.cleaned_data['phone_number'],
                            country=order_form.cleaned_data['country'],
                            province=order_form.cleaned_data['province'],
                            city=order_form.cleaned_data['city'],
                            address=order_form.cleaned_data['address'],
                            postal_code=order_form.cleaned_data['postal_code']
                        )

                        # ذخیره آدرس جدید در پروفایل کاربر اگر درخواست شده
                        if order_form.cleaned_data.get('save_new_address'):
                            UserAddress.objects.create(
                                user_profile=profile,
                                title=order_form.cleaned_data.get('address_title', 'آدرس جدید'),
                                first_name=order_address.first_name,
                                last_name=order_address.last_name,
                                phone_number=order_address.phone_number,
                                country=order_address.country,
                                province=order_address.province,
                                city=order_address.city,
                                address=order_address.address,
                                postal_code=order_address.postal_code,
                                is_default=not profile.addresses.filter(is_default=True).exists()
                            )

                    # ایجاد آیتم‌های سفارش
                    for item in cart:
                        product = item['product_obj']
                        OrderItem.objects.create(
                            order=order_obj,
                            product=product,
                            quantity=item['quantity'],
                            price=product.price,
                        )

                    cart.clear()
                    messages.success(request, _('سفارش شما با موفقیت ایجاد شد.'))
                    return redirect('order_detail', order_id=order_obj.id)

            except Exception as e:
                messages.error(request, _('خطایی در ایجاد سفارش رخ داد.'))
                logger.error(f"Order creation error: {str(e)}")

    else:
        order_form = OrderAddressForm(user=request.user)

    return render(request, 'orders/order_create.html', {
        'form': order_form,
        'cart': cart
    })


def _create_order_address_from_user_address(self, order, user_address):
    """ایجاد آدرس سفارش از آدرس کاربر"""
    return OrderAddress.objects.create(
        order=order,
        first_name=user_address.first_name,
        last_name=user_address.last_name,
        phone_number=user_address.phone_number,
        country=user_address.country,
        province=user_address.province,
        city=user_address.city,
        address=user_address.address,
        postal_code=user_address.postal_code
    )


def _create_order_address_from_profile(self, order, profile):
    """ایجاد آدرس سفارش از پروفایل کاربر"""
    return OrderAddress.objects.create(
        order=order,
        first_name=profile.first_name,
        last_name=profile.last_name,
        phone_number=profile.user.phone_number,
        country=profile.country,
        province=profile.province,
        city=profile.city,
        address=profile.address,
        postal_code=profile.postal_code
    )


class OrderForm(forms.ModelForm):
    # فیلدهای فقط نمایشی - غیرقابل ویرایش
    phone_number = forms.CharField(
        max_length=15,
        disabled=True,
        label=_('شماره تماس'),
        required=False
    )
    full_name = forms.CharField(
        max_length=200,
        disabled=True,
        label=_('نام کامل'),
        required=False
    )

    class Meta:
        model = Order
        fields = ['order_notes']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile

            # تنظیم مقادیر اولیه فقط برای نمایش
            self.fields['phone_number'].initial = self.user.phone_number
            self.fields['full_name'].initial = profile.full_name

            # غیرفعال کردن تمام فیلدهای اطلاعات شخصی
            for field_name in self.fields:
                if field_name not in ['order_notes']:
                    self.fields[field_name].disabled = True

    def clean(self):
        # جلوگیری از تغییرات غیرمجاز
        cleaned_data = super().clean()
        return cleaned_data


@login_required
def order_detail(request, order_id):
    try:
        order = Order.objects.select_related('user_profile').prefetch_related(
            'items__product'
        ).get(
            id=order_id,
            user_profile__user=request.user
        )
    except Order.DoesNotExist:
        raise Http404(_("سفارش یافت نشد."))

    return render(request, 'orders/order_detail.html', {
        'order': order
    })