from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from core.models import (
    BlogPost,
    Brand,
    Category,
    Coupon,
    Order,
    OrderItem,
    Product,
    ProductReview,
    ReferralCode,
    ShippingZone,
)


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


class PanelPagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='yuri', password='senha12345', is_staff=True)
        self.client.login(username='yuri', password='senha12345')


class DashboardTests(PanelPagesTestCase):
    def test_dashboard_renders(self):
        response = self.client.get(reverse('panel:dashboard'))
        self.assertEqual(response.status_code, 200)


class ProductPanelTests(PanelPagesTestCase):
    def test_products_list_renders(self):
        make_product()
        response = self.client.get(reverse('panel:produtos'))
        self.assertContains(response, 'Cabo Turbo CB-105')

    def test_product_create_form_renders(self):
        response = self.client.get(reverse('panel:produto_novo'))
        self.assertEqual(response.status_code, 200)

    def test_creating_product_redirects_to_edit_page(self):
        response = self.client.post(
            reverse('panel:produto_novo'),
            {
                'name': 'Novo produto', 'slug': 'novo-produto', 'sku': '', 'category': make_category().pk,
                'description': '', 'price': '10.00', 'stock': '1', 'icon': 'package',
            },
        )
        produto = Product.objects.get(slug='novo-produto')
        self.assertRedirects(response, reverse('panel:produto_editar', args=[produto.pk]))

    def test_product_edit_page_renders_with_images_and_variants_sections(self):
        produto = make_product()
        response = self.client.get(reverse('panel:produto_editar', args=[produto.pk]))
        self.assertContains(response, 'Fotos')
        self.assertContains(response, 'Variantes')

    def test_adding_variant_creates_it_and_redirects_back(self):
        produto = make_product()
        response = self.client.post(
            reverse('panel:produto_variante_nova', args=[produto.pk]),
            {'color': 'Azul', 'size': 'Infantil', 'sku': '', 'stock': '4'},
        )
        self.assertRedirects(response, reverse('panel:produto_editar', args=[produto.pk]))
        self.assertEqual(produto.variants.count(), 1)

    def test_quick_update_changes_price_and_stock_from_the_list(self):
        produto = make_product(price=Decimal('50.00'), stock=1)

        response = self.client.post(
            reverse('panel:produto_rapido', args=[produto.pk]),
            {'price': '65.90', 'stock': '30'},
        )

        produto.refresh_from_db()
        self.assertRedirects(response, reverse('panel:produtos'))
        self.assertEqual(produto.price, Decimal('65.90'))
        self.assertEqual(produto.stock, 30)

    def test_quick_update_rejects_negative_stock(self):
        produto = make_product(price=Decimal('50.00'), stock=10)

        self.client.post(
            reverse('panel:produto_rapido', args=[produto.pk]),
            {'price': '50.00', 'stock': '-5'},
        )

        produto.refresh_from_db()
        self.assertEqual(produto.stock, 10)

    def test_quick_update_preserves_search_query_string_on_redirect(self):
        produto = make_product()

        response = self.client.post(
            f"{reverse('panel:produto_rapido', args=[produto.pk])}?busca=cabo",
            {'price': '99.00', 'stock': '5'},
        )

        self.assertRedirects(response, f"{reverse('panel:produtos')}?busca=cabo")

    def test_products_list_filters_by_category(self):
        outra_categoria = Category.objects.create(name='Fones', slug='fones', icon='headphones')
        produto_cabo = make_product(name='Cabo X')
        produto_fone = make_product(name='Fone Y', slug='fone-y', category=outra_categoria)

        response = self.client.get(reverse('panel:produtos'), {'categoria': outra_categoria.pk})

        nomes = [p.name for p in response.context['produtos']]
        self.assertIn('Fone Y', nomes)
        self.assertNotIn('Cabo X', nomes)

    def test_products_list_filters_by_brand(self):
        marca = Brand.objects.create(name='AGOLD', slug='agold')
        make_product(name='Com marca', brand=marca)
        make_product(name='Sem marca', slug='sem-marca')

        response = self.client.get(reverse('panel:produtos'), {'marca': marca.pk})

        nomes = [p.name for p in response.context['produtos']]
        self.assertIn('Com marca', nomes)
        self.assertNotIn('Sem marca', nomes)

    def test_removing_product_redirects_to_list(self):
        produto = make_product()
        response = self.client.post(reverse('panel:produto_remover', args=[produto.pk]))
        self.assertRedirects(response, reverse('panel:produtos'))
        self.assertFalse(Product.objects.filter(pk=produto.pk).exists())


class OrderPanelTests(PanelPagesTestCase):
    def _make_order(self, **extra):
        fields = {
            'code': 'CS-TEST0001', 'customer_name': 'Mariana Ribeiro', 'email': 'mariana@example.com',
            'address': 'Av. das Americas, 15500', 'city': 'Rio de Janeiro', 'zip': '22790-701',
            'total': Decimal('99.00'),
        }
        fields.update(extra)
        order = Order.objects.create(**fields)
        OrderItem.objects.create(order=order, product_name='Cabo', price=Decimal('99.00'), qty=1)
        return order

    def test_orders_list_renders(self):
        self._make_order()
        response = self.client.get(reverse('panel:pedidos'))
        self.assertContains(response, 'CS-TEST0001')

    def test_order_detail_renders(self):
        order = self._make_order()
        response = self.client.get(reverse('panel:pedido_detalhe', args=[order.pk]))
        self.assertContains(response, 'Mariana Ribeiro')

    def test_changing_status_updates_order(self):
        order = self._make_order()
        self.client.post(reverse('panel:pedido_status', args=[order.pk]), {'status': 'pago'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'pago')

    def test_invalid_status_is_ignored(self):
        order = self._make_order()
        self.client.post(reverse('panel:pedido_status', args=[order.pk]), {'status': 'inexistente'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'pendente')


class CatalogCrudTests(PanelPagesTestCase):
    def test_categories_list_renders(self):
        make_category()
        response = self.client.get(reverse('panel:categorias'))
        self.assertContains(response, 'Cabos')

    def test_creating_category_redirects_to_list(self):
        response = self.client.post(
            reverse('panel:categoria_nova'),
            {'name': 'Áudio', 'slug': 'audio', 'icon': 'headphones', 'order': '0', 'seo_text': ''},
        )
        self.assertRedirects(response, reverse('panel:categorias'))
        self.assertTrue(Category.objects.filter(slug='audio').exists())

    def test_brands_list_renders(self):
        Brand.objects.create(name='AGOLD', slug='agold')
        response = self.client.get(reverse('panel:marcas'))
        self.assertContains(response, 'AGOLD')

    def test_creating_coupon_redirects_to_list(self):
        response = self.client.post(
            reverse('panel:cupom_novo'),
            {'code': 'BEMVINDO10', 'percent_off': '10', 'active': 'on'},
        )
        self.assertRedirects(response, reverse('panel:cupons'))
        self.assertTrue(Coupon.objects.filter(code='BEMVINDO10').exists())

    def test_shipping_zones_list_renders(self):
        ShippingZone.objects.create(
            name='Recreio', cep_start='22790000', cep_end='22799999',
            price=Decimal('12.00'), days_min=1, days_max=2,
        )
        response = self.client.get(reverse('panel:fretes'))
        self.assertContains(response, 'Recreio')

    def test_blog_posts_list_renders(self):
        BlogPost.objects.create(title='Inclusão de verdade', slug='inclusao', body='Texto')
        response = self.client.get(reverse('panel:posts'))
        self.assertContains(response, 'Inclusão de verdade')

    def test_list_page_shows_a_delete_link_for_each_row(self):
        category = make_category()
        response = self.client.get(reverse('panel:categorias'))
        self.assertContains(response, reverse('panel:categoria_remover', args=[category.pk]))

    def test_delete_confirmation_page_renders(self):
        category = make_category()
        response = self.client.get(reverse('panel:categoria_remover', args=[category.pk]))
        self.assertContains(response, category.name)

    def test_confirming_delete_removes_the_category(self):
        category = make_category()
        response = self.client.post(reverse('panel:categoria_remover', args=[category.pk]))
        self.assertRedirects(response, reverse('panel:categorias'))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())


class ReviewModerationTests(PanelPagesTestCase):
    def test_reviews_list_renders(self):
        produto = make_product()
        ProductReview.objects.create(product=produto, author_name='Mariana', rating=5, comment='Ótimo')
        response = self.client.get(reverse('panel:avaliacoes'))
        self.assertContains(response, 'Mariana')

    def test_approving_review_marks_it_approved(self):
        produto = make_product()
        review = ProductReview.objects.create(product=produto, author_name='Mariana', rating=5, comment='Ótimo')
        self.client.post(reverse('panel:avaliacao_aprovar', args=[review.pk]))
        review.refresh_from_db()
        self.assertTrue(review.approved)

    def test_removing_review_deletes_it(self):
        produto = make_product()
        review = ProductReview.objects.create(product=produto, author_name='Mariana', rating=5, comment='Ótimo')
        self.client.post(reverse('panel:avaliacao_remover', args=[review.pk]))
        self.assertFalse(ProductReview.objects.filter(pk=review.pk).exists())


class ReferralPanelTests(PanelPagesTestCase):
    def test_referral_list_renders(self):
        ReferralCode.objects.create(owner_name='Mariana', owner_email='m@example.com')
        response = self.client.get(reverse('panel:indicacoes'))
        self.assertContains(response, 'Mariana')
