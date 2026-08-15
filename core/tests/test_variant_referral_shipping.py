from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from core.models import Category, Product, ReferralCode, ShippingZone, Variant


def make_category(**extra):
    fields = {'slug': 'cabos', 'name': 'Cabos', 'icon': 'cable'}
    fields.update(extra)
    category, _ = Category.objects.get_or_create(slug=fields['slug'], defaults=fields)
    return category


def make_product(**extra):
    fields = {
        'name': 'Abafador LEF-1219',
        'slug': 'abafador-lef-1219',
        'price': Decimal('199.00'),
        'stock': 5,
        'category': make_category(),
    }
    fields.update(extra)
    return Product.objects.create(**fields)


class VariantTests(TestCase):
    def test_variant_has_its_own_stock_separate_from_product(self):
        product = make_product(stock=0)
        azul = Variant.objects.create(product=product, color='Azul', size='Infantil', stock=4)

        self.assertEqual(azul.stock, 4)
        self.assertEqual(product.stock, 0)

    def test_product_total_stock_sums_all_variants(self):
        product = make_product(stock=0)
        Variant.objects.create(product=product, color='Azul', size='Infantil', stock=4)
        Variant.objects.create(product=product, color='Rosa', size='Infantil', stock=3)

        self.assertEqual(product.total_variant_stock, 7)

    def test_product_without_variants_falls_back_to_own_stock(self):
        product = make_product(stock=5)

        self.assertEqual(product.total_variant_stock, 5)

    def test_variant_combination_is_unique_per_product(self):
        product = make_product()
        Variant.objects.create(product=product, color='Azul', size='Infantil', stock=4)

        with self.assertRaises(IntegrityError):
            Variant.objects.create(product=product, color='Azul', size='Infantil', stock=1)

    def test_variant_label_combines_color_and_size(self):
        variant = Variant(color='Azul', size='Infantil')

        self.assertEqual(variant.label, 'Azul · Infantil')

    def test_variant_in_stock_reflects_its_own_stock(self):
        variant = Variant(stock=0)

        self.assertFalse(variant.in_stock)


class ReferralCodeTests(TestCase):
    def test_code_is_generated_automatically(self):
        referral = ReferralCode.objects.create(owner_name='Mariana Ribeiro', owner_email='m@example.com')

        self.assertTrue(referral.code)

    def test_generated_codes_are_unique(self):
        first = ReferralCode.objects.create(owner_name='A', owner_email='a@example.com')
        second = ReferralCode.objects.create(owner_name='B', owner_email='b@example.com')

        self.assertNotEqual(first.code, second.code)

    def test_referral_use_increments_counter(self):
        referral = ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')

        referral.register_use()

        self.assertEqual(referral.uses, 1)

    def test_reward_unlocks_after_threshold(self):
        referral = ReferralCode.objects.create(
            owner_name='Mariana', owner_email='m@example.com', reward_threshold=3
        )

        for _ in range(3):
            referral.register_use()

        self.assertTrue(referral.reward_unlocked)

    def test_reward_not_unlocked_before_threshold(self):
        referral = ReferralCode.objects.create(
            owner_name='Mariana', owner_email='m@example.com', reward_threshold=3
        )

        referral.register_use()

        self.assertFalse(referral.reward_unlocked)


class ShippingZoneValidationTests(TestCase):
    def test_rejects_cep_start_after_cep_end(self):
        zone = ShippingZone(
            name='Invertida', cep_start='23099999', cep_end='22700000',
            price=Decimal('15.00'), days_min=1, days_max=3,
        )

        with self.assertRaises(Exception):
            zone.full_clean()

    def test_rejects_non_numeric_cep(self):
        zone = ShippingZone(
            name='Invalida', cep_start='ABCDEFGH', cep_end='22799999',
            price=Decimal('15.00'), days_min=1, days_max=3,
        )

        with self.assertRaises(Exception):
            zone.full_clean()

    def test_rejects_days_min_after_days_max(self):
        zone = ShippingZone(
            name='Prazo invertido', cep_start='22700000', cep_end='22799999',
            price=Decimal('15.00'), days_min=8, days_max=3,
        )

        with self.assertRaises(Exception):
            zone.full_clean()

    def test_accepts_a_valid_zone(self):
        zone = ShippingZone(
            name='Recreio', cep_start='22790000', cep_end='22799999',
            price=Decimal('12.00'), days_min=1, days_max=2,
        )

        zone.full_clean()


class ShippingZoneTests(TestCase):
    def test_zone_matches_cep_within_its_range(self):
        ShippingZone.objects.create(
            name='Rio — Zona Oeste', cep_start='22700000', cep_end='23099999',
            price=Decimal('15.00'), days_min=1, days_max=3,
        )

        zone = ShippingZone.objects.for_cep('22790701')

        self.assertIsNotNone(zone)
        self.assertEqual(zone.name, 'Rio — Zona Oeste')

    def test_cep_outside_every_range_finds_nothing(self):
        ShippingZone.objects.create(
            name='Rio — Zona Oeste', cep_start='22700000', cep_end='23099999',
            price=Decimal('15.00'), days_min=1, days_max=3,
        )

        self.assertIsNone(ShippingZone.objects.for_cep('90000000'))

    def test_cep_with_punctuation_is_normalized(self):
        ShippingZone.objects.create(
            name='Rio — Zona Oeste', cep_start='22700000', cep_end='23099999',
            price=Decimal('15.00'), days_min=1, days_max=3,
        )

        self.assertIsNotNone(ShippingZone.objects.for_cep('22790-701'))

    def test_narrower_zone_wins_when_ranges_overlap(self):
        ShippingZone.objects.create(
            name='Rio Estado', cep_start='20000000', cep_end='28999999',
            price=Decimal('25.00'), days_min=3, days_max=8,
        )
        ShippingZone.objects.create(
            name='Recreio', cep_start='22790000', cep_end='22799999',
            price=Decimal('12.00'), days_min=1, days_max=2,
        )

        zone = ShippingZone.objects.for_cep('22790701')

        self.assertEqual(zone.name, 'Recreio')
