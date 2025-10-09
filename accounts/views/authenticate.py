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

from ..forms import SignUpForm, ResendOTPForm
from ..services.otp_service import send_sms_via_asanak, OTPService
import logging

logger = logging.getLogger(__name__)


User = get_user_model()


class SignUpView(View):
    template_name = 'accounts/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, _("You are already signed in."))
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Display signup form"""
        form = SignUpForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST or None)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        phone = form.cleaned_data['phone']
        password = form.cleaned_data['password']
        email = form.cleaned_data.get('email') or ""

        if User.objects.filter(phone=phone).exists():
            form.add_error('phone', _("An account with this phone number already exists."))
            return render(request, self.template_name, {'form': form})

        try:
            otp_code = f"{OTPService.generate_otp():06d}"
            OTPService.store_otp(phone, otp_code)
        except Exception:
            logger.exception("Failed to generate/store OTP for %s", phone)
            form.add_error(None, _("Could not generate verification code. Please try again later."))
            return render(request, self.template_name, {'form': form})

        password_hash = make_password(password)
        signed_payload = signing.dumps({
            'phone': phone,
            'password_hash': password_hash,
            'email': email,
        })

        request.session['pending_signup'] = signed_payload
        request.session.set_expiry(300)

        try:
            send_sms_via_asanak(phone, otp_code)
        except Exception:
            logger.exception("Failed to send OTP SMS for %s", phone)
            form.add_error(None, _("Failed to send verification SMS. Please try again later."))
            request.session.pop('pending_signup', None)
            return render(request, self.template_name, {'form': form})

        messages.success(request, _("Verification code sent. Please enter it."))
        return redirect("accounts:verify_otp")


class VerifyOTPView(View):
    template_name = 'accounts/verify_otp.html'

    def get(self, request):
        """Display signup form"""
        return render(request, self.template_name)

    def post(self, request):
        input_code = (request.POST.get("otp_code") or "").strip()
        signed_payload = request.session.get("pending_signup")

        if not signed_payload:
            messages.error(request, _("Invalid request. Please start the sign-up again."))
            return redirect("accounts:signup")

        if not input_code:
            messages.error(request, _("Please provide the verification code."))
            return redirect("accounts:verify_otp")

        try:
            pending_data = signing.loads(signed_payload)
        except BadSignature:
            messages.error(request, _("Sign-up data is invalid. Please try again."))
            request.session.pop("pending_signup", None)
            return redirect("accounts:signup")

        phone = pending_data.get("phone")
        password_hash = pending_data.get("password_hash")
        email = pending_data.get("email", "")

        if not all([phone, password_hash]):
            messages.error(request, _("Sign-up data is incomplete. Please try again."))
            request.session.pop("pending_signup", None)
            return redirect("accounts:signup")

        try:
            OTPService.verify_otp(phone, input_code)
        except ValidationError as exc:
            messages.error(request, exc.message)
            return redirect("accounts:verify_otp")
        except Exception:
            logger.exception("Failed OTP verification for %s", phone)
            messages.error(request, _("Error verifying the code. Please try again."))
            return redirect("accounts:verify_otp")

        if User.objects.filter(phone=phone).exists():
            request.session.pop("pending_signup", None)
            messages.info(request, _("This phone number is already registered."))
            return redirect("accounts:login")

        try:
            user = User.objects.create(
                phone=phone,
                email=email,
                password=password_hash,
                is_phone_verified=True,
            )
        except Exception:
            logger.exception("Failed to create user after OTP verification for %s", phone)
            messages.error(request, _("Could not create the account. Please try again later."))
            return redirect("accounts:signup")

        request.session.pop("pending_signup", None)
        messages.success(request, _("Sign-up completed successfully."))
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect("pages:home")


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
            messages.success(request, "Ø¨Ù‡ Ù‡ÛŒÙˆØ§ Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯.")
            return redirect("pages:home")

        messages.error(request, "Ø´Ù…Ø§Ø±Ù‡ ØªÙ…Ø§Ø³ ÛŒØ§ Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± ØµØ­ÛŒØ­ Ù†Ù…ÛŒ Ø¨Ø§Ø´Ø¯")
        return render(request, "accounts/login.html")

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
    """ÙˆÛŒÙˆ Ø­Ø±ÙÙ‡â€ŒØ§ÛŒ Ø¨Ø±Ø§ÛŒ Ù…Ø¯ÛŒØ±ÛŒØª Ø®Ø±ÙˆØ¬ Ú©Ø§Ø±Ø¨Ø±"""

    # Ø¢Ø¯Ø±Ø³ Ø±ÛŒØ¯Ø§ÛŒØ±Ú©Øª Ù¾Ø³ Ø§Ø² Ø®Ø±ÙˆØ¬
    next_page = reverse_lazy('pages:home')

    # ØºÛŒØ±ÙØ¹Ø§Ù„ Ú©Ø±Ø¯Ù† Ú©Ø´ Ø¨Ø±Ø§ÛŒ Ø§ÛŒÙ† ÙˆÛŒÙˆ
    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_next_page(self):
        """ØªØ¹ÛŒÛŒÙ† ØµÙØ­Ù‡ Ù…Ù‚ØµØ¯ Ù¾Ø³ Ø§Ø² Ø®Ø±ÙˆØ¬"""
        next_page = super().get_next_page()

        # Ø§Ú¯Ø± Ù¾Ø§Ø±Ø§Ù…ØªØ± next Ø¯Ø± URL ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø´ØªØŒ Ø§Ø² Ø¢Ù† Ø§Ø³ØªÙØ§Ø¯Ù‡ Ú©Ù†
        if self.request.GET.get('next'):
            return self.request.GET.get('next')

        return next_page

    def post(self, request, *args, **kwargs):
        """Ù…Ø¯ÛŒØ±ÛŒØª Ø¯Ø±Ø®ÙˆØ§Ø³Øª POST Ø¨Ø±Ø§ÛŒ Ø®Ø±ÙˆØ¬"""
        # Ø¯Ø±ÛŒØ§ÙØª Ù†Ø§Ù… Ú©Ø§Ø±Ø¨Ø± Ù‚Ø¨Ù„ Ø§Ø² Ø®Ø±ÙˆØ¬ Ø¨Ø±Ø§ÛŒ Ù†Ù…Ø§ÛŒØ´ Ø¯Ø± Ù¾ÛŒØ§Ù…
        username = request.user.username or request.user.phone

        # Ø§Ù†Ø¬Ø§Ù… Ø¹Ù…Ù„ÛŒØ§Øª Ø®Ø±ÙˆØ¬
        response = super().post(request, *args, **kwargs)

        # Ù†Ù…Ø§ÛŒØ´ Ù¾ÛŒØ§Ù… Ù…ÙˆÙÙ‚ÛŒØª
        messages.success(
            request,
            _('Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø§Ø² Ø³ÛŒØ³ØªÙ… Ø®Ø§Ø±Ø¬ Ø´Ø¯ÛŒØ¯. Ø¨Ø§Ø²Ú¯Ø´Øª Ø´Ù…Ø§ Ø±Ø§ Ù…Ù†ØªØ¸Ø±ÛŒÙ…!'),
            extra_tags='success'
        )

        # Ø«Ø¨Øª Ù„Ø§Ú¯ Ø®Ø±ÙˆØ¬
        logger.info(f"User {username} logged out successfully")

        return response

    def get(self, request, *args, **kwargs):
        """Ù…Ø¯ÛŒØ±ÛŒØª Ø¯Ø±Ø®ÙˆØ§Ø³Øª GET Ø¨Ø±Ø§ÛŒ Ø®Ø±ÙˆØ¬ (Ø¨Ø±Ø§ÛŒ Ù„ÛŒÙ†Ú© Ù…Ø³ØªÙ‚ÛŒÙ…)"""
        # Ø¯Ø± ØµÙˆØ±Øª Ø§Ø³ØªÙØ§Ø¯Ù‡ Ø§Ø² GET Ù†ÛŒØ² Ú©Ø§Ø±Ø¨Ø± Ø±Ø§ Ø®Ø§Ø±Ø¬ Ù…ÛŒâ€ŒÚ©Ù†ÛŒÙ…
        return self.post(request, *args, **kwargs)


class SimpleLogoutView(View):
    """ÙˆÛŒÙˆ Ø³Ø§Ø¯Ù‡ Ø¨Ø±Ø§ÛŒ Ø®Ø±ÙˆØ¬ Ú©Ø§Ø±Ø¨Ø±"""

    def get(self, request):
        """Ù…Ø¯ÛŒØ±ÛŒØª Ø¯Ø±Ø®ÙˆØ§Ø³Øª GET Ø¨Ø±Ø§ÛŒ Ø®Ø±ÙˆØ¬"""
        # Ø¨Ø±Ø±Ø³ÛŒ Ø§ÛŒÙ†Ú©Ù‡ Ú©Ø§Ø±Ø¨Ø± ÙˆØ§Ø±Ø¯ Ø³ÛŒØ³ØªÙ… Ø§Ø³Øª ÛŒØ§ Ù†Ù‡
        if not request.user.is_authenticated:
            messages.info(request, _('Ø´Ù…Ø§ Ù‚Ø¨Ù„Ø§ Ø§Ø² Ø³ÛŒØ³ØªÙ… Ø®Ø§Ø±Ø¬ Ø´Ø¯Ù‡â€ŒØ§ÛŒØ¯.'))
            return redirect('pages:home')

        # Ø¯Ø±ÛŒØ§ÙØª Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ú©Ø§Ø±Ø¨Ø± Ù‚Ø¨Ù„ Ø§Ø² Ø®Ø±ÙˆØ¬
        username = request.user.username or request.user.phone

        # Ø§Ù†Ø¬Ø§Ù… Ø¹Ù…Ù„ÛŒØ§Øª Ø®Ø±ÙˆØ¬
        logout(request)

        # Ù†Ù…Ø§ÛŒØ´ Ù¾ÛŒØ§Ù… Ù…ÙˆÙÙ‚ÛŒØª
        messages.success(
            request,
            _('Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø§Ø² Ø³ÛŒØ³ØªÙ… Ø®Ø§Ø±Ø¬ Ø´Ø¯ÛŒØ¯. Ø¨Ù‡ Ø§Ù…ÛŒØ¯ Ø¯ÛŒØ¯Ø§Ø± Ù…Ø¬Ø¯Ø¯!'),
            extra_tags='success'
        )

        # Ø«Ø¨Øª Ù„Ø§Ú¯ Ø®Ø±ÙˆØ¬
        logger.info(f"User {username} logged out successfully")

        return redirect('pages:home')


class TemplateLogoutView(LoginRequiredMixin, LogoutView):
    """ÙˆÛŒÙˆ Ø®Ø±ÙˆØ¬ Ø¨Ø§ ØªÙ…Ù¾Ù„ÛŒØª Ø§Ø®ØªØµØ§ØµÛŒ"""

    template_name = 'accounts/logout.html'
    next_page = reverse_lazy('pages:home')

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Ù…Ø¯ÛŒØ±ÛŒØª Ø¯Ø±Ø®ÙˆØ§Ø³Øª POST Ø¨Ø±Ø§ÛŒ Ø®Ø±ÙˆØ¬"""
        # Ø¯Ø±ÛŒØ§ÙØª Ù†Ø§Ù… Ú©Ø§Ø±Ø¨Ø± Ù‚Ø¨Ù„ Ø§Ø² Ø®Ø±ÙˆØ¬
        username = request.user.username or request.user.phone

        # Ø§Ù†Ø¬Ø§Ù… Ø¹Ù…Ù„ÛŒØ§Øª Ø®Ø±ÙˆØ¬
        response = super().post(request, *args, **kwargs)

        # Ù†Ù…Ø§ÛŒØ´ Ù¾ÛŒØ§Ù… Ù…ÙˆÙÙ‚ÛŒØª
        messages.success(
            request,
            _('Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø§Ø² Ø³ÛŒØ³ØªÙ… Ø®Ø§Ø±Ø¬ Ø´Ø¯ÛŒØ¯. Ø¨Ù‡ Ø§Ù…ÛŒØ¯ Ø¯ÛŒØ¯Ø§Ø± Ù…Ø¬Ø¯Ø¯!'),
            extra_tags='success'
        )

        # Ø«Ø¨Øª Ù„Ø§Ú¯ Ø®Ø±ÙˆØ¬
        logger.info(f"User {username} logged out successfully")

        return response
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
#         messages.success(request, "Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª ÙˆÛŒØ±Ø§ÛŒØ´ Ø´Ø¯")
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
#             messages.success(request, "Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª ÙˆÛŒØ±Ø§ÛŒØ´ Ø´Ø¯")
#             return redirect("dashboard")
#         messages.error(request, "Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø´Ù…Ø§ Ø§Ø´ØªØ¨Ø§Ù‡ Ø§Ø³Øª")
#     return render(request, "accounts/change_password.html")


# def forgot_password(request):
#     if request.method == "POST":
#         phone = request.POST["phone"]
#         code = generate_code()
#
#         if not valid_phone(phone):
#             messages.error(request, "Ø´Ù…Ø§Ø±Ù‡ ØªÙ…Ø§Ø³ ÙˆØ§Ø±Ø¯ Ø´Ø¯Ù‡ Ù…Ø¹ØªØ¨Ø± Ù†Ù…ÛŒ Ø¨Ø§Ø´Ø¯")
#             return redirect("request_phone")
#
#         request.session["phone"] = phone
#         request.session["code"] = code
#
#         send_sms(phone, f"Ú©Ø¯ ØªØ§ÛŒÛŒØ¯ Ø¨Ø±Ø§ÛŒ ØªØºÛŒÛŒØ± Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± : {code}")
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
#             messages.success(request, "Ø±Ù…Ø² Ø¹Ø¨ÙˆØ± Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø¨Ø§Ø²Ú¯Ø±Ø¯Ø§Ù†ÛŒ Ø´Ø¯")
#             return redirect("login")
#
#         messages.error(request, "Ú©Ø¯ ØªØ§ÛŒÛŒØ¯ Ø§Ø´ØªØ¨Ø§Ù‡ Ø§Ø³Øª")
#     return render(request, "accounts/reset_password.html")





