from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings

from core.models import Order, OrderItem
from store.whatsapp_api import is_configured, send_order_confirmation


def make_order(**extra):
    fields = {
        'code': 'CS-TEST0001',
        'customer_name': 'Mariana Ribeiro',
        'email': 'mariana@example.com',
        'phone': '21988124407',
        'address': 'Av. das Americas, 15500',
        'city': 'Rio de Janeiro',
        'zip': '22790-701',
        'total': Decimal('99.00'),
    }
    fields.update(extra)
    order = Order.objects.create(**fields)
    OrderItem.objects.create(order=order, product_name='Cabo', price=Decimal('99.00'), qty=1)
    return order


class ConfigurationTests(TestCase):
    @override_settings(WHATSAPP_CLOUD_API_TOKEN='', WHATSAPP_CLOUD_PHONE_ID='')
    def test_not_configured_without_credentials(self):
        self.assertFalse(is_configured())

    @override_settings(WHATSAPP_CLOUD_API_TOKEN='token', WHATSAPP_CLOUD_PHONE_ID='123')
    def test_configured_with_both_credentials(self):
        self.assertTrue(is_configured())


class SendOrderConfirmationTests(TestCase):
    @override_settings(WHATSAPP_CLOUD_API_TOKEN='', WHATSAPP_CLOUD_PHONE_ID='')
    def test_does_nothing_without_credentials(self):
        order = make_order()

        with mock.patch('urllib.request.urlopen') as urlopen:
            result = send_order_confirmation(order)

        self.assertFalse(result)
        urlopen.assert_not_called()

    @override_settings(WHATSAPP_CLOUD_API_TOKEN='token', WHATSAPP_CLOUD_PHONE_ID='123')
    def test_does_nothing_without_a_phone_number(self):
        order = make_order(phone='')

        with mock.patch('urllib.request.urlopen') as urlopen:
            result = send_order_confirmation(order)

        self.assertFalse(result)
        urlopen.assert_not_called()

    @override_settings(WHATSAPP_CLOUD_API_TOKEN='token', WHATSAPP_CLOUD_PHONE_ID='123')
    def test_sends_and_returns_true_on_success(self):
        order = make_order()

        with mock.patch('urllib.request.urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value = mock.Mock()
            result = send_order_confirmation(order)

        self.assertTrue(result)
        urlopen.assert_called_once()

    @override_settings(WHATSAPP_CLOUD_API_TOKEN='token', WHATSAPP_CLOUD_PHONE_ID='123')
    def test_returns_false_instead_of_raising_on_network_failure(self):
        import urllib.error

        order = make_order()

        with mock.patch('urllib.request.urlopen', side_effect=urllib.error.URLError('boom')):
            result = send_order_confirmation(order)

        self.assertFalse(result)
