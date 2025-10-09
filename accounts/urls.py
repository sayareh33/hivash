from django.urls import path
from accounts.views.authenticate import SignUpView, LoginView, VerifyOTPView, ResendOTPView, CustomLogoutView
from accounts.views.profile import profile_view

app_name = 'accounts'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify_otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),

    # path('auth-status/', auth_status, name='auth_status'),
    # # ویوهای لاگین و بازیابی رمز عبور
    # path('login/', LoginView.as_view(), name='login'),
    # path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    # path('reset-password-verify/', ResetPasswordVerifyView.as_view(), name='reset_password_verify'),
    # path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    # # یا
    # path('logout/', SimpleLogoutView.as_view(), name='logout'),
    #
    # # path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    # # path('verify-signup/', VerifySignupView.as_view(), name='verify_signup'),
    #
    # # احراز هویت
    #
    # # OTP
    # path('send-otp/', send_otp_view, name='send_otp'),
    #
    # # رمز عبور
    # path('password/change/', password_change_view, name='password_change'),
    # path('password/reset/', password_reset_view, name='password_reset'),
    # path('password/reset/confirm/', password_reset_confirm_view, name='password_reset_confirm'),

    path('profile/', profile_view, name='profile'),
    # path('profile/edit/', profile_edit, name='profile_edit'),
    #
    # # ایمیل
    # path('email/', email_management_view, name='email_management'),

    # path('email/verification-sent/', email_verification_sent_view, name='email_verification_sent'),
    # path('email/confirm/<uidb64>/<token>/', email_confirm_view, name='email_confirm'),
]