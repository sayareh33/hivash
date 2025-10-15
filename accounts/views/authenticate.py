import logging
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core import signing
from django.core.signing import BadSignature
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View
from django.utils.translation import gettext_lazy as _

from config.settings import OTP_MAX_ATTEMPTS
from ..forms import SignUpForm, ResendOTPForm
from ..services.otp_service import send_sms_via_asanak, OTPService

logger = logging.getLogger(__name__)

User = get_user_model()

# ---------------- ویو ثبت‌نام اصلاح شده -----------------
class SignUpView(View):
    template_name = 'accounts/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, _("شما قبلاً وارد شده‌اید."))
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': SignUpForm()})

    def post(self, request):
        form = SignUpForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        phone = form.cleaned_data['phone']
        password = form.cleaned_data['password']
        email = form.cleaned_data.get('email', '')

        # بررسی وجود کاربر
        if User.objects.filter(phone=phone, is_active=True).exists():
            form.add_error('phone', _('این شماره تلفن قبلاً ثبت شده است.'))
            return render(request, self.template_name, {'form': form})

            # حذف کاربران موقت قبلی با همین شماره
        User.objects.filter(phone=phone, is_active=False).delete()

        # ایجاد کاربر موقت
        try:
            temp_user = User.objects.create_user(
                phone=phone,
                password=password,
                email=email,
                is_active=False,
                is_phone_verified=False
            )
        except Exception as e:
            logger.error(f"Failed to create temp user: {e}")
            form.add_error(None, _('خطا در ایجاد حساب کاربری.'))
            return render(request, self.template_name, {'form': form})

            # ارسال OTP
        try:
            temp_user.send_otp()
            logger.info(f"OTP sent successfully to {phone}")
            print(1)
        except Exception as e:
            logger.error(f"OTP send failed: {e}")
            temp_user.delete()
            form.add_error(None, _('ارسال کد تأیید با خطا مواجه شد.'))
            return render(request, self.template_name, {'form': form})

            # ذخیره در session
        request.session['pending_user_id'] = temp_user.id
        request.session.set_expiry(300)  # 5 دقیقه
        messages.success(request, _('کد تأیید ارسال شد. لطفاً آن را وارد کنید.'))
        return redirect('accounts:verify_otp')

    # ---------------- ویو تأیید OTP اصلاح شده -----------------
class VerifyOTPView(View):
    template_name = 'accounts/verify_otp.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, _("شما قبلاً وارد شده‌اید."))
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        if not request.session.get('pending_user_id'):
            messages.error(request, _("مدت اعتبار ثبت‌نام شما منقضی شده است. لطفا دوباره ثبت نام کنید."))
            return redirect("accounts:signup")
        return render(request, self.template_name)

    def post(self, request):
        input_code = (request.POST.get("otp_code") or "").strip()
        user_id = request.session.get('pending_user_id')

        if not user_id:
            messages.error(request, _("مدت اعتبار ثبت‌نام شما منقضی شده است. لطفا دوباره ثبت نام کنید."))
            return redirect("accounts:signup")

        if not input_code or len(input_code) != 6:
            messages.error(request, _("لطفاً کد تأیید ۶ رقمی را وارد کنید."))
            return redirect("accounts:verify_otp")

        try:
            user = User.objects.get(id=user_id, is_active=False)
        except User.DoesNotExist:
            messages.error(request, _("کاربر یافت نشد. لطفاً دوباره ثبت‌نام کنید."))
            request.session.pop('pending_user_id', None)
            return redirect("accounts:signup")

            # تأیید OTP
        ok, msg = user.verify_otp(input_code)
        if not ok:
            messages.error(request, msg)
            # اگر حساب قفل شد، session را پاک کن
            if user.is_locked:
                request.session.pop('pending_user_id', None)
                return redirect("accounts:signup")
            return redirect("accounts:verify_otp")

            # فعال کردن کاربر نهایی
        user.is_active = True
        user.save()

        # پاک‌سازی session و لاگین
        request.session.pop('pending_user_id', None)
        login(request, user)

        messages.success(request, _("ثبت‌نام با موفقیت انجام شد. خوش آمدید!"))
        return redirect("pages:home")

    def verify_otp(self, code):

        """تأیید OTP با مدیریت بهتر"""
        if self.is_locked:
            return False, _("حساب قفل شده است. لطفاً چند دقیقه دیگر تلاش کنید.")

        if not self.otp_code or not self.otp_created_at:
            return False, _("کد تأیید وجود ندارد یا منقضی شده است.")

        if self.is_otp_expired():
            return False, _("کد تأیید منقضی شده است.")

        # نرمال‌سازی کدها
        input_code = str(code).strip()
        stored_code = str(self.otp_code).strip()

        if input_code == stored_code:
            # تأیید موفق
            self.otp_code = None
            self.otp_created_at = None
            self.otp_attempts = 0
            self.is_phone_verified = True
            self.save(update_fields=[
                'otp_code', 'otp_created_at', 'otp_attempts', 'is_phone_verified'
            ])
            return True, _("تأیید موفق")
        else:
            # تأیید ناموفق
            self.otp_attempts += 1
            remaining_attempts = OTP_MAX_ATTEMPTS - self.otp_attempts

            if self.otp_attempts >= OTP_MAX_ATTEMPTS:
                self.lock_account()
                self.save()
                return False, _("کد تأیید نامعتبر است. حساب قفل شد.")
            else:
                self.save(update_fields=['otp_attempts'])
                return False, _(f"کد تأیید نامعتبر است. {remaining_attempts} تلاش باقی مانده.")


# def register(request):
#     phone = request.session.get("phone")
#     if not phone:
#         return redirect("request_phone")
#
#     if request.method == "POST":
#         name = request.POST["name"]
#         family = request.POST["family"]
#         password = request.POST["password"]
#
#         user = User.objects.get(phone=phone)
#         user.name = name
#         user.family = family
#         user.set_password(password)
#         user.save()
#
#         login(request, user)
#         return redirect("dashboard")
#     return render(request, "accounts/register.html")
#
# @login_required
# def dashboard(request):
#     return render(request, "accounts/dashboard.html")
#
#
# @login_required
# def edit_profile(request):
#     if request.method == "POST":
#         request.user.name = request.POST["name"]
#         request.user.family = request.POST["family"]
#         request.user.save()
#         messages.success(request, "اطلاعات شما با موفقیت ویرایش شد")
#         return redirect("dashboard")
#     return render(request, "accounts/edit_profile.html")
#
#
# @login_required
# def change_password(request):
#     if request.method == "POST":
#         current_password = request.POST['current_password']
#         new_password = request.POST['new_password']
#
#         if request.user.check_password(current_password):
#             request.user.set_password(new_password)
#             request.user.save()
#             messages.success(request, "رمز عبور شما با موفقیت ویرایش شد")
#             return redirect("dashboard")
#         messages.error(request, "رمز عبور شما اشتباه است")
#     return render(request, "accounts/change_password.html")


# def forgot_password(request):
#     if request.method == "POST":
#         phone = request.POST["phone"]
#         code = generate_code()
#
#         if not valid_phone(phone):
#             messages.error(request, "شماره تماس وارد شده معتبر نمی باشد")
#             return redirect("request_phone")
#
#         request.session["phone"] = phone
#         request.session["code"] = code
#
#         send_sms(phone, f"کد تایید برای تغییر رمز عبور : {code}")
#         return redirect("reset_password")
#     return render(request, "accounts/forgot_password.html")
#
#
# def reset_password(request):
#     if request.method == "POST":
#         input_code = request.POST["code"]
#         phone = request.session.get("phone")
#         courrect_code = request.session.get("code")
#         new_password = request.POST["new_password"]
#
#         if input_code == courrect_code:
#             user = User.objects.get(phone=phone)
#             user.set_password(new_password)
#             user.save()
#             messages.success(request, "رمز عبور با موفقیت بازگردانی شد")
#             return redirect("login")
#
#         messages.error(request, "کد تایید اشتباه است")
#     return render(request, "accounts/reset_password.html")





