import json

from core.models import Product

COOKIE_NAME = 'cart'
COOKIE_MAX_AGE = 60 * 60 * 24 * 30
MAX_QTY_PER_ITEM = 20
MAX_ITEMS_IN_CART = 50


def get_cart(request):
    raw = request.COOKIES.get(COOKIE_NAME)
    if not raw:
        return {}
    try:
        cart = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    if not isinstance(cart, dict):
        return {}
    return {str(k): int(v) for k, v in cart.items() if _is_positive_int(v)}


def set_cart(response, cart):
    response.set_cookie(
        COOKIE_NAME,
        json.dumps(cart),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite='Lax',
    )


def get_cart_lines(request):
    cart = get_cart(request)
    if not cart:
        return []
    products = Product.objects.filter(
        id__in=list(cart.keys()), active=True
    ).select_related('category')
    lines = []
    for product in products:
        qty = _clamp_qty(cart.get(str(product.id), 0), product.stock)
        if qty <= 0:
            continue
        lines.append(
            {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'qty': qty,
                'icon': product.icon,
                'stock': product.stock,
                'slug': product.slug,
            }
        )
    return lines


def add_to_cart(request, product_id, qty):
    cart = get_cart(request)
    key = str(product_id)
    wanted = cart.get(key, 0) + _safe_int(qty)
    return _store_qty(cart, key, product_id, wanted)


def set_cart_qty(request, product_id, qty):
    cart = get_cart(request)
    return _store_qty(cart, str(product_id), product_id, _safe_int(qty))


def clear_cart(request):
    return {}


def _store_qty(cart, key, product_id, wanted):
    """Return a new cart with `key` clamped to what is actually buyable."""
    final = _clamp_qty(wanted, _stock_for(product_id))
    updated = {k: v for k, v in cart.items() if k != key}
    if final > 0 and len(updated) < MAX_ITEMS_IN_CART:
        updated[key] = final
    return updated


def _stock_for(product_id):
    stock = (
        Product.objects.filter(id=product_id, active=True)
        .values_list('stock', flat=True)
        .first()
    )
    return stock or 0


def _clamp_qty(qty, stock):
    return max(0, min(_safe_int(qty), MAX_QTY_PER_ITEM, stock))


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
