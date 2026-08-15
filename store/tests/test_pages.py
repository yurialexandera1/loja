"""Cada pagina precisa abrir de verdade — template quebrado nao aparece
nos testes de logica, so aqui."""

import json
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from core.models import Brand, Category, Order, OrderItem, Product, ReferralCode


def make_product(name='Cabo Turbo CB-105', **extra):
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


class PageRenderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.brand = Brand.objects.create(name='AGOLD', slug='agold')
        self.product = make_product(
            sku='1002347',
            brand=self.brand,
            featured=True,
            compare_at_price=Decimal('129.00'),
            description='Cabo resistente com carga rapida.',
        )

    def test_home_renders_with_featured_product(self):
        response = self.client.get(reverse('store:home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/home.html')
        self.assertContains(response, 'Cabo Turbo CB-105')

    def test_home_shows_discount_badge_from_compare_at_price(self):
        response = self.client.get(reverse('store:home'))

        self.assertContains(response, '23%')

    def test_home_category_showcase_uses_a_product_photo_when_available(self):
        from core.models import ProductImage

        ProductImage.objects.create(product=self.product, image='produtos/x.jpg')

        response = self.client.get(reverse('store:home'))

        self.assertContains(response, 'cat-card-shot')
        self.assertContains(response, 'produtos/x')

    def test_home_category_showcase_falls_back_to_icon_without_photo(self):
        response = self.client.get(reverse('store:home'))

        self.assertContains(response, 'href="#i-cable"')

    def test_catalog_page_renders(self):
        response = self.client.get(reverse('store:produtos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1002347')

    def test_product_page_renders_with_pix_price(self):
        response = self.client.get(reverse('store:produto', args=[self.product.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '96,03')

    def test_product_page_returns_404_for_inactive_product(self):
        Product.objects.filter(id=self.product.id).update(active=False)

        response = self.client.get(reverse('store:produto', args=[self.product.slug]))

        self.assertEqual(response.status_code, 404)

    def test_empty_cart_page_renders_invitation(self):
        response = self.client.get(reverse('store:carrinho'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seu pedido está vazio')

    def test_cart_page_shows_line_subtotal(self):
        self.client.cookies['cart'] = json.dumps({str(self.product.id): 2})

        response = self.client.get(reverse('store:carrinho'))

        self.assertContains(response, '198,00')

    def test_checkout_page_renders_form(self):
        self.client.cookies['cart'] = json.dumps({str(self.product.id): 1})

        response = self.client.get(reverse('store:checkout'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entrega e pagamento')

    def test_order_page_renders_whatsapp_link(self):
        order = Order.objects.create(
            code='CS-TEST0001',
            customer_name='Mariana Ribeiro',
            email='mariana@example.com',
            address='Av. das Americas, 15500',
            city='Rio de Janeiro',
            zip='22790-701',
            total=Decimal('114.00'),
        )
        OrderItem.objects.create(
            order=order, product_name='Cabo Turbo CB-105', price=Decimal('99.00'), qty=1
        )

        response = self.client.get(reverse('store:pedido', args=[order.code]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wa.me/5521995095642')
        self.assertContains(response, 'CS-TEST0001')


class ReferralSignupPageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_creates_referral_and_shows_link(self):
        response = self.client.post(
            reverse('store:indicar'),
            {'owner_name': 'Mariana Ribeiro', 'owner_email': 'mariana@example.com'},
        )

        referral = ReferralCode.objects.get(owner_email='mariana@example.com')
        self.assertContains(response, referral.code)
        self.assertContains(response, 'ref=' + referral.code)

    def test_repeat_signup_with_same_email_reuses_existing_code(self):
        self.client.post(
            reverse('store:indicar'),
            {'owner_name': 'Mariana', 'owner_email': 'mariana@example.com'},
        )
        self.client.post(
            reverse('store:indicar'),
            {'owner_name': 'Mariana Ribeiro', 'owner_email': 'mariana@example.com'},
        )

        self.assertEqual(ReferralCode.objects.filter(owner_email='mariana@example.com').count(), 1)


class SoldOutProductTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product(name='Esgotado', stock=0)

    def test_catalog_marks_product_as_unavailable(self):
        response = self.client.get(reverse('store:produtos'))

        self.assertContains(response, 'Indisponível')

    def test_product_page_offers_whatsapp_instead_of_buy_button(self):
        response = self.client.get(reverse('store:produto', args=[self.product.slug]))

        self.assertContains(response, 'Avisar quando chegar')
        self.assertNotContains(response, 'Adicionar ao pedido')
