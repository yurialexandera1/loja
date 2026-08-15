from decimal import Decimal
from urllib.parse import unquote

from django.test import TestCase

from core.models import Order, OrderItem
from store.whatsapp import order_message, whatsapp_url


def make_order(**extra):
    fields = {
        'code': 'CS-TEST0001',
        'customer_name': 'Mariana Ribeiro',
        'email': 'mariana@example.com',
        'phone': '21988124407',
        'address': 'Av. das Americas, 15500',
        'city': 'Rio de Janeiro',
        'zip': '22790-701',
        'shipping_option': 'padrao',
        'total': Decimal('213.00'),
    }
    fields.update(extra)
    order = Order.objects.create(**fields)
    OrderItem.objects.create(
        order=order,
        product_name='Cabo Turbo CB-105',
        sku='1002347',
        price=Decimal('99.00'),
        qty=2,
    )
    return order


class OrderMessageTests(TestCase):
    def test_message_opens_with_the_order_code(self):
        message = order_message(make_order())

        self.assertTrue(message.startswith('*PEDIDO CS-TEST0001*'))

    def test_message_lists_item_with_quantity_sku_and_subtotal(self):
        message = order_message(make_order())

        self.assertIn('2x Cabo Turbo CB-105 · cod. 1002347', message)
        self.assertIn('R$ 198.00', message)

    def test_message_shows_total_and_shipping_label(self):
        message = order_message(make_order())

        self.assertIn('*TOTAL: R$ 213.00*', message)
        self.assertIn('Padrao (5 a 8 dias)', message)

    def test_message_omits_sku_when_product_has_none(self):
        order = make_order()
        order.items.update(sku='')

        self.assertNotIn('cod.', order_message(order))

    def test_message_omits_contact_line_without_phone(self):
        order = make_order(phone='')

        self.assertNotIn('Contato:', order_message(order))


class WhatsappUrlTests(TestCase):
    def test_url_points_to_the_store_number(self):
        url = whatsapp_url(make_order())

        self.assertTrue(url.startswith('https://wa.me/5521995095642?text='))

    def test_message_survives_url_encoding(self):
        order = make_order()

        decoded = unquote(whatsapp_url(order).split('?text=', 1)[1])

        self.assertEqual(decoded, order_message(order))

    def test_accepts_a_different_number(self):
        url = whatsapp_url(make_order(), number='5511999999999')

        self.assertIn('wa.me/5511999999999', url)
