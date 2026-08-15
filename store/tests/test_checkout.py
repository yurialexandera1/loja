from decimal import Decimal

from django.test import TestCase

from core.models import Category, Coupon, Order, OrderItem, Product, ReferralCode, ShippingZone
from store.checkout_service import OutOfStock, create_order


def make_product(name='Cabo Turbo CB-105', price='99.00', stock=5):
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


def line_for(product, qty):
    return {
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'qty': qty,
        'icon': product.icon,
    }


def lines_over_stock(product):
    return [line_for(product, product.stock + 1)]


CUSTOMER = {
    'customer_name': 'Mariana Ribeiro',
    'email': 'mariana@example.com',
    'phone': '21988124407',
    'address': 'Av. das Americas, 15500',
    'city': 'Rio de Janeiro',
    'zip': '22790-701',
    'shipping_option': 'padrao',
}


class CreateOrderStockTests(TestCase):
    def test_creates_order_and_decrements_stock_when_quantity_available(self):
        product = make_product(stock=5)

        order = create_order(None, CUSTOMER, [line_for(product, 2)], Decimal('198.00'))

        product.refresh_from_db()
        self.assertEqual(product.stock, 3)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.status, 'pendente')

    def test_raises_out_of_stock_when_quantity_exceeds_available(self):
        product = make_product(stock=2)

        with self.assertRaises(OutOfStock):
            create_order(None, CUSTOMER, [line_for(product, 3)], Decimal('297.00'))

    def test_stock_never_goes_negative_after_rejected_order(self):
        product = make_product(stock=2)

        with self.assertRaises(OutOfStock):
            create_order(None, CUSTOMER, lines_over_stock(product), Decimal('297.00'))

        product.refresh_from_db()
        self.assertEqual(product.stock, 2)

    def test_rolls_back_whole_order_when_second_item_is_unavailable(self):
        available = make_product(name='Cabo OK', stock=10)
        unavailable = make_product(name='Abafador LEF-1219', price='199.00', stock=1)
        lines = [line_for(available, 1), line_for(unavailable, 5)]

        with self.assertRaises(OutOfStock):
            create_order(None, CUSTOMER, lines, Decimal('1094.00'))

        available.refresh_from_db()
        self.assertEqual(available.stock, 10)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_rejects_line_for_inactive_product(self):
        product = make_product(stock=5)
        product.active = False
        product.save(update_fields=['active'])

        with self.assertRaises(OutOfStock):
            create_order(None, CUSTOMER, [line_for(product, 1)], Decimal('99.00'))


class CreateOrderTotalTests(TestCase):
    def test_total_is_subtotal_plus_shipping_price(self):
        product = make_product(stock=5)

        order = create_order(None, CUSTOMER, [line_for(product, 2)], Decimal('198.00'))

        self.assertEqual(order.total, Decimal('213.00'))

    def test_price_comes_from_database_not_from_submitted_line(self):
        product = make_product(price='99.00', stock=5)
        tampered = line_for(product, 1)
        tampered['price'] = 1.00

        order = create_order(None, CUSTOMER, [tampered], Decimal('1.00'))

        item = order.items.get()
        self.assertEqual(item.price, Decimal('99.00'))
        self.assertEqual(order.total, Decimal('114.00'))

    def test_order_code_is_unique_per_order(self):
        product = make_product(stock=10)

        first = create_order(None, CUSTOMER, [line_for(product, 1)], Decimal('99.00'))
        second = create_order(None, CUSTOMER, [line_for(product, 1)], Decimal('99.00'))

        self.assertNotEqual(first.code, second.code)


class CreateOrderCouponTests(TestCase):
    def test_valid_coupon_discounts_the_subtotal_before_shipping(self):
        product = make_product(price='200.00', stock=5)
        coupon = Coupon.objects.create(code='OFF10', percent_off=10)

        order = create_order(
            None, CUSTOMER, [line_for(product, 1)], Decimal('200.00'), coupon=coupon
        )

        self.assertEqual(order.discount, Decimal('20.00'))
        self.assertEqual(order.total, Decimal('195.00'))
        self.assertEqual(order.coupon, coupon)

    def test_applying_a_coupon_increments_its_usage_count(self):
        product = make_product(stock=5)
        coupon = Coupon.objects.create(code='OFF10', percent_off=10, used_count=2)

        create_order(None, CUSTOMER, [line_for(product, 1)], Decimal('99.00'), coupon=coupon)

        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 3)

    def test_expired_coupon_is_ignored_instead_of_applied(self):
        from django.utils import timezone

        product = make_product(price='200.00', stock=5)
        coupon = Coupon.objects.create(
            code='OLD10', percent_off=10, expires_at=timezone.now() - timezone.timedelta(days=1)
        )

        order = create_order(
            None, CUSTOMER, [line_for(product, 1)], Decimal('200.00'), coupon=coupon
        )

        self.assertEqual(order.discount, Decimal('0'))
        self.assertIsNone(order.coupon)

    def test_order_without_coupon_has_zero_discount(self):
        product = make_product(stock=5)

        order = create_order(None, CUSTOMER, [line_for(product, 1)], Decimal('99.00'))

        self.assertEqual(order.discount, Decimal('0'))
        self.assertIsNone(order.coupon)


class CreateOrderShippingZoneTests(TestCase):
    def test_order_uses_shipping_zone_price_when_cep_matches(self):
        ShippingZone.objects.create(
            name='Recreio', cep_start='22790000', cep_end='22799999',
            price=Decimal('12.00'), days_min=1, days_max=2,
        )
        product = make_product(price='100.00', stock=5)
        customer = {**CUSTOMER, 'zip': '22790-701'}

        order = create_order(None, customer, [line_for(product, 1)], Decimal('100.00'))

        self.assertEqual(order.total, Decimal('112.00'))

    def test_order_falls_back_to_fixed_table_without_matching_zone(self):
        product = make_product(price='100.00', stock=5)
        customer = {**CUSTOMER, 'zip': '90000-000'}

        order = create_order(None, customer, [line_for(product, 1)], Decimal('100.00'))

        self.assertEqual(order.total, Decimal('115.00'))


class CreateOrderReferralTests(TestCase):
    def test_referral_applies_ten_percent_discount(self):
        product = make_product(price='200.00', stock=5)
        referral = ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')

        order = create_order(
            None, CUSTOMER, [line_for(product, 1)], Decimal('200.00'), referral=referral
        )

        self.assertEqual(order.discount, Decimal('20.00'))
        self.assertEqual(order.total, Decimal('195.00'))

    def test_referral_use_is_credited_to_the_owner(self):
        product = make_product(stock=5)
        referral = ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')

        create_order(None, CUSTOMER, [line_for(product, 1)], Decimal('99.00'), referral=referral)

        referral.refresh_from_db()
        self.assertEqual(referral.uses, 1)

    def test_coupon_takes_priority_over_referral(self):
        product = make_product(price='200.00', stock=5)
        coupon = Coupon.objects.create(code='OFF50', percent_off=50)
        referral = ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')

        order = create_order(
            None, CUSTOMER, [line_for(product, 1)], Decimal('200.00'),
            coupon=coupon, referral=referral,
        )

        self.assertEqual(order.discount, Decimal('100.00'))
        referral.refresh_from_db()
        self.assertEqual(referral.uses, 0)
