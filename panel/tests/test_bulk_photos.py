from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from core.models import Category, Product, ProductImage


def make_category(**extra):
    fields = {'slug': 'cabos', 'name': 'Cabos', 'icon': 'cable'}
    fields.update(extra)
    category, _ = Category.objects.get_or_create(slug=fields['slug'], defaults=fields)
    return category


def make_product(sku, **extra):
    fields = {
        'name': f'Produto {sku}',
        'slug': f'produto-{sku}'.lower(),
        'sku': sku,
        'price': Decimal('50.00'),
        'stock': 5,
        'category': make_category(),
    }
    fields.update(extra)
    return Product.objects.create(**fields)


def fake_image(filename):
    buffer = BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/jpeg')


class BulkPhotoUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='yuri', password='senha12345', is_staff=True)
        self.client.login(username='yuri', password='senha12345')

    def test_uploads_are_matched_to_products_by_sku_in_filename(self):
        make_product(sku='1002347')
        make_product(sku='1002350')

        self.client.post(
            reverse('panel:produtos_fotos_lote'),
            {'files': [fake_image('1002347.jpg'), fake_image('1002350-foto2.jpg')]},
        )

        self.assertEqual(ProductImage.objects.filter(product__sku='1002347').count(), 1)
        self.assertEqual(ProductImage.objects.filter(product__sku='1002350').count(), 1)

    def test_unmatched_filename_is_reported_and_not_saved(self):
        make_product(sku='1002347')

        response = self.client.post(
            reverse('panel:produtos_fotos_lote'),
            {'files': [fake_image('codigo-inexistente.jpg')]},
            follow=True,
        )

        self.assertEqual(ProductImage.objects.count(), 0)
        self.assertContains(response, 'codigo-inexistente.jpg')

    def test_second_photo_for_same_product_gets_next_order(self):
        make_product(sku='1002347')

        self.client.post(
            reverse('panel:produtos_fotos_lote'),
            {'files': [fake_image('1002347-a.jpg'), fake_image('1002347-b.jpg')]},
        )

        orders = list(
            ProductImage.objects.filter(product__sku='1002347').order_by('order').values_list('order', flat=True)
        )
        self.assertEqual(orders, [0, 1])

    def test_page_renders_for_staff(self):
        response = self.client.get(reverse('panel:produtos_fotos_lote'))

        self.assertEqual(response.status_code, 200)
