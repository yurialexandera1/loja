from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from core.models import Brand, Category, Product, ProductImage


def make_category():
    category, _ = Category.objects.get_or_create(
        slug='cabos', defaults={'name': 'Cabos', 'icon': 'cable'}
    )
    return category


def make_product(name='Cabo Turbo CB-105', **extra):
    fields = {
        'name': name,
        'slug': name.lower().replace(' ', '-'),
        'price': Decimal('99.00'),
        'stock': 5,
        'category': make_category(),
    }
    fields.update(extra)
    return Product.objects.create(**fields)


class BrandTests(TestCase):
    def test_brand_is_optional_on_product(self):
        product = make_product()

        self.assertIsNone(product.brand)

    def test_product_survives_when_brand_is_deleted(self):
        brand = Brand.objects.create(name='AGOLD', slug='agold')
        product = make_product(brand=brand)

        brand.delete()

        product.refresh_from_db()
        self.assertIsNone(product.brand)
        self.assertTrue(Product.objects.filter(id=product.id).exists())

    def test_brand_slug_is_unique(self):
        Brand.objects.create(name='AGOLD', slug='agold')

        with self.assertRaises(IntegrityError):
            Brand.objects.create(name='Agold Duplicada', slug='agold')


class ProductSkuTests(TestCase):
    def test_sku_is_unique_across_products(self):
        make_product(sku='1002350')

        with self.assertRaises(IntegrityError):
            make_product(name='Outro produto', sku='1002350')

    def test_blank_sku_does_not_collide(self):
        make_product(name='Sem codigo A', sku='')
        make_product(name='Sem codigo B', sku='')

        self.assertEqual(Product.objects.filter(sku='').count(), 2)


class ProductPricingTests(TestCase):
    def test_has_discount_is_false_without_compare_at_price(self):
        product = make_product()

        self.assertFalse(product.has_discount)
        self.assertEqual(product.discount_percent, 0)

    def test_discount_percent_is_rounded_down(self):
        product = make_product(price=Decimal('99.00'), compare_at_price=Decimal('129.00'))

        self.assertTrue(product.has_discount)
        self.assertEqual(product.discount_percent, 23)

    def test_ignores_compare_at_price_below_current_price(self):
        product = make_product(price=Decimal('99.00'), compare_at_price=Decimal('80.00'))

        self.assertFalse(product.has_discount)
        self.assertEqual(product.discount_percent, 0)

    def test_pix_price_applies_configured_discount(self):
        product = make_product(price=Decimal('199.00'))

        self.assertEqual(product.pix_price, Decimal('193.03'))


class ProductStockStateTests(TestCase):
    def test_is_low_stock_when_at_or_below_threshold(self):
        self.assertTrue(make_product(name='Quase acabando', stock=4).is_low_stock)

    def test_is_not_low_stock_when_above_threshold(self):
        self.assertFalse(make_product(name='Cheio', stock=5).is_low_stock)

    def test_is_not_low_stock_when_sold_out(self):
        product = make_product(name='Esgotado', stock=0)

        self.assertFalse(product.is_low_stock)
        self.assertFalse(product.in_stock)


class ProductImageTests(TestCase):
    def test_images_are_ordered_by_position(self):
        product = make_product()
        ProductImage.objects.create(product=product, image='produtos/c.jpg', order=2)
        ProductImage.objects.create(product=product, image='produtos/a.jpg', order=0)
        ProductImage.objects.create(product=product, image='produtos/b.jpg', order=1)

        names = [image.image.name for image in product.images.all()]

        self.assertEqual(names, ['produtos/a.jpg', 'produtos/b.jpg', 'produtos/c.jpg'])

    def test_main_image_is_the_first_one(self):
        product = make_product()
        ProductImage.objects.create(product=product, image='produtos/z.jpg', order=5)
        first = ProductImage.objects.create(product=product, image='produtos/a.jpg', order=0)

        self.assertEqual(product.main_image, first)

    def test_main_image_is_none_without_images(self):
        self.assertIsNone(make_product().main_image)

    def test_images_are_deleted_with_the_product(self):
        product = make_product()
        ProductImage.objects.create(product=product, image='produtos/a.jpg')

        product.delete()

        self.assertEqual(ProductImage.objects.count(), 0)


class InclusiveLineTests(TestCase):
    def test_inclusive_products_have_their_own_queryset(self):
        make_product(name='Cordao TEA', is_inclusive=True)
        make_product(name='Cabo comum')

        inclusive = Product.objects.inclusive()

        self.assertEqual([p.name for p in inclusive], ['Cordao TEA'])

    def test_inclusive_queryset_hides_inactive_products(self):
        make_product(name='Cordao TEA', is_inclusive=True, active=False)

        self.assertEqual(Product.objects.inclusive().count(), 0)
