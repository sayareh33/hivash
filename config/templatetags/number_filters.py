from django import template
from persiantools import digits

register = template.Library()

@register.filter(name='translate_number')
def translate_number(value):
    """
    فیلتر برای تبدیل اعداد انگلیسی به فارسی
    مثال:
        {{ 12345|translate_number }} => ۱۲۳۴۵
    """
    try:
        return digits.en_to_fa(str(value))
    except Exception:
        return value
