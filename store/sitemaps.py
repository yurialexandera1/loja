from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from core.models import BlogPost, Category, Product


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.active()

    def location(self, product):
        return reverse('store:produto', args=[product.slug])


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, category):
        return f"{reverse('store:produtos')}?categoria={category.slug}"


class BlogSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return BlogPost.objects.published()

    def location(self, post):
        return reverse('store:blog_post', args=[post.slug])

    def lastmod(self, post):
        return post.created_at


class StaticSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['store:home', 'store:produtos']

    def location(self, name):
        return reverse(name)
