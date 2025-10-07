from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.utils.translation import gettext_lazy as _

from ..forms import SignUpForm, ResendOTPForm
from ..services.otp_service import send_sms_via_asanak
from ..validators import validate_iranian_mobile
import logging

logger = logging.getLogger(__name__)


User = get_user_model()


class SignUpView(View):
    template_name = 'accounts/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'شما قبلاً وارد سیستم شده‌اید.')
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Display signup form"""
        form = SignUpForm()
        return render(request, self.template_name)

    def post(self, request):
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        email = request.POST.get("email")
        # terms_accepted = request.POST.get("terms_accepted")

        # بررسی وجود فیلدهای ضروری
        if not all([phone, password, confirm_password]):
            messages.error(request, "لطفا تمام فیلدهای ضروری را پر کنید")
            return render(request, self.template_name)

        if not validate_iranian_mobile(phone):
            messages.error(request, "شماره تماس وارد شده معتبر نمی باشد")
            return render(request, self.template_name)

            # اعتبارسنجی‌های اضافی
        if password != confirm_password:
            messages.error(request, "رمز عبور و تکرار آن مطابقت ندارند")
            return render(request, self.template_name)

        if len(password) < 8:
            messages.error(request, "رمز عبور باید حداقل ۸ کاراکتر باشد")
            return render(request, self.template_name)

            # بررسی وجود کاربر با این شماره
        if User.objects.filter(phone=phone).exists():
            messages.error(request, "این شماره تماس قبلا ثبت شده است")
            return render(request, self.template_name)
        temp_user = User(phone=phone)  # ایجاد یک نمونه موقت

        try:
            # فراخوانی متد generate_otp از طریق instance
            otp_code = temp_user.generate_otp()
            print(f"OTP Code for {phone}: {otp_code}")
        except Exception as e:
            print(f"Error generating OTP: {e}")
            messages.error(request, "خطا در تولید کد تایید")
            return render(request, self.template_name)

        phone = request.session.get("phone")
        password = request.session.get("password")
        email = request.session.get("email")
        otp_code = request.session.get("otp_code")

        # تنظیم timeout برای session (مثلاً 10 دقیقه)
        request.session.set_expiry(300)

        # ارسال SMS
        try:
            send_sms_via_asanak(phone, f"کد تایید شما : {otp_code} به هیوا خوش آمدید")
            print("SMS sent successfully")
        except Exception as e:
            print(f"SMS sending failed: {e}")
            messages.error(request, "خطا در ارسال SMS. لطفا مجدداً تلاش کنید.")
            return render(request, self.template_name)

        messages.success(request, "کد تایید برای شما ارسال شد")
        return redirect("accounts:verify_otp")


class VerifyOTPView(View):
    template_name = 'accounts/verify_otp.html'

    def get(self, request):
        """Display signup form"""
        return render(request, self.template_name)

    def post(self, request):
        input_code = request.POST.get("otp_code")
        phone = request.session.get("phone")
        password = request.session.get("password")
        email = request.session.get("email")
        correct_code = request.session.get("otp_code")

        if not all([phone, password, correct_code, input_code]):
            messages.error(request, _("لطفا کد تایید را وارد کنید"))
            return redirect(request, "accounts:verify_otp")

        if input_code == correct_code:
            try:
                # ایجاد کاربر جدید با استفاده از create_user برای هش خودکار پسورد
                user = User.objects.create_user( phone=phone,password=password,
                    email=email if email else "" )

                # پاک کردن داده‌های موقت session

                # پاک کردن session با روش ایمن
                session_keys = ["phone", "password", "email", "otp_code"]
                for key in session_keys:
                    request.session.pop(key, None)

                messages.success(request, "به هیوا خوش آمدید.")
                return redirect("pages:home")

            except Exception as e:
                print(f"Error creating user: {e}")
                messages.error(request, "خطا در ایجاد حساب کاربری")
                return render(request, "template_name")
        else:
            messages.error(request, "کد تایید وارد شده اشتباه است")
            return render(request, "template_name")


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        phone = request.POST["phone"]
        password = request.POST["password"]

        user = authenticate(request, phone=phone, password=password)

        if user:
            login(request, user)
            messages.success(request, "به هیوا خوش آمدید.")
            return redirect("pages:home")

        messages.error(request, "شماره تماس یا رمز عبور صحیح نمی باشد")
        return render(request, "accounts/login.html")

class ResendOTPView(View):
    """
    ویو ارسال مجدد OTP
    """
    template_name = 'accounts/resend_otp.html'

    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, 'شما قبلا وارد سیستم شده‌اید.')
            return redirect('pages:home')

        # بررسی اینکه کاربر از فرآیند ثبت‌نام آمده است
        if 'phone' not in request.session or 'password' not in request.session:
            messages.error(request, 'لطفا ابتدا ثبت‌نام کنید.')
            return redirect('accounts:signup')

        form = ResendOTPForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        try:
            phone = request.session.get('phone')
            password = request.session.get('password')

            if not phone or not password:
                messages.error(request, _('لطفا ابتدا ثبت‌نام کنید.'))
                return redirect('accounts:signup')

            user = get_object_or_404(User, password=password, phone=phone)

            # بررسی امکان ارسال مجدد
            if not user.can_resend_otp():
                messages.error(request, _('لطفا کمی صبر کنید قبل از درخواست کد جدید.'))
                return redirect('accounts:signup')

            # ارسال مجدد OTP
            otp_code = user.generate_otp()
            success, message = send_sms_via_asanak(phone, otp_code)

            if success:
                messages.error(request, _('کد تأیید جدید ارسال شد.'))
                return redirect('accounts:verify_otp')

            else:
                messages.error(request, _('خطا در ارسال کد تأیید.'))
                return redirect('accounts:signup')



        except Exception as e:
            logger.error(f"Error in resend OTP: {str(e)}")
            messages.error(request, _('خطای داخلی سرور.'))
            return redirect('accounts:signup')


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