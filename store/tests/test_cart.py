import json
from decimal import Decimal

from django.test import RequestFactory, TestCase

from core.models import Category, Product
from store.cart import MAX_QTY_PER_ITEM, add_to_cart, get_cart_lines, set_cart_qty


def make_product(name='Cabo Turbo CB-105', stock=5):
    category, _ = Category.objects.get_or_create(
        slug='cabos', defaults={'name': 'Cabos', 'icon': 'cable'}
    )
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        price=Decimal('99.00'),
        stock=stock,
        category=category,
    )


def request_with_cart(cart):
    request = RequestFactory().get('/')
    request.COOKIES['cart'] = json.dumps(cart)
    return request


class AddToCartTests(TestCase):
    def test_adds_requested_quantity_to_empty_cart(self):
        product = make_product(stock=5)

        cart = add_to_cart(request_with_cart({}), product.id, 2)

        self.assertEqual(cart[str(product.id)], 2)

    def test_caps_quantity_at_available_stock(self):
        product = make_product(stock=3)

        cart = add_to_cart(request_with_cart({}), product.id, 99)

        self.assertEqual(cart[str(product.id)], 3)

    def test_caps_quantity_at_max_per_item_when_stock_is_large(self):
        product = make_product(stock=500)

        cart = add_to_cart(request_with_cart({}), product.id, 999)

        self.assertEqual(cart[str(product.id)], MAX_QTY_PER_ITEM)

    def test_ignores_non_positive_quantity(self):
        product = make_product(stock=5)

        cart = add_to_cart(request_with_cart({}), product.id, 0)

        self.assertNotIn(str(product.id), cart)


class SetCartQtyTests(TestCase):
    def test_removes_item_when_quantity_is_zero(self):
        product = make_product(stock=5)

        cart = set_cart_qty(request_with_cart({str(product.id): 2}), product.id, 0)

        self.assertNotIn(str(product.id), cart)

    def test_caps_updated_quantity_at_available_stock(self):
        product = make_product(stock=4)

        cart = set_cart_qty(request_with_cart({str(product.id): 1}), product.id, 50)

        self.assertEqual(cart[str(product.id)], 4)


class CartLinesTests(TestCase):
    def test_ignores_corrupted_cookie_instead_of_crashing(self):
        request = RequestFactory().get('/')
        request.COOKIES['cart'] = 'not-json-at-all'

        self.assertEqual(get_cart_lines(request), [])

    def test_drops_lines_for_products_that_no_longer_exist(self):
        product = make_product(stock=5)
        request = request_with_cart({str(product.id): 1, '999999': 3})

        lines = get_cart_lines(request)

        self.assertEqual([line['id'] for line in lines], [product.id])

    def test_drops_lines_for_deactivated_products(self):
        product = make_product(stock=5)
        product.active = False
        product.save(update_fields=['active'])

        self.assertEqual(get_cart_lines(request_with_cart({str(product.id): 1})), [])

    def test_clamps_line_quantity_to_current_stock(self):
        product = make_product(stock=2)

        lines = get_cart_lines(request_with_cart({str(product.id): 9}))

        self.assertEqual(lines[0]['qty'], 2)
