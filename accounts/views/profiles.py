from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import cache
from django.views import View
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum, Avg, Count
from pymongo.asynchronous.auth import authenticate

from accounts.models import UserProfile, LoginHistory, BlockedNumber, SensitiveDataHistory, PhoneNumberHistory
from accounts.forms import ProfileEditForm, LoginForm, ChangePhoneNumberForm, VerifyPhoneChangeForm
import logging

from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Max

from accounts.services import PhoneService
from accounts.services.otp_service import OTPService
from accounts.utils import get_client_ip
from config import settings
from orders.models import Order  # فرض بر این است که مدل Order وجود دارد





from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, F
from orders.models import  Order, OrderItem


logger = logging.getLogger(__name__)
User = get_user_model()
#
#
# @login_required
# def profile_view(request):
#     try:
#         profile = request.user.profile
#     except UserProfile.DoesNotExist:
#         profile = UserProfile.objects.create(user=request.user)
#
#     # دریافت سفارشات کاربر - استفاده از user_id به جای user
#     orders = Order.objects.filter(customer_id=request.user).order_by('-datetime_created')
#
#     # صفحه‌بندی سفارشات
#     paginator = Paginator(orders, 10)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#
#     # محاسبه آمار خرید
#     total_orders = orders.count()
#
#     # سفارشات پرداخت شده: وضعیت 'ORDER_STATUS_PAID'
#     completed_orders = Order.objects.filter(status='ORDER_STATUS_PAID').count()
#
#     # محاسبه مجموع مبلغ پرداخت شدهF
#     total_spent = 0
#     paid_orders = orders.filter(status='ORDER_STATUS_PAID')
#     for order in paid_orders:
#         # جمع کل آیتم‌های این سفارش
#         order_total = order.items.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
#         total_spent += order_total
#
#     # میانگین مبلغ سفارشات پرداخت شده
#     avg_order_value = total_spent / completed_orders if completed_orders > 0 else 0
#
#     # 5 سفارش اخیر برای تب خلاصه
#     recent_orders = orders[:5]
#
#     context = {
#         'profile': profile,
#         'orders': page_obj,
#         'recent_orders': recent_orders,
#         'total_orders': total_orders,
#         'completed_orders': completed_orders,
#         'total_spent': total_spent,
#         'avg_order_value': avg_order_value,
#     }
#
#     return render(request, 'accounts/profile1.html', context)

# @login_required
# def profile_view(request):
#     try:
#         profile = request.user.profile
#     except UserProfile.DoesNotExist:
#         profile = UserProfile.objects.create(user=request.user)
#
#     # FIX: Use user_profile instead of customer_id
#     orders = Order.objects.filter(user_profile=profile).order_by('-datetime_created')
#
#     # صفحه‌بندی سفارشات
#     paginator = Paginator(orders, 10)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#
#     # محاسبه آمار خرید
#     total_orders = orders.count()
#
#     # FIX: Also filter completed orders by user profile
#     completed_orders = orders.filter(status='ORDER_STATUS_PAID').count()
#
#     # محاسبه مجموع مبلغ پرداخت شده
#     total_spent = 0
#     paid_orders = orders.filter(status='ORDER_STATUS_PAID')
#     for order in paid_orders:
#         # جمع کل آیتم‌های این سفارش
#         order_total = order.items.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
#         total_spent += order_total
#
#     # میانگین مبلغ سفارشات پرداخت شده
#     avg_order_value = total_spent / completed_orders if completed_orders > 0 else 0
#
#     # 5 سفارش اخیر برای تب خلاصه
#     recent_orders = orders[:5]
#
#     context = {
#         'profile': profile,
#         'orders': page_obj,
#         'recent_orders': recent_orders,
#         'total_orders': total_orders,
#         'completed_orders': completed_orders,
#         'total_spent': total_spent,
#         'avg_order_value': avg_order_value,
#     }
#
#     return render(request, 'accounts/profile1.html', context)


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # تصحیح: استفاده از user_profile به جای customer_id
    orders = Order.objects.filter(user_profile=profile).order_by('-datetime_created')

    # صفحه‌بندی سفارشات
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # محاسبه آمار خرید
    total_orders = orders.count()

    # تصحیح: فیلتر کردن سفارشات پرداخت شده کاربر جاری
    completed_orders = orders.filter(status=Order.ORDER_STATUS_PAID).count()

    # محاسبه مجموع مبلغ پرداخت شده
    total_spent = 0
    paid_orders = orders.filter(status=Order.ORDER_STATUS_PAID)
    for order in paid_orders:
        # استفاده از متد total_price که در مدل Order تعریف کردید
        total_spent += order.total_price

    # میانگین مبلغ سفارشات پرداخت شده
    avg_order_value = total_spent / completed_orders if completed_orders > 0 else 0

    # 5 سفارش اخیر برای تب خلاصه
    recent_orders = orders[:5]

    context = {
        'profile': profile,
        'orders': page_obj,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
        'avg_order_value': avg_order_value,
    }

    return render(request, 'accounts/profile1.html', context)


@login_required
def change_phone_number(request):
    if request.method == 'POST':
        form = ChangePhoneNumberForm(request.POST, user=request.user)

        if form.is_valid():
            new_phone = form.cleaned_data['new_phone_number']

            # تولید و ارسال OTP
            otp_code = OTPService.generate_otp(new_phone)
            OTPService.send_otp_sms(new_phone, otp_code)

            # ذخیره درخواست تغییر در session
            request.session['pending_phone_change'] = {
                'new_phone': new_phone,
                'otp_sent_to': new_phone,
                'attempts': 0
            }

            messages.info(request, _('کد تأیید به شماره جدید ارسال شد.'))
            return redirect('verify_phone_change')

    else:
        form = ChangePhoneNumberForm(user=request.user)

    return render(request, 'accounts/change_phone.html', {'form': form})


@login_required
def verify_phone_change(request):
    if 'pending_phone_change' not in request.session:
        messages.error(request, _('درخواست تغییر شماره تلفن یافت نشد.'))
        return redirect('change_phone_number')

    pending_data = request.session['pending_phone_change']

    if request.method == 'POST':
        form = VerifyPhoneChangeForm(request.POST)

        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            new_phone = pending_data['new_phone']

            # بررسی OTP
            if OTPService.verify_otp(new_phone, verification_code):
                try:
                    with transaction.atomic():
                        # ذخیره تاریخچه
                        SensitiveDataHistory.objects.create(
                            user=request.user,
                            field_name='phone_number',
                            old_value=request.user.phone_number,
                            new_value=new_phone,
                            verified=True
                        )

                        PhoneNumberHistory.objects.create(
                            user=request.user,
                            phone_number=request.user.phone_number,
                            is_primary=False
                        )

                        # اعمال تغییر
                        old_phone = request.user.phone_number
                        request.user.phone_number = new_phone
                        request.user.save()

                        # به روزرسانی پروفایل اگر نیاز باشد
                        if hasattr(request.user, 'profile'):
                            request.user.profile.save()

                        # پاک کردن session
                        del request.session['pending_phone_change']

                        messages.success(request, _('شماره تلفن با موفقیت تغییر کرد.'))
                        logger.info(f"User {request.user.id} changed phone from {old_phone} to {new_phone}")

                        return redirect('profile')

                except Exception as e:
                    messages.error(request, _('خطایی در تغییر شماره تلفن رخ داد.'))
                    logger.error(f"Phone change error: {str(e)}")

            else:
                pending_data['attempts'] += 1
                request.session['pending_phone_change'] = pending_data

                if pending_data['attempts'] >= 3:
                    del request.session['pending_phone_change']
                    messages.error(request, _('تعداد تلاش‌های شما بیش از حد مجاز است.'))
                    return redirect('change_phone_number')

                messages.error(request, _('کد تأیید نامعتبر است.'))

    else:
        form = VerifyPhoneChangeForm()

    return render(request, 'accounts/verify_phone_change.html', {
        'form': form,
        'phone': pending_data['otp_sent_to'][-4:]  # نمایش 4 رقم آخر
    })
# class LoginView(View):
#     """
#     ویو حرفه‌ای ورود به سیستم با مدیریت امنیتی پیشرفته
#     و لاگ‌گیری جامع
#     """
#
#     template_name = 'accounts/login.html'
#     max_login_attempts = 5
#     lockout_time = 300  # 5 دقیقه قفل شدن پس از تلاش‌های ناموفق
#
#     def get(self, request):
#         """نمایش فرم ورود"""
#         if request.user.is_authenticated:
#             messages.info(request, 'شما قبلا وارد سیستم شده‌اید.')
#             return redirect('pages:home')
#
#         form = LoginForm()
#         return render(request, self.template_name, {'form': form})
#
#     def post(self, request):
#         """پردازش فرم ورود با مدیریت امنیتی"""
#         form = LoginForm(request.POST)
#
#         if not form.is_valid():
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, f"{form.fields[field].label}: {error}")
#             logger.warning(f"Login form invalid: {form.errors}")
#             return render(request, self.template_name, {'form': form})
#
#         try:
#             # شروع تراکنش اتمیک برای عملیات ورود
#             with transaction.atomic():
#                 return self._process_login(request, form)
#         except Exception as e:
#             logger.error(f"Login error: {str(e)}", exc_info=True)
#             messages.error(request, 'خطایی در ورود به سیستم رخ داده است.')
#             return render(request, self.template_name, {'form': form})
#
#     def _process_login(self, request, form):
#         """پردازش درخواست ورود در تراکنش اتمیک"""
#         phone = form.cleaned_data['phone']
#         password = form.cleaned_data['password']
#         remember_me = form.cleaned_data.get('remember_me', False)
#
#         logger.info(f"Login attempt for phone: {phone}")
#
#         # استانداردسازی شماره تلفن
#         try:
#             db_phone = PhoneService.standardize_phone(phone, 'database')
#             display_phone = PhoneService.standardize_phone(phone, 'display')
#             logger.info(f"Standardized phone: {db_phone}")
#         except ValidationError as e:
#             messages.error(request, 'شماره تلفن معتبر نیست.')
#             logger.warning(f"Invalid phone format: {phone}, error: {str(e)}")
#             return render(request, self.template_name, {'form': form})
#
#         # بررسی مسدود بودن شماره تلفن
#         if self._is_phone_blocked(db_phone):
#             messages.error(request, 'این شماره تلفن مسدود شده است.')
#             logger.warning(f"Blocked phone attempt: {db_phone}")
#             return render(request, self.template_name, {'form': form})
#
#         # بررسی تعداد تلاش‌های ناموفق
#         if self._is_login_blocked(request, db_phone):
#             messages.error(request, 'به دلیل تلاش‌های ناموفق متعدد، حساب شما به طور موقت مسدود شده است.')
#             logger.warning(f"Login blocked for phone: {db_phone}")
#             return render(request, self.template_name, {'form': form})
#
#         # احراز هویت کاربر - استفاده از backend پیش فرض Django
#         User = get_user_model()
#
#         # ابتدا بررسی وجود کاربر
#         try:
#             user = User.objects.get(phone=db_phone)
#
#             # بررسی فعال بودن حساب کاربری
#             if not user.is_active:
#                 messages.error(request, 'حساب کاربری شما غیرفعال است.')
#                 logger.warning(f"Inactive user login attempt: {db_phone}")
#                 return render(request, self.template_name, {'form': form})
#
#             # بررسی تأیید شماره تلفن
#             if not user.is_phone_verified:
#                 messages.error(request, 'لطفا ابتدا شماره تلفن خود را تأیید کنید.')
#                 logger.warning(f"Unverified phone attempt: {db_phone}")
#                 # ذخیره اطلاعات برای صفحه تأیید
#                 request.session['unverified_phone'] = db_phone
#                 return redirect('accounts:verify_otp')
#
#         except User.DoesNotExist:
#             # کاربر وجود ندارد
#             messages.error(request, 'شماره تلفن یا رمز عبور اشتباه است.')
#             logger.warning(f"Login attempt for non-existent user: {db_phone}")
#             self._increment_failed_attempts(db_phone)
#             return render(request, self.template_name, {'form': form})
#
#         # احراز هویت با استفاده از authenticate استاندارد Django
#         user = authenticate(request, phone=db_phone, password=password)
#
#         logger.debug(f"Authentication result for {db_phone}: {user}")
#
#         if user is not None:
#             # ورود کاربر
#             try:
#                 login(request, user)
#
#                 # بازنشانی شمارنده تلاش‌های ناموفق
#                 self._reset_failed_attempts(db_phone)
#                 logger.info(f"User {db_phone} login successful")
#             except Exception as e:
#                 logger.error(f"Login failed for {db_phone}: {str(e)}")
#                 messages.error(request, 'خطا در ورود به سیستم. لطفاً مجدداً تلاش کنید.')
#                 return render(request, self.template_name, {'form': form})
#
#             # تنظیم session بر اساس remember me
#             if not remember_me:
#                 request.session.set_expiry(0)  # Session در مرورگر بسته شود
#             else:
#                 request.session.set_expiry(settings.SESSION_COOKIE_AGE)
#
#             # ذخیره session
#             request.session.save()
#             logger.info(f"Session settings applied, remember_me: {remember_me}")
#
#             # ثبت تاریخچه ورود موفق
#             try:
#                 LoginHistory.objects.create(
#                     user=user,
#                     ip_address=get_client_ip(request),
#                     user_agent=request.META.get('HTTP_USER_AGENT', ''),
#                     is_successful=True
#                 )
#                 logger.info(f"Login history recorded for {db_phone}")
#             except Exception as e:
#                 logger.error(f"Failed to create login history: {str(e)}")
#
#             # هدایت به صفحه مورد نظر یا صفحه پیش‌فرض
#             next_url = request.GET.get('next') or 'pages:home'
#             logger.info(f"Redirecting to: {next_url}")
#             return redirect(next_url)
#
#         else:
#             # افزایش شمارنده تلاش‌های ناموفق
#             self._increment_failed_attempts(db_phone)
#
#             # ثبت تاریخچه ورود ناموفق
#             try:
#                 LoginHistory.objects.create(
#                     user=user,
#                     ip_address=get_client_ip(request),
#                     user_agent=request.META.get('HTTP_USER_AGENT', ''),
#                     is_successful=False
#                 )
#                 logger.warning(f"Failed login for user: {db_phone}")
#             except Exception as e:
#                 logger.error(f"Error recording failed login: {str(e)}")
#
#             messages.error(request, 'شماره تلفن یا رمز عبور اشتباه است.')
#             return render(request, self.template_name, {'form': form})
#
#     def _is_phone_blocked(self, phone):
#         """بررسی مسدود بودن شماره تلفن"""
#         try:
#             return BlockedNumber.objects.filter(phone=phone).exists()
#         except Exception as e:
#             logger.error(f"Error checking blocked numbers: {str(e)}")
#             return False
#
#     def _is_login_blocked(self, request, phone):
#         """بررسی مسدود شدن موقت به دلیل تلاش‌های ناموفق"""
#         cache_key = f"login_attempts_{phone}"
#         attempts = cache.get(cache_key, 0)
#
#         return attempts >= self.max_login_attempts
#
#     def _increment_failed_attempts(self, phone):
#         """افزایش شمارنده تلاش‌های ناموفق"""
#         cache_key = f"login_attempts_{phone}"
#         attempts = cache.get(cache_key, 0) + 1
#
#         if attempts >= self.max_login_attempts:
#             # قفل کردن به مدت 5 دقیقه
#             cache.set(cache_key, attempts, self.lockout_time)
#         else:
#             cache.set(cache_key, attempts, 3600)  # 1 ساعت
#
#     def _reset_failed_attempts(self, phone):
#         """بازنشانی شمارنده تلاش‌های ناموفق"""
#         cache_key = f"login_attempts_{phone}"
#         cache.delete(cache_key)
# در ابتدای متد post


# بعد از authenticate


# بعد از login


class LoginView(View):
    template_name = 'accounts/login.html'
    max_login_attempts = 5
    lockout_time = 300

    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, 'شما قبلا وارد سیستم شده‌اید.')
            return redirect('pages:home')

        # بررسی اگر کاربر از قبل لاگین کرده اما verify نشده
        if 'unverified_phone' in request.session:
            return redirect('accounts:verify_otp')

        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)

        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
            return render(request, self.template_name, {'form': form})

        try:
            return self._process_login(request, form)
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            messages.error(request, 'خطایی در ورود به سیستم رخ داده است.')
            return render(request, self.template_name, {'form': form})

    def _process_login(self, request, form):
        phone = form.cleaned_data['phone']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)
        logger.info(f"Login attempt - Phone: {phone}, REMOTE_ADDR: {request.META.get('REMOTE_ADDR')}")

        # استانداردسازی شماره تلفن
        try:
            db_phone = PhoneService.standardize_phone(phone, 'database')
        except ValidationError:
            messages.error(request, 'شماره تلفن معتبر نیست.')
            return render(request, self.template_name, {'form': form})

        # بررسی وجود کاربر
        User = get_user_model()
        try:
            user = User.objects.get(phone=db_phone)

            # بررسی فعال بودن حساب
            if not user.is_active:
                messages.error(request, 'حساب کاربری شما غیرفعال است.')
                return render(request, self.template_name, {'form': form})

            # بررسی تأیید شماره تلفن
            if not user.is_phone_verified:
                request.session['unverified_phone'] = db_phone
                request.session['login_attempt_user_id'] = user.id
                messages.info(request, 'لطفا ابتدا شماره تلفن خود را تأیید کنید.')
                return redirect('accounts:verify_otp')

        except User.DoesNotExist:
            messages.error(request, 'شماره تلفن یا رمز عبور اشتباه است.')
            return render(request, self.template_name, {'form': form})

        # احراز هویت
        user = authenticate(request, username=db_phone, password=password)
        logger.info(f"Authenticate result: {user}")

        if user is not None:
            if user.is_active and user.is_phone_verified:
                login(request, user)
                logger.info(f"Login successful - User ID: {user.id}, Session: {request.session.session_key}")

                # تنظیم مدت زمان session
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

                # پاک کردن sessionهای مربوط به لاگین
                if 'unverified_phone' in request.session:
                    del request.session['unverified_phone']
                if 'login_attempt_user_id' in request.session:
                    del request.session['login_attempt_user_id']

                # هدایت به صفحه مناسب
                next_url = request.GET.get('next', 'pages:home')
                return redirect(next_url)
            else:
                messages.error(request, 'حساب کاربری شما غیرفعال یا تأیید نشده است.')
                return render(request, self.template_name, {'form': form})
        else:
            messages.error(request, 'شماره تلفن یا رمز عبور اشتباه است.')
            return render(request, self.template_name, {'form': form})


@login_required
def profile_edit(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # اگر پروفایل وجود نداشت، ایجاد می‌کنیم
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        # ارسال user به فرم برای اعتبارسنجی
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'لطفاً خطاهای زیر را اصلاح کنید.')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'page_title': 'ویرایش پروفایل',
        'profile': profile
    })

#
# @login_required
# def profile_edit(request):
#     profile = request.user.profile
#
#     if request.method == 'POST':
#         form = ProfileEditForm(request.POST, instance=profile, user=request.user)
#         if form.is_valid():
#             form.save()
#             return redirect('accounts:profile')
#     else:
#         form = ProfileEditForm(instance=profile, user=request.user)
#
#     return render(request, 'accounts/profile_edit.html', {
#         'form': form,
#         'page_title': 'ویرایش پروفایل'
#     })
#
# @login_required
# def profile_view(request):
#     try:
#         profile = request.user.profile
#     except UserProfile.DoesNotExist:
#         # اگر پروفایل وجود نداشت، یک پروفایل خالی ایجاد می‌کنیم
#         profile = UserProfile.objects.create(user=request.user)
#
#     # دریافت سفارشات کاربر
#     orders = Order.objects.filter(User=request.user).order_by('-created_at')
#
#     # صفحه‌بندی سفارشات
#     paginator = Paginator(orders, 10)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#
#     # محاسبه آمار خرید
#     total_orders = orders.count()
#     completed_orders = orders.filter(status='delivered').count()
#     total_spent = orders.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
#     avg_order_value = orders.filter(status='delivered').aggregate(Avg('total_amount'))['total_amount__avg'] or 0
#
#     # 5 سفارش اخیر برای تب خلاصه
#     recent_orders = orders[:5]
#
#     context = {
#         'profile': profile,
#         'orders': page_obj,
#         'recent_orders': recent_orders,
#         'total_orders': total_orders,
#         'completed_orders': completed_orders,
#         'total_spent': total_spent,
#         'avg_order_value': avg_order_value,
#     }
#
#     return render(request, 'accounts/profile.html', context)


# class ProfileEditForm(forms.ModelForm):
#     class Meta:
#         model = UserProfile
#         fields = [
#             'first_name', 'last_name', 'birth_date', 'avatar',
#             'country', 'province', 'city', 'address', 'postal_code',
#             'email', 'emergency_contact', 'email_notifications', 'sms_notifications'
#         ]
#         widgets = {
#             'birth_date': forms.DateInput(attrs={'type': 'date'}),
#             'address': forms.Textarea(attrs={'rows': 3}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if email:
#             # بررسی یکتا بودن ایمیل (به جز برای کاربر فعلی)
#             if UserProfile.objects.exclude(user=self.user).filter(email=email).exists():
#                 raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
#         return email
# @login_required
# def profile_view(request):
#     profile = request.user.profile
#     orders = Order.objects.filter(user=request.user).order_by('-created_at')
#
#     # محاسبه آمار خرید
#     total_orders = orders.count()
#     completed_orders = orders.filter(status='delivered').count()
#     total_spent = orders.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
#     last_order = orders.first()
#     last_order_date = last_order.created_at if last_order else None
#
#     return render(request, 'accounts/profile.html', {
#         'profile': profile,
#         'orders': orders[:10],  # 10 سفارش آخر
#         'total_orders': total_orders,
#         'completed_orders': completed_orders,
#         'total_spent': total_spent,
#         'last_order_date': last_order_date
#     })
# @login_required
# def profile_view(request):
#     try:
#         profile = request.user.profile
#     except UserProfile.DoesNotExist:
#         profile = UserProfile.objects.create(user=request.user)
#
#     context = {
#         'profile': profile,
#         'user': request.user,
#         'phone': request.user.phone,
#         'is_phone_verified': request.user.is_phone_verified
#     }
#     return render(request, 'accounts/profile.html', context)
#
#
# class ProfileEditView(LoginRequiredMixin, UpdateView):
#     model = UserProfile
#     form_class = ProfileEditForm
#     template_name = 'accounts/profile_edit.html'
#     success_url = reverse_lazy('accounts:profile')
#
#     # برای جلوگیری از دسترسی کاربران به پروفایل دیگران
#     def dispatch(self, request, *args, **kwargs):
#         # بررسی اینکه کاربر فقط به پروفایل خودش دسترسی دارد
#         obj = self.get_object()
#         if obj.user != request.user:
#             raise PermissionDenied(_("شما اجازه دسترسی به این پروفایل را ندارید."))
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_object(self, queryset=None):
#         # ایجاد خودکار پروفایل اگر وجود نداشته باشد
#         obj, created = UserProfile.objects.get_or_create(user=self.request.user)
#         if created:
#             # اگر پروفایل تازه ایجاد شده، لاگ مناسب ثبت شود
#             logger.info(f"New profile created for user: {self.request.user.phone}")
#         return obj
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         # ارسال کاربر به فرم برای اعتبارسنجی‌های پیشرفته
#         kwargs['user'] = self.request.user
#         return kwargs
#
#     @transaction.atomic
#     def form_valid(self, form):
#         # ذخیره‌سازی در تراکنش اتمی برای جلوگیری از ناسازگاری داده‌ها
#         response = super().form_valid(form)
#
#         # ثبت لاگ تغییرات
#         self._log_profile_changes(form)
#
#         # ارسال پیام موفقیت
#         messages.success(
#             self.request,
#             _('پروفایل شما با موفقیت به‌روزرسانی شد.'),
#             extra_tags='success'
#         )
#
#         return response
#
#     def form_invalid(self, form):
#         # ارسال پیام خطا با جزئیات
#         error_count = len(form.errors)
#         messages.error(
#             self.request,
#             _('لطفاً {} خطای زیر را اصلاح کنید.').format(error_count),
#             extra_tags='danger'
#         )
#         return super().form_invalid(form)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # افزودن اطلاعات اضافی به context
#         context['page_title'] = _('ویرایش پروفایل')
#         context['active_tab'] = 'profile'
#         return context
#
#     def _log_profile_changes(self, form):
#         """ثبت تغییرات انجام شده در پروفایل"""
#         changed_fields = []
#         for field in form.changed_data:
#             # جلوگیری از لاگ کردن فیلدهای حساس
#             if field not in ['avatar', 'password']:
#                 changed_fields.append(field)
#
#         if changed_fields:
#             logger.info(
#                 f"User {self.request.user.phone} updated profile fields: {', '.join(changed_fields)}"
#             )