from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.models import BlogPost, Category, Coupon, Product, ProductReview


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


class CouponTests(TestCase):
    def test_valid_coupon_is_usable(self):
        coupon = Coupon.objects.create(code='BEMVINDO10', percent_off=10)

        self.assertTrue(coupon.is_valid())

    def test_inactive_coupon_is_not_usable(self):
        coupon = Coupon.objects.create(code='OFF', percent_off=10, active=False)

        self.assertFalse(coupon.is_valid())

    def test_expired_coupon_is_not_usable(self):
        coupon = Coupon.objects.create(
            code='OFF', percent_off=10, expires_at=timezone.now() - timezone.timedelta(days=1)
        )

        self.assertFalse(coupon.is_valid())

    def test_coupon_past_usage_limit_is_not_usable(self):
        coupon = Coupon.objects.create(code='OFF', percent_off=10, max_uses=1, used_count=1)

        self.assertFalse(coupon.is_valid())

    def test_coupon_below_usage_limit_is_usable(self):
        coupon = Coupon.objects.create(code='OFF', percent_off=10, max_uses=5, used_count=2)

        self.assertTrue(coupon.is_valid())

    def test_discount_applies_percentage_to_subtotal(self):
        coupon = Coupon.objects.create(code='OFF10', percent_off=10)

        self.assertEqual(coupon.discount_for(Decimal('200.00')), Decimal('20.00'))

    def test_discount_never_exceeds_subtotal(self):
        coupon = Coupon.objects.create(code='OFF200', percent_off=200)

        self.assertEqual(coupon.discount_for(Decimal('50.00')), Decimal('50.00'))

    def test_code_lookup_is_case_insensitive(self):
        Coupon.objects.create(code='BEMVINDO10', percent_off=10)

        self.assertTrue(Coupon.objects.filter(code__iexact='bemvindo10').exists())

    def test_percent_off_above_100_fails_validation(self):
        coupon = Coupon(code='OFF999', percent_off=999)

        with self.assertRaises(Exception):
            coupon.full_clean()

    def test_percent_off_of_zero_fails_validation(self):
        coupon = Coupon(code='OFF0', percent_off=0)

        with self.assertRaises(Exception):
            coupon.full_clean()


class ProductReviewTests(TestCase):
    def test_review_requires_rating_between_1_and_5(self):
        product = make_product()
        review = ProductReview(
            product=product, author_name='Mariana', rating=6, comment='Otimo'
        )

        with self.assertRaises(Exception):
            review.full_clean()

    def test_average_rating_is_none_without_approved_reviews(self):
        product = make_product()

        self.assertIsNone(product.average_rating)

    def test_average_rating_only_counts_approved_reviews(self):
        product = make_product()
        ProductReview.objects.create(
            product=product, author_name='A', rating=5, comment='Bom', approved=True
        )
        ProductReview.objects.create(
            product=product, author_name='B', rating=1, comment='Ruim', approved=False
        )

        self.assertEqual(product.average_rating, 5)

    def test_review_count_only_counts_approved(self):
        product = make_product()
        ProductReview.objects.create(
            product=product, author_name='A', rating=5, comment='Bom', approved=True
        )
        ProductReview.objects.create(
            product=product, author_name='B', rating=4, comment='Ok', approved=False
        )

        self.assertEqual(product.review_count, 1)


class CategorySeoTests(TestCase):
    def test_category_has_optional_seo_text(self):
        category = make_category(seo_text='Capinhas e peliculas para todos os modelos.')

        self.assertIn('peliculas', category.seo_text)

    def test_category_seo_text_defaults_to_blank(self):
        category = make_category()

        self.assertEqual(category.seo_text, '')


class BlogPostTests(TestCase):
    def test_only_published_posts_appear_in_default_queryset(self):
        BlogPost.objects.create(
            title='Publicado', slug='publicado', body='Texto', published=True
        )
        BlogPost.objects.create(
            title='Rascunho', slug='rascunho', body='Texto', published=False
        )

        self.assertEqual(BlogPost.objects.published().count(), 1)

    def test_posts_are_ordered_newest_first(self):
        first = BlogPost.objects.create(
            title='Primeiro', slug='primeiro', body='A', published=True
        )
        second = BlogPost.objects.create(
            title='Segundo', slug='segundo', body='B', published=True
        )

        self.assertEqual(list(BlogPost.objects.published()), [second, first])
