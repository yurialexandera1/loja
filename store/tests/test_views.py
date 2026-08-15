import json
from decimal import Decimal
from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse

from core.models import Category, Order, Product, ReferralCode
from store.checkout_service import OutOfStock


def make_product(name='Cabo Turbo CB-105', stock=5, price='99.00'):
    category, _ = Category.objects.get_or_create(
        slug='cabos', defaults={'name': 'Cabos', 'icon': 'cable'}
    )
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        price=Decimal(price),
        stock=stock,
        category=category,
    )


CHECKOUT_POST = {
    'customer_name': 'Mariana Ribeiro',
    'email': 'mariana@example.com',
    'phone': '21988124407',
    'address': 'Av. das Americas, 15500',
    'city': 'Rio de Janeiro',
    'zip': '22790-701',
    'shipping_option': 'padrao',
}


class CheckoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _put_in_cart(self, product, qty):
        self.client.cookies['cart'] = json.dumps({str(product.id): qty})

    def test_places_order_and_empties_cart_when_stock_is_available(self):
        product = make_product(stock=5)
        self._put_in_cart(product, 2)

        response = self.client.post(reverse('store:checkout'), CHECKOUT_POST)

        order = Order.objects.get()
        self.assertRedirects(response, reverse('store:pedido', args=[order.code]))
        product.refresh_from_db()
        self.assertEqual(product.stock, 3)

    def test_reduces_quantity_to_stock_when_stock_dropped_since_adding(self):
        product = make_product(stock=5)
        self._put_in_cart(product, 2)
        Product.objects.filter(id=product.id).update(stock=1)

        self.client.post(reverse('store:checkout'), CHECKOUT_POST)

        item = Order.objects.get().items.get()
        self.assertEqual(item.qty, 1)
        product.refresh_from_db()
        self.assertEqual(product.stock, 0)

    def test_shows_message_instead_of_crashing_when_another_buyer_took_the_last_unit(self):
        product = make_product(stock=5)
        self._put_in_cart(product, 2)
        raise_out_of_stock = mock.Mock(
            side_effect=OutOfStock(product.name, requested=2, available=1)
        )

        with mock.patch('store.views.create_order', raise_out_of_stock):
            response = self.client.post(reverse('store:checkout'), CHECKOUT_POST)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Restam apenas 1 unidades')
        self.assertEqual(Order.objects.count(), 0)

    def test_redirects_to_cart_when_cart_is_empty(self):
        response = self.client.get(reverse('store:checkout'))

        self.assertRedirects(response, reverse('store:carrinho'))

    def test_add_to_cart_never_stores_more_than_stock(self):
        product = make_product(stock=3)

        self.client.post(reverse('store:add_cart', args=[product.slug]), {'qty': '99'})

        cart = json.loads(self.client.cookies['cart'].value)
        self.assertEqual(cart[str(product.id)], 3)


class ReferralCheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _put_in_cart(self, product, qty):
        self.client.cookies['cart'] = json.dumps({str(product.id): qty})

    def test_visiting_product_with_ref_sets_cookie(self):
        product = make_product()
        referral = ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')

        self.client.get(reverse('store:produto', args=[product.slug]), {'ref': referral.code})

        self.assertEqual(self.client.cookies['ref'].value, referral.code)

    def test_invalid_ref_code_is_not_stored(self):
        product = make_product()

        self.client.get(reverse('store:produto', args=[product.slug]), {'ref': 'NAOEXISTE'})

        self.assertNotIn('ref', self.client.cookies)

    def test_checkout_applies_referral_discount_from_cookie(self):
        product = make_product(price='200.00', stock=5)
        referral = ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')
        self._put_in_cart(product, 1)
        self.client.cookies['ref'] = referral.code

        self.client.post(reverse('store:checkout'), CHECKOUT_POST)

        order = Order.objects.get()
        self.assertEqual(order.discount, Decimal('20.00'))
        referral.refresh_from_db()
        self.assertEqual(referral.uses, 1)


class CheckoutApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _payload(self, product, qty):
        return {**CHECKOUT_POST, 'items': [{'id': product.id, 'qty': qty}]}

    def test_returns_201_and_order_code_on_success(self):
        product = make_product(stock=5)

        response = self.client.post(
            '/api/checkout/',
            data=json.dumps(self._payload(product, 2)),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['code'], Order.objects.get().code)

    def test_returns_409_when_stock_is_insufficient(self):
        product = make_product(stock=1)

        response = self.client.post(
            '/api/checkout/',
            data=json.dumps(self._payload(product, 4)),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body['error'], 'estoque_insuficiente')
        self.assertEqual(body['disponivel'], 1)
        self.assertEqual(Order.objects.count(), 0)
