#!/usr/bin/env python
"""
اسکریپت اجرای تست‌های جامع
"""

import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# افزودن مسیر پروژه به sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """اجرای تمام تست‌ها"""
    os.environ['DJANGO_SETTINGS_MODULE'] = 'your_project.settings'
    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(
        verbosity=2,
        interactive=True,
        failfast=False
    )

    # اجرای تست‌ها
    failures = test_runner.run_tests([
        'accounts.tests.test_models',
        'accounts.tests.test_services',
        'accounts.tests.test_views',
        'accounts.tests.test_integration',
    ])

    return failures


if __name__ == '__main__':
    failures = run_tests()
    sys.exit(bool(failures))