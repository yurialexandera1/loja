from core.models import get_site_settings
from store.cart import get_cart


def cart_count(request):
    cart = get_cart(request)
    return {'cart_count': sum(int(v) for v in cart.values())}


def tracking_ids(request):
    site_settings = get_site_settings()
    return {
        'ga4_id': site_settings['ga4_id'],
        'meta_pixel_id': site_settings['meta_pixel_id'],
    }
