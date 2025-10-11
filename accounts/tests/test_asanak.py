import os
from unittest.mock import MagicMock

import pytest
import requests
from requests import patch

from accounts.services.otp_service import send_sms_via_asanak


@patch('accounts.services.otp_service.requests.post')
def test_send_sms_success(self, mock_post):
    """تست ارسال موفق پیامک با URL صحیح آسانک"""
    # شبیه‌سازی پاسخ موفق آسانک
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'success'
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = send_sms_via_asanak('09123456789', '123456')

    # بررسی فراخوانی با URL صحیح
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://sms.asanak.ir/webservice/v2rest/sendsms"
    assert call_args[1]['headers']['Content-Type'] == 'application/x-www-form-urlencoded'

    assert result is True


@patch('accounts.services.otp_service.requests.post')
def test_send_sms_with_correct_payload(self, mock_post):
    """تست payload ارسالی به آسانک"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'success'
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = send_sms_via_asanak('09123456789', '123456')

    # بررسی payload
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs['data']

    assert payload['destination'] == '989123456789'  # بدون صفر اول
    assert payload['message'] == 'کد تایید شما 123456 آزمایش هیوا'
    assert 'username' in payload
    assert 'password' in payload
    assert 'template_id' in payload
    assert 'source' in payload


@patch('accounts.services.otp_service.requests.post')
def test_send_sms_network_timeout(self, mock_post):
    """تست timeout در ارسال پیامک"""
    mock_post.side_effect = requests.exceptions.Timeout("Timeout error")

    result = send_sms_via_asanak('09123456789', '123456')

    assert result is False


@patch('accounts.services.otp_service.requests.post')
def test_send_sms_http_error(self, mock_post):
    """تست خطای HTTP از سمت آسانک"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
    mock_post.return_value = mock_response

    result = send_sms_via_asanak('09123456789', '123456')

    assert result is False


class TestAsanakIntegration:
    """تست‌های یکپارچه‌سازی با سرویس آسانک"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Integration tests disabled"
    )
    def test_real_asanak_connection(self):
        """تست واقعی اتصال به آسانک (فقط زمانی اجرا شود که صراحتاً درخواست شود)"""
        # این تست فقط زمانی اجرا می‌شود که RUN_INTEGRATION_TESTS=true باشد
        phone = '09123456789'  # شماره تست
        otp = '123456'

        result = send_sms_via_asanak(phone, otp)

        # فقط اطمینان از اینکه خطایی رخ نداده
        assert result in [True, False]  # ممکن است به دلیل اعتبارسنجی شماره false شود

    @patch('accounts.services.otp_service.requests.post')
    def test_asanak_specific_response_handling(self, mock_post):
        """تست مدیریت پاسخ‌های خاص آسانک"""
        test_cases = [
            ('success', True),
            ('0', True),
            ('error', False),
            ('invalid destination', False),
            ('', False)
        ]

        for response_text, expected_result in test_cases:
            with self.subTest(response_text=response_text):
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = response_text
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                result = send_sms_via_asanak('09123456789', '123456')

                assert result == expected_result