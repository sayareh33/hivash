import hashlib
from django.utils import timezone
from .models import Visit

def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        ip = xff.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class VisitLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            ip = get_client_ip(request) or ''
            # هش کردن آی‌پی با salt برای حریم خصوصی
            salt = 'your-secret-salt'  # از settings بخون
            ip_hash = hashlib.sha256((ip + salt).encode()).hexdigest() if ip else None

            Visit.objects.create(
                path=request.path,
                method=request.method,
                referer=request.META.get('HTTP_REFERER'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                ip_hash=ip_hash,
                session_key=getattr(request, 'session', None).session_key if hasattr(request, 'session') else None,
            )
        except Exception:
            pass

        return response


import hashlib
from .models import Visit
from django.utils.deprecation import MiddlewareMixin
from user_agents import parse

class VisitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = request.META.get('REMOTE_ADDR', '')
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        user_agent_str = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_str)

        Visit.objects.create(
            path=request.path,
            method=request.method,
            referer=request.META.get('HTTP_REFERER', ''),
            user_agent=user_agent_str,
            ip_hash=ip_hash,
            session_key=request.session.session_key,
            user=request.user if request.user.is_authenticated else None,
            device=user_agent.device.family,
            browser=user_agent.browser.family,
            country='',  # اگر می‌خوای GeoIP اضافه کن
            city=''
        )
