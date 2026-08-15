"""Feed de produtos no formato Google Merchant / Meta Catalog (RSS 2.0 + g: namespace).
Usado para publicar o catalogo no Instagram Shopping e no Google Shopping.
"""

from django.http import HttpResponse
from django.template.loader import render_to_string

from core.models import Product


def produtos_xml(request):
    produtos = Product.objects.for_listing()
    xml = render_to_string('store/feed_produtos.xml', {'produtos': produtos, 'request': request})
    return HttpResponse(xml, content_type='application/xml')
