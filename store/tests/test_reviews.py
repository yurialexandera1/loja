from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from core.models import Category, Product, ProductReview


def make_product(**extra):
    category, _ = Category.objects.get_or_create(
        slug='cabos', defaults={'name': 'Cabos', 'icon': 'cable'}
    )
    fields = {
        'name': 'Cabo Turbo CB-105',
        'slug': 'cabo-turbo-cb-105',
        'price': Decimal('99.00'),
        'stock': 5,
        'category': category,
    }
    fields.update(extra)
    return Product.objects.create(**fields)


class SubmitReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product()

    def test_valid_review_is_saved_as_unapproved(self):
        self.client.post(
            reverse('store:avaliar', args=[self.product.slug]),
            {'author_name': 'Mariana', 'rating': '5', 'comment': 'Chegou rapido, otimo produto.'},
        )

        review = ProductReview.objects.get()
        self.assertFalse(review.approved)
        self.assertEqual(review.rating, 5)

    def test_thanks_message_does_not_reveal_pending_moderation_as_error(self):
        response = self.client.post(
            reverse('store:avaliar', args=[self.product.slug]),
            {'author_name': 'Mariana', 'rating': '5', 'comment': 'Otimo produto, recomendo.'},
            follow=True,
        )

        self.assertContains(response, 'recebida')

    def test_rejects_rating_outside_one_to_five(self):
        self.client.post(
            reverse('store:avaliar', args=[self.product.slug]),
            {'author_name': 'Mariana', 'rating': '9', 'comment': 'Nota invalida'},
        )

        self.assertEqual(ProductReview.objects.count(), 0)

    def test_rejects_blank_comment(self):
        self.client.post(
            reverse('store:avaliar', args=[self.product.slug]),
            {'author_name': 'Mariana', 'rating': '5', 'comment': ''},
        )

        self.assertEqual(ProductReview.objects.count(), 0)


class ProductPageReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product()

    def test_approved_review_appears_on_product_page(self):
        ProductReview.objects.create(
            product=self.product,
            author_name='Mariana',
            rating=5,
            comment='Excelente, recomendo a todos.',
            approved=True,
        )

        response = self.client.get(reverse('store:produto', args=[self.product.slug]))

        self.assertContains(response, 'Excelente, recomendo a todos.')

    def test_unapproved_review_does_not_appear(self):
        ProductReview.objects.create(
            product=self.product,
            author_name='Mariana',
            rating=1,
            comment='Comentario nao aprovado ainda.',
            approved=False,
        )

        response = self.client.get(reverse('store:produto', args=[self.product.slug]))

        self.assertNotContains(response, 'Comentario nao aprovado ainda.')

    def test_product_without_reviews_shows_empty_state(self):
        response = self.client.get(reverse('store:produto', args=[self.product.slug]))

        self.assertContains(response, 'Ainda sem avaliações')
