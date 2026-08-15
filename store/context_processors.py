from django.conf import settings

from store.cart import get_cart


def cart_count(request):
    cart = get_cart(request)
    return {'cart_count': sum(int(v) for v in cart.values())}


def tracking_ids(request):
    return {
        'ga4_id': settings.GA4_MEASUREMENT_ID,
        'meta_pixel_id': settings.META_PIXEL_ID,
    }
