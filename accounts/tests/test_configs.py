import pytest
from django.conf import settings
from django.test.utils import setup_test_environment, teardown_test_environment


def pytest_configure():
    """پیکربندی pytest برای پروژه جنگو"""
    setup_test_environment()

    # تنظیمات تست
    settings.DEBUG = False
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }


def pytest_unconfigure():
    """تمیزکاری پس از اجرای تست‌ها"""
    teardown_test_environment()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """دسترسی به دیتابیس برای تمام تست‌ها"""
    pass