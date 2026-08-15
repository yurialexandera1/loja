import json

from core.models import Product, Variant

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


def _parse_key(key):
    """Cart key is 'pid' or 'pid-vid' (variant). Returns (product_id, variant_id|None)."""
    parts = str(key).split('-', 1)
    pid = _safe_int(parts[0])
    vid = _safe_int(parts[1]) if len(parts) == 2 else None
    return pid, (vid or None)


def _make_key(product_id, variant_id=None):
    return f'{product_id}-{variant_id}' if variant_id else str(product_id)


def get_cart_lines(request):
    cart = get_cart(request)
    if not cart:
        return []
    parsed = {key: _parse_key(key) for key in cart}
    pids = {pid for pid, _ in parsed.values()}
    vids = {vid for _, vid in parsed.values() if vid}
    products = {
        p.id: p
        for p in Product.objects.filter(id__in=pids, active=True).select_related('category')
    }
    variants = {v.id: v for v in Variant.objects.filter(id__in=vids)} if vids else {}
    lines = []
    for key, (pid, vid) in parsed.items():
        product = products.get(pid)
        if not product:
            continue
        variant = variants.get(vid) if vid else None
        if vid and (not variant or variant.product_id != product.id):
            continue
        stock = variant.stock if variant else product.stock
        qty = _clamp_qty(cart.get(key, 0), stock)
        if qty <= 0:
            continue
        lines.append(
            {
                'key': key,
                'id': product.id,
                'name': product.name,
                'variant_label': variant.label if variant else '',
                'price': float(product.price),
                'qty': qty,
                'icon': product.icon,
                'stock': stock,
                'slug': product.slug,
            }
        )
    return lines


def add_to_cart(request, product_id, qty, variant_id=None):
    cart = get_cart(request)
    key = _make_key(product_id, variant_id)
    wanted = cart.get(key, 0) + _safe_int(qty)
    return _store_qty(cart, key, product_id, variant_id, wanted)


def set_cart_qty(request, cart_key, qty):
    cart = get_cart(request)
    product_id, variant_id = _parse_key(cart_key)
    return _store_qty(cart, _make_key(product_id, variant_id), product_id, variant_id, _safe_int(qty))


def clear_cart(request):
    return {}


def _store_qty(cart, key, product_id, variant_id, wanted):
    """Return a new cart with `key` clamped to what is actually buyable."""
    final = _clamp_qty(wanted, _stock_for(product_id, variant_id))
    updated = {k: v for k, v in cart.items() if k != key}
    if final > 0 and len(updated) < MAX_ITEMS_IN_CART:
        updated[key] = final
    return updated


def _stock_for(product_id, variant_id=None):
    if variant_id:
        stock = (
            Variant.objects.filter(id=variant_id, product_id=product_id)
            .values_list('stock', flat=True)
            .first()
        )
        return stock or 0
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
