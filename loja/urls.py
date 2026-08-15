from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from store.sitemaps import BlogSitemap, CategorySitemap, ProductSitemap, StaticSitemap

SITEMAPS = {
    'static': StaticSitemap,
    'produtos': ProductSitemap,
    'categorias': CategorySitemap,
    'blog': BlogSitemap,
}


def robots_txt(request):
    linhas = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /painel/',
        'Disallow: /carrinho/',
        'Disallow: /checkout/',
        'Disallow: /pedido/',
        f'Sitemap: https://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(linhas), content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('painel/', include('panel.urls')),
    path('api/', include('api.urls')),
    path('robots.txt', robots_txt, name='robots'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap'),
    path('', include('store.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
