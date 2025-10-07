import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# در فایل validators.py
from phonenumbers import parse, is_valid_number, NumberParseException, format_number
def validate_iranian_mobile(value, return_format='database'):
    """
    اعتبارسنجی شماره موبایل ایرانی و بازگرداندن در فرمت‌های مختلف
    return_format: 'standard' (0xxxxxxxxxx), 'international' (+98xxxxxxxxxx), 'database' (xxxxxxxxxx)
    """
    if not value:
        raise ValidationError('لطفاً شماره موبایل را وارد کنید')

    try:
        # تبدیل اعداد فارسی/عربی به انگلیسی
        persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
        arabic_numbers = '٠١٢٣٤٥٦٧٨٩'
        english_numbers = '0123456789'

        # ایجاد جداول ترجمه
        persian_trans = str.maketrans(persian_numbers, english_numbers)
        arabic_trans = str.maketrans(arabic_numbers, english_numbers)

        # اعمال ترجمه
        value = str(value).translate(persian_trans).translate(arabic_trans)

        # حذف کاراکترهای غیرعددی به جز +
        cleaned = re.sub(r'[^\d+]', '', value)

        # اگر رشته خالی شد
        if not cleaned:
            raise ValidationError('شماره موبایل معتبر نیست')

        # افزودن پیشوند +98 اگر با 0 شروع شده
        if cleaned.startswith('0'):
            international_format = '+98' + cleaned[1:]
        elif cleaned.startswith('98'):
            international_format = '+' + cleaned
        elif not cleaned.startswith('+98'):
            # اگر نه با صفر شروع شده نه با ۹۸ و نه +۹۸
            # اما طول 10 رقم دارد و با 9 شروع می‌شود
            if len(cleaned) == 10 and cleaned.startswith('9'):
                international_format = '+98' + cleaned
            else:
                raise ValidationError('فرمت شماره موبایل صحیح نیست')

        # اعتبارسنجی با phonenumbers
        parsed = parse(international_format, None)
        if not is_valid_number(parsed) or parsed.country_code != 98:
            raise ValidationError('شماره موبایل معتبر نیست')

        # بررسی ساختار ایرانی
        national_num = str(parsed.national_number)
        if not national_num.startswith('9') or len(national_num) != 10:
            raise ValidationError('فرمت شماره موبایل ایرانی صحیح نیست')

        # بازگرداندن شماره در فرمت مورد نظر
        if return_format == 'international':
            return international_format
        elif return_format == 'standard':
            return '0' + national_num  # 0xxxxxxxxxx
        else:
            return national_num  # xxxxxxxxxx

    except NumberParseException as e:
        raise ValidationError(f'خطا در فرمت شماره: {str(e)}')