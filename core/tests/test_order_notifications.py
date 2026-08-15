from decimal import Decimal

from django.core import mail
from django.test import TestCase

from core.models import Order


def make_order(**extra):
    fields = {
        'code': 'CS-TEST0001',
        'customer_name': 'Mariana Ribeiro',
        'email': 'mariana@example.com',
        'address': 'Av. das Americas, 15500',
        'city': 'Rio de Janeiro',
        'zip': '22790-701',
        'total': Decimal('99.00'),
    }
    fields.update(extra)
    return Order.objects.create(**fields)


class OrderStatusNotificationTests(TestCase):
    def test_no_email_sent_on_order_creation(self):
        make_order()

        self.assertEqual(len(mail.outbox), 0)

    def test_email_sent_when_status_changes_to_paid(self):
        order = make_order()
        mail.outbox.clear()

        order.status = 'pago'
        order.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('CS-TEST0001', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['mariana@example.com'])

    def test_no_email_sent_when_status_stays_the_same(self):
        order = make_order()
        mail.outbox.clear()

        order.total = Decimal('120.00')
        order.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_email_sent_when_status_changes_to_shipped(self):
        order = make_order(status='pago')
        mail.outbox.clear()

        order.status = 'enviado'
        order.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('enviado', mail.outbox[0].body)

    def test_pending_status_does_not_trigger_email(self):
        order = make_order(status='cancelado')
        mail.outbox.clear()

        order.status = 'pendente'
        order.save()

        self.assertEqual(len(mail.outbox), 0)
