from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import logger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.core import signing
from django.core.signing import BadSignature
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

from accounts.forms import ResendOTPForm, LoginForm
from accounts.services.otp_service import OTPService, send_sms_via_asanak
from django.utils.translation import gettext_lazy as _

class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, _("You are already signed in."))
            return redirect("pages:home")
        form = LoginForm()
        return render(request, self.template_name)

    def post(self, request):
        form = LoginForm(request.POST)
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()

        if not phone or not password:
            messages.error(request, _("Please fill in all fields."))
            return render(request, self.template_name)
        if form.is_valid():
            phone = form.cleaned_data['phone']  # شماره نرمال‌سازی شده
            password = form.cleaned_data['password']
        user = authenticate(request, phone=phone, password=password)

        if user:
            if not user.is_active:
                messages.error(request, _("Your account is deactivated."))
                return render(request, self.template_name, {'form': form})

            login(request, user)
            messages.success(request, _("به هیوا خوش آمدید."))
            return redirect("pages:home")

        messages.error(request, _("شماره تلفن یا رمز عبور صحیح نیست."))
        return render(request, self.template_name, {'form': form})
class ResendOTPView(View):
    """Allow users to request another OTP during sign-up."""
    template_name = 'accounts/resend_otp.html'

    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, _("You are already signed in."))
            return redirect('pages:home')

        if 'pending_signup' not in request.session:
            messages.error(request, _("No pending sign-up was found. Please start again."))
            return redirect('accounts:signup')

        form = ResendOTPForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        signed_payload = request.session.get('pending_signup')
        if not signed_payload:
            messages.error(request, _("No pending sign-up was found. Please start again."))
            return redirect('accounts:signup')

        try:
            pending_data = signing.loads(signed_payload)
        except BadSignature:
            messages.error(request, _("Sign-up data is invalid. Please try again."))
            request.session.pop('pending_signup', None)
            return redirect('accounts:signup')

        phone = pending_data.get('phone')
        if not phone:
            messages.error(request, _("Sign-up data is incomplete. Please try again."))
            request.session.pop('pending_signup', None)
            return redirect('accounts:signup')

        try:
            otp_code = f"{OTPService.generate_otp():06d}"
            OTPService.store_otp(phone, otp_code)
            send_sms_via_asanak(phone, otp_code)
        except Exception:
            logger.exception("Failed to resend OTP for %s", phone)
            messages.error(request, _("Could not resend the verification code. Please try again later."))
            return redirect('accounts:verify_otp')

        messages.success(request, _("A new verification code was sent."))
        return redirect('accounts:verify_otp')


class CustomLogoutView(LoginRequiredMixin, LogoutView):
    """ویو حرفه‌ای برای مدیریت خروج کاربر"""

    # آدرس ریدایرکت پس از خروج
    next_page = reverse_lazy('pages:home')

    # غیرفعال کردن کش برای این ویو
    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_next_page(self):
        """تعیین صفحه مقصد پس از خروج"""
        next_page = super().get_next_page()

        # اگر پارامتر next در URL وجود داشت، از آن استفاده کن
        if self.request.GET.get('next'):
            return self.request.GET.get('next')

        return next_page

    def post(self, request, *args, **kwargs):
        """مدیریت درخواست POST برای خروج"""
        # دریافت نام کاربر قبل از خروج برای نمایش در پیام
        username = request.user.username or request.user.phone

        # انجام عملیات خروج
        response = super().post(request, *args, **kwargs)

        # نمایش پیام موفقیت
        messages.success(
            request,
            _('شما با موفقیت از سیستم خارج شدید. بازگشت شما را منتظریم!'),
            extra_tags='success'
        )

        # ثبت لاگ خروج
        logger.info(f"User {username} logged out successfully")

        return response

    def get(self, request, *args, **kwargs):
        """مدیریت درخواست GET برای خروج (برای لینک مستقیم)"""
        # در صورت استفاده از GET نیز کاربر را خارج می‌کنیم
        return self.post(request, *args, **kwargs)


class SimpleLogoutView(View):
    """ویو ساده برای خروج کاربر"""

    def get(self, request):
        """مدیریت درخواست GET برای خروج"""
        # بررسی اینکه کاربر وارد سیستم است یا نه
        if not request.user.is_authenticated:
            messages.info(request, _('شما قبلا از سیستم خارج شده‌اید.'))
            return redirect('pages:home')

        # دریافت اطلاعات کاربر قبل از خروج
        phone = request.user.phone

        # انجام عملیات خروج
        logout(request)

        # نمایش پیام موفقیت
        messages.success(
            request,
            _('شما با موفقیت از سیستم خارج شدید. به امید دیدار مجدد!'),
            extra_tags='success'
        )

        # ثبت لاگ خروج
        logger.info(f"User {phone} logged out successfully")

        return redirect('pages:home')


class TemplateLogoutView(LoginRequiredMixin, LogoutView):
    """ویو خروج با تمپلیت اختصاصی"""

    template_name = 'accounts/logout.html'
    next_page = reverse_lazy('pages:home')

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """مدیریت درخواست POST برای خروج"""
        # دریافت نام کاربر قبل از خروج
        username = request.user.username or request.user.phone

        # انجام عملیات خروج
        response = super().post(request, *args, **kwargs)

        # نمایش پیام موفقیت
        messages.success(
            request,
            _('شما با موفقیت از سیستم خارج شدید. به امید دیدار مجدد!'),
            extra_tags='success'
        )

        # ثبت لاگ خروج
        logger.info(f"User {username} logged out successfully")

        return response