from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from core.models import Brand, Category, Product
from store.views import PRODUCTS_PER_PAGE


def make_product(name, **extra):
    category, _ = Category.objects.get_or_create(
        slug='cabos', defaults={'name': 'Cabos', 'icon': 'cable'}
    )
    fields = {
        'name': name,
        'slug': name.lower().replace(' ', '-'),
        'price': Decimal('99.00'),
        'stock': 5,
        'category': category,
    }
    fields.update(extra)
    return Product.objects.create(**fields)


class ProductSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.agold = Brand.objects.create(name='AGOLD', slug='agold')
        self.cabo = make_product('Cabo Turbo CB-105', sku='1002347', brand=self.agold)
        self.abafador = make_product('Abafador LEF-1219', sku='1002350', is_inclusive=True)

    def _names(self, response):
        return [p.name for p in response.context['products']]

    def test_finds_product_by_name(self):
        response = self.client.get(reverse('store:produtos'), {'busca': 'abafador'})

        self.assertEqual(self._names(response), ['Abafador LEF-1219'])

    def test_finds_product_by_sku(self):
        response = self.client.get(reverse('store:produtos'), {'busca': '1002347'})

        self.assertEqual(self._names(response), ['Cabo Turbo CB-105'])

    def test_finds_product_by_brand_name(self):
        response = self.client.get(reverse('store:produtos'), {'busca': 'agold'})

        self.assertEqual(self._names(response), ['Cabo Turbo CB-105'])

    def test_returns_empty_list_when_nothing_matches(self):
        response = self.client.get(reverse('store:produtos'), {'busca': 'geladeira'})

        self.assertEqual(self._names(response), [])

    def test_hides_inactive_products_from_search(self):
        Product.objects.filter(id=self.cabo.id).update(active=False)

        response = self.client.get(reverse('store:produtos'), {'busca': '1002347'})

        self.assertEqual(self._names(response), [])

    def test_filters_the_inclusive_line(self):
        response = self.client.get(reverse('store:produtos'), {'categoria': 'inclusivos'})

        self.assertEqual(self._names(response), ['Abafador LEF-1219'])


class ProductPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        for index in range(PRODUCTS_PER_PAGE + 6):
            make_product(f'Produto {index:03d}')

    def test_first_page_is_capped_at_page_size(self):
        response = self.client.get(reverse('store:produtos'))

        self.assertEqual(len(response.context['products']), PRODUCTS_PER_PAGE)
        self.assertTrue(response.context['page_obj'].has_next())

    def test_second_page_holds_the_remainder(self):
        response = self.client.get(reverse('store:produtos'), {'page': '2'})

        self.assertEqual(len(response.context['products']), 6)
        self.assertFalse(response.context['page_obj'].has_next())

    def test_invalid_page_falls_back_to_the_last_page(self):
        response = self.client.get(reverse('store:produtos'), {'page': '999'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 2)
