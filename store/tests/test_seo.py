from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from core.models import BlogPost, Category, Product


def make_category(**extra):
    fields = {'slug': 'cabos', 'name': 'Cabos', 'icon': 'cable'}
    fields.update(extra)
    category, _ = Category.objects.get_or_create(slug=fields['slug'], defaults=fields)
    return category


def make_product(**extra):
    fields = {
        'name': 'Cabo Turbo CB-105',
        'slug': 'cabo-turbo-cb-105',
        'price': Decimal('99.00'),
        'stock': 5,
        'category': make_category(),
    }
    fields.update(extra)
    return Product.objects.create(**fields)


class SitemapTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sitemap_lists_active_product_urls(self):
        product = make_product()

        response = self.client.get('/sitemap.xml')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'/produto/{product.slug}/')

    def test_sitemap_omits_inactive_products(self):
        product = make_product(active=False)

        response = self.client.get('/sitemap.xml')

        self.assertNotContains(response, f'/produto/{product.slug}/')

    def test_sitemap_includes_category_pages(self):
        make_category()

        response = self.client.get('/sitemap.xml')

        self.assertContains(response, 'categoria=cabos')

    def test_sitemap_includes_published_blog_posts(self):
        BlogPost.objects.create(
            title='Inclusão de verdade', slug='inclusao-de-verdade', body='Texto', published=True
        )

        response = self.client.get('/sitemap.xml')

        self.assertContains(response, '/blog/inclusao-de-verdade/')

    def test_sitemap_omits_unpublished_blog_posts(self):
        BlogPost.objects.create(
            title='Rascunho', slug='rascunho', body='Texto', published=False
        )

        response = self.client.get('/sitemap.xml')

        self.assertNotContains(response, '/blog/rascunho/')


class RobotsTests(TestCase):
    def test_robots_txt_points_to_the_sitemap(self):
        response = self.client.get('/robots.txt')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sitemap:')
        self.assertContains(response, '/sitemap.xml')

    def test_robots_txt_disallows_the_staff_panel(self):
        response = self.client.get('/robots.txt')

        self.assertContains(response, 'Disallow: /painel/')

    def test_robots_txt_disallows_cart_and_checkout(self):
        response = self.client.get('/robots.txt')

        self.assertContains(response, 'Disallow: /carrinho/')
        self.assertContains(response, 'Disallow: /checkout/')


class ProductFeedTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_feed_lists_active_products_with_price_and_availability(self):
        make_product(sku='1002347')

        response = self.client.get(reverse('store:feed_produtos'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertContains(response, '1002347')
        self.assertContains(response, 'in stock')
        self.assertContains(response, 'BRL')

    def test_feed_marks_out_of_stock_products(self):
        make_product(name='Esgotado', stock=0)

        response = self.client.get(reverse('store:feed_produtos'))

        self.assertContains(response, 'out of stock')

    def test_feed_omits_inactive_products(self):
        product = make_product(active=False)

        response = self.client.get(reverse('store:feed_produtos'))

        self.assertNotContains(response, product.name)


class ProductStructuredDataTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_product_page_includes_json_ld_offer(self):
        product = make_product(sku='1002347')

        response = self.client.get(reverse('store:produto', args=[product.slug]))

        self.assertContains(response, '"@type": "Product"')
        self.assertContains(response, '"@type": "Offer"')
        self.assertContains(response, 'schema.org/InStock')

    def test_out_of_stock_product_reports_out_of_stock_availability(self):
        product = make_product(name='Esgotado', stock=0)

        response = self.client.get(reverse('store:produto', args=[product.slug]))

        self.assertContains(response, 'schema.org/OutOfStock')

    def test_product_page_sets_open_graph_title(self):
        product = make_product()

        response = self.client.get(reverse('store:produto', args=[product.slug]))

        self.assertContains(response, f'og:title" content="{product.name}')
